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
        self.owner = request.links.submitter.title
        self.url = request.absolute_url
        match = re.search(r"\[(\w+)\]", request.summary)
        self.tag = "" if match is None else match.group(1)
        self.open_issue_count = request.issue_open_count
        self.duration_in_days = self._get_duration_in_days(request)
        self.is_pending_for_code_owners = self._is_pending_for_code_owners(request, code_owners, devgroup)

    def is_submitted(self):
        return self.tag.casefold() == 'submitted'

    @staticmethod
    def _get_duration_in_days(request):
        current = datetime.now()
        request_time_added = datetime.strptime(request.time_added, '%Y-%m-%dT%H:%M:%SZ')
        return (current - request_time_added).total_seconds()/86400

    @staticmethod
    def _is_pending_for_code_owners(request, code_owners, devgroup):
        reviewers = [target_reviewer.title for target_reviewer in request.target_people]
        review_groups = [target_group.title for target_group in request.target_groups if target_group.title != devgroup]

        is_code_owner_in_reviewers = not set(reviewers).isdisjoint(code_owners)
        return is_code_owner_in_reviewers or len(review_groups) > 0


class ReviewRequestCount:
    def __init__(self, description):
        self.description = description
        self.urls = []
        self.count = 0

    def increase(self, url):
        self.count += 1
        self.urls.append(url)
        return self


class ReviewStatus:
    def __init__(self):
        self.unresolved = ReviewRequestCount("With unresolved comments")
        self.submitted = ReviewRequestCount("Code submitted")
        self.pending_for_code_owner = ReviewRequestCount("Pending for code owners")
        self.pending_for_internal = ReviewRequestCount("pending for internal reviewers")

    def update(self, review):
        if review.open_issue_count > 0:
            self.unresolved.increase(review.url)
        elif review.is_submitted():
            self.submitted.increase(review.url)
        elif review.is_pending_for_code_owners:
            self.pending_for_code_owner.increase(review.url)
        else:
            self.pending_for_internal.increase(review.url)

    def get_status(self):
        return [
            {
                "description": x.description,
                "count"      : x.count,
                'urls'       : x.urls
            }
            for x in [self.unresolved, self.submitted, self.pending_for_code_owner, self.pending_for_internal]
        ]


class ReviewDurations:
    def __init__(self, max_days):
        self.durations = [ReviewStatus() for _ in range(max_days)]
        self.names = ["1 day"] + [f'{x} days' for x in range(2, max_days + 1)]

    def update(self, review):
        days = math.ceil(review.duration_in_days)
        self.durations[days - 1].update(review) # 0-based index

    def get_durations(self):
        data = [
            {
                "status" : "With unresolved comments",
                "values" : [x.unresolved.count for x in self.durations]
            },
            {
                "status": "Pending for review",
                "values": [x.pending_for_code_owner.count + x.pending_for_internal.count for x in self.durations]
            },
            {
                "status": "Code submitted",
                "values": [x.submitted.count for x in self.durations]
            }
        ]
        return {"names" : self.names, "data" : data}


def get_all_review_requests(devgroup):
    client = RBClient('https://review-board.natinst.com', api_token=token)
    root = client.get_root()
    reviews = root.get_review_requests(to_groups=devgroup, status='pending', counts_only=True)
    return root.get_review_requests(to_groups="nishmicoredriver", status='pending', max_results=reviews.count)


def get_review_status(review_list):
    review_status = ReviewStatus()
    for review in review_list:
        review_status.update(review)
    return review_status.get_status()


def get_open_review_count_per_owner(review_list):
    return dict(Counter([r.owner for r in review_list]))


def get_review_duration(review_list):
    durations = ReviewDurations(math.ceil(max([x.duration_in_days for x in review_list])))
    for review in review_list:
        durations.update(review)
    return durations.get_durations()


def brief_review_list(review_requests, code_owners, devgroup, ignore_tags):
    review_list = [RequestInfo(request, code_owners, devgroup) for request in review_requests]
    ignore_tags_casefold = [x.casefold() for x in ignore_tags]
    return [r for r in review_list if r.tag.casefold() not in ignore_tags_casefold]


def analyze_open_reviews(code_owners, devgroup, ignore_tags):
    review_requests = get_all_review_requests(devgroup)
    review_list = brief_review_list(review_requests, code_owners, devgroup, ignore_tags)
    return {
        "status": get_review_status(review_list),
        "owners": get_open_review_count_per_owner(review_list),
        "duration": get_review_duration(review_list)
    }


if __name__ == '__main__':
    res = analyze_open_reviews(["mkirsch", "mlopez"], "nishmicoredriver", ["ATS"])
    print(res)

