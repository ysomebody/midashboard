# -*- coding: utf-8 -*-
import math
import re
from collections import Counter
from datetime import datetime

from rbtools.api.client import RBClient

user = 'hohuang'
token = '7db9bd6a9db7d83855c9f42a87b80f99b069cc2e'

class RequestInfo:
    def __init__(self, request, code_owners, devgroup):
        self.developer = request.links.submitter.title
        self.url = request.absolute_url
        match = re.search(r"\[(\w+)\]", request.summary)
        self.tag = "" if match is None else match.group(1)
        self.open_issue_count = request.issue_open_count
        self.duration_in_days = self._get_duration_in_days(request)
        self.reviewers = [target_reviewer.title for target_reviewer in request.target_people]
        self.review_groups = [target_group.title for target_group in request.target_groups if target_group.title != devgroup]
        self.is_pending_for_code_owners = self._is_pending_for_code_owners(code_owners)

    def is_submitted(self):
        return self.tag.casefold() == 'submitted'

    @staticmethod
    def _get_duration_in_days(request):
        current = datetime.now()
        request_time_added = datetime.strptime(request.time_added, '%Y-%m-%dT%H:%M:%SZ')
        return (current - request_time_added).total_seconds()/86400

    def _is_pending_for_code_owners(self, code_owners):
        is_code_owner_in_reviewers = not set(self.reviewers).isdisjoint(code_owners)
        return is_code_owner_in_reviewers or len(self.review_groups) > 0


class ReviewRequestCounter:
    def __init__(self, description):
        self.description = description
        self.reviews = []
        self.count = 0

    def add(self, review):
        self.count += 1
        self.reviews.append(review)
        return self


class ReviewOverallCounter:
    def __init__(self):
        self.unresolved = ReviewRequestCounter("Unresolved")
        self.submitted = ReviewRequestCounter("Submitted")
        self.pending_for_code_owner = ReviewRequestCounter("Owner review")
        self.pending_for_internal = ReviewRequestCounter("Internal reviewer")

    def add(self, review):
        if review.open_issue_count > 0:
            self.unresolved.add(review)
        elif review.is_submitted():
            self.submitted.add(review)
        elif review.is_pending_for_code_owners:
            self.pending_for_code_owner.add(review)
        else:
            self.pending_for_internal.add(review)

    def get_overall(self):
        return [
            {
                "description": counter.description,
                "count"      : counter.count,
                'urls'       : [review.url for review in counter.reviews]
            }
            for counter in [self.unresolved, self.submitted, self.pending_for_code_owner, self.pending_for_internal]
        ]


class ReviewDurationsCounter:
    def __init__(self, max_days):
        self.counters_per_day = [ReviewOverallCounter() for _ in range(max_days)]
        self.names = ["1 day"] + [f'{x} days' for x in range(2, max_days + 1)]

    def add(self, review):
        days = math.ceil(review.duration_in_days)
        self.counters_per_day[days - 1].add(review) # 0-based index

    def get_durations(self):
        data = [
            {
                "status" : "Unresolved",
                "values" : [x.unresolved.count for x in self.counters_per_day]
            },
            {
                "status": "Pending",
                "values": [x.pending_for_code_owner.count + x.pending_for_internal.count for x in self.counters_per_day]
            },
            {
                "status": "Submitted",
                "values": [x.submitted.count for x in self.counters_per_day]
            }
        ]
        return {"names" : self.names, "data" : data}


def get_all_review_requests(devgroup):
    client = RBClient('https://review-board.natinst.com', api_token=token)
    root = client.get_root()
    reviews = root.get_review_requests(to_groups=devgroup, status='pending', counts_only=True)
    return root.get_review_requests(to_groups="nishmicoredriver", status='pending', max_results=reviews.count)


def get_overall_review_status(review_list):
    overall_counter = ReviewOverallCounter()
    for review in review_list:
        overall_counter.add(review)
    return overall_counter.get_overall()


def get_open_review_count_per_developer(review_list):
    return dict(Counter([r.developer for r in review_list if not r.is_submitted()]))


def get_open_review_count_per_reviewer(review_list, code_owners):
    reviewer_counters = dict() # {reviewer : ReviewRequestCounter(reviewer)}
    for review in review_list:
        for reviewer in review.reviewers:
            if reviewer not in code_owners:
                continue
            if reviewer not in reviewer_counters:
                reviewer_counters[reviewer] = ReviewRequestCounter(reviewer)
            reviewer_counters[reviewer].add(review)
    review_count_per_reviewer = dict()
    for reviewer, counter in reviewer_counters.items():
        review_count_per_reviewer[reviewer] = counter.count
    return review_count_per_reviewer


def get_review_duration(review_list):
    durations_counter = ReviewDurationsCounter(math.ceil(max([x.duration_in_days for x in review_list])))
    for review in review_list:
        durations_counter.add(review)
    return durations_counter.get_durations()


def brief_review_list(review_requests, code_owners, devgroup, ignore_tags):
    review_list = [RequestInfo(request, code_owners, devgroup) for request in review_requests]
    ignore_tags_casefold = [x.casefold() for x in ignore_tags]
    return [r for r in review_list if r.tag.casefold() not in ignore_tags_casefold]


def analyze_open_reviews(code_owners, devgroup, ignore_tags):
    review_requests = get_all_review_requests(devgroup)
    review_list = brief_review_list(review_requests, code_owners, devgroup, ignore_tags)
    return {
        "status": get_overall_review_status(review_list),
        "developers": get_open_review_count_per_developer(review_list),
        "reviewers": get_open_review_count_per_reviewer(review_list, code_owners),
        "duration": get_review_duration(review_list)
    }


if __name__ == '__main__':
    res = analyze_open_reviews(["mkirsch", "mlopez"], "nishmicoredriver", ["ATS"])
    print(res)

