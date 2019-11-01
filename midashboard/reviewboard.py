# -*- coding: utf-8 -*-
import math
import re
from collections import defaultdict
from datetime import datetime

from rbtools.api.client import RBClient
import json
import pickle


class ReviewBoard:
    def __init__(self):
        # TODO: Move the login info to file
        self.token = '7db9bd6a9db7d83855c9f42a87b80f99b069cc2e'
        self.url = 'https://review-board.natinst.com'

        self.reviews = []
        self.dev_group = None

    def download_reviews(self, dev_group):
        self.dev_group = dev_group

        root = RBClient(self.url, api_token=self.token).get_root()
        reviews = root.get_review_requests(to_groups=dev_group, status='pending', counts_only=True)
        reviews = root.get_review_requests(to_groups=dev_group, status='pending', max_results=reviews.count)
        self.reviews = [self.RawReviewInfo(r) for r in reviews]

    def dump(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump((self.dev_group, self.reviews), f)

    def load(self, filename):
        with open(filename, 'rb') as f:
            cache = pickle.load(f)
            self.dev_group = cache[0]
            self.reviews = cache[1]

    def get_review_brief_list(self, code_owners, ignore_tags):
        brief_list = [self.ReviewInfoBrief(r, code_owners, self.dev_group) for r in self.reviews]
        ignore_tags_casefold = [x.casefold() for x in ignore_tags]
        return [r for r in brief_list if r.tag.casefold() not in ignore_tags_casefold]

    class RawReviewInfo:
        def __init__(self, request):
            self.submitter = request.links.submitter.title
            self.url = request.absolute_url
            self.summary = request.summary
            self.issue_open_count = request.issue_open_count
            self.time_added = self._to_timestamp(request.time_added)
            self.comments = [self.Comment(r) for r in request.get_reviews()]
            self.changes_time = [self._to_timestamp(c.timestamp) for c in request.get_changes()]
            self.reviewers = [tp.title for tp in request.target_people]
            self.groups = [tg.title for tg in request.target_groups]

        @staticmethod
        def _to_timestamp(timestr):
            return datetime.strptime(timestr, '%Y-%m-%dT%H:%M:%SZ')

        class Comment:
            def __init__(self, review):
                self.reviewer = review.links.user.title
                self.time = ReviewBoard.RawReviewInfo._to_timestamp(review.timestamp)
                self.ship_it = review.ship_it

    class ReviewInfoBrief:
        def __init__(self, raw_review_info, code_owners, devgroup):
            self.developer = raw_review_info.submitter
            self.url = raw_review_info.url
            self.summary = raw_review_info.summary
            match = re.search(r"\[(\w+)\]", raw_review_info.summary)
            self.tag = "" if match is None else match.group(1)
            self.issue_open_count = raw_review_info.issue_open_count
            self.days_since_posted = self._days_since(raw_review_info.time_added)
            self.days_since_last_change = self._days_since(
                max([raw_review_info.time_added] + raw_review_info.changes_time)
            )
            self.review_groups = [g for g in raw_review_info.groups if g != devgroup]
            owners_in_review = list(set(raw_review_info.reviewers) & set(code_owners))
            self.code_owner_review_statuses = [
                self.ReviewStatus(owner, raw_review_info.comments) for owner in owners_in_review
            ]
            self.has_posted_to_code_owners = len(owners_in_review) > 0 or len(self.review_groups) > 0

        def is_submitted(self):
            return self.tag.casefold() == 'submitted'

        @staticmethod
        def _days_since(time):
            return math.ceil((datetime.now() - time).total_seconds() / 86400)

        def to_dict(self):
            return {
                'developer': self.developer,
                'url': self.url,
                'summary': self.summary,
                'open issues': self.issue_open_count,
                'days since last change': self.days_since_last_change,
                'owner reviews': [review_status.to_dict() for review_status in self.code_owner_review_statuses]
            }

        class ReviewStatus:
            def __init__(self, reviewer, comments):
                self.reviewer = reviewer
                self.ship_it = False
                latest_comment = None
                latest_comment_time = datetime.min
                my_comments = [c for c in comments if c.reviewer == self.reviewer]
                for comment in my_comments:
                    if comment.time > latest_comment_time:
                        latest_comment_time = comment.time
                        latest_comment = comment
                self.days_since_latest_comment = ReviewBoard.ReviewInfoBrief._days_since(latest_comment_time)
                self.ship_it = False if latest_comment is None else latest_comment.ship_it

            def to_dict(self):
                return {
                    'reviewer': self.reviewer,
                    'ship_it': self.ship_it,
                    'days since last comment': self.days_since_latest_comment
                }


class ReviewCounter(defaultdict):
    """
    key: name
    value: list of review
    """
    def __init__(self):
        super(ReviewCounter, self).__init__(list)

    def to_dict(self):
        return \
        {
            name:
            {
                'count': len(review_list),
                'details': [r.to_dict() for r in review_list]
            }
            for (name, review_list) in self.items()
        }


class ReviewOverallCounter(ReviewCounter):
    """
    key: review status (unresolved, submitted, pending owner review, pending internal review)
    value: list of reviews
    """
    def __init__(self, review_brief_list=[]):
        super(ReviewOverallCounter, self).__init__()
        for review in review_brief_list:
            self.add(review)

    def add(self, review):
        if review.issue_open_count > 0:
            self['Unresolved'].append(review)
        elif review.is_submitted():
            self['Submitted'].append(review)
        elif review.has_posted_to_code_owners:
            self['Code Owner'].append(review)
        else:
            self['Internal'].append(review)


class UnresolvedReviewCounter(ReviewCounter):
    """
    key: developer name
    value: list of reviews that has unresolved comments from the developer
    """
    def __init__(self, review_brief_list):
        super(UnresolvedReviewCounter, self).__init__()
        for review in review_brief_list:
            self._add(review)

    def _add(self, review):
        if review.issue_open_count > 0:
            self[review.developer].append(review)


class InactiveReviewCounter(ReviewCounter):
    """
    key: code owner name
    value: list of reviews that the reviewer didn't give comments for more than inactive_threshold_in_days
           since last code change
    """
    def __init__(self, review_brief_list, inactive_threshold_in_days):
        super(InactiveReviewCounter, self).__init__()
        self.inactive_threshold_in_days = inactive_threshold_in_days
        for review in review_brief_list:
            self._add(review)

    def _add(self, review):
        if review.issue_open_count > 0:
            return
        if review.days_since_last_change < self.inactive_threshold_in_days:
            return
        for review_status in review.code_owner_review_statuses:
            if review_status.ship_it:
                continue
            if review_status.days_since_latest_comment < self.inactive_threshold_in_days:
                continue
            self[review_status.reviewer].append(review)


class ReviewCountersByDay(defaultdict):
    """
    key: days since the review is posted
    value: ReviewOverallCounter for the day
    """
    def __init__(self, review_brief_list):
        super(ReviewCountersByDay, self).__init__(ReviewOverallCounter)
        for review in review_brief_list:
            self._add(review)

    def _add(self, review):
        self[review.days_since_posted - 1].add(review)  # 0-based index

    def to_dict(self):
        return {key: roc.to_dict() for key, roc in self.items()}


def analyze_open_reviews(dev_group, code_owners, ignore_tags, cache_file=None):
    reviewboard = ReviewBoard()
    if cache_file is None:
        reviewboard.download_reviews(dev_group)
    else:
        reviewboard.load(cache_file)
    brief_list = reviewboard.get_review_brief_list(code_owners, ignore_tags)
    return {
        "Overall": ReviewOverallCounter(brief_list).to_dict(),
        "Unresolved Reviews": UnresolvedReviewCounter(brief_list).to_dict(),
        "Inactive Reviews": InactiveReviewCounter(brief_list, 7).to_dict(),
        "Days Since Posted": ReviewCountersByDay(brief_list).to_dict()
    }


if __name__ == '__main__':
    review_statistics = analyze_open_reviews(
        dev_group='nishmicoredriver',
        code_owners=["mkirsch", "mlopez", "thofler"],
        ignore_tags=['ATS'],
        cache_file=r'..\data\reviewboard_cache'
    )
    print(json.dumps(review_statistics, indent=4))