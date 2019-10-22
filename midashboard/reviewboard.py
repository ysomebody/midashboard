# -*- coding: utf-8 -*-
import math
import re
from collections import Counter
from datetime import datetime

from rbtools.api.client import RBClient
import json

user = 'hohuang'
token = '7db9bd6a9db7d83855c9f42a87b80f99b069cc2e'


class ReviewerStatus:
    def __init__(self, name, has_shipit):
        self.name = name
        self.has_shipit = has_shipit


class RequestInfo:
    def __init__(self, request, code_owners, devgroup):
        self.developer = request.links.submitter.title
        self.url = request.absolute_url
        match = re.search(r"\[(\w+)\]", request.summary)
        self.tag = "" if match is None else match.group(1)
        self.open_issue_count = request.issue_open_count
        self.duration_in_days = self._get_duration_in_days(request)
        self.review_groups = [target_group.title for target_group in request.target_groups if target_group.title != devgroup]
        self.reviewer_status = self._get_reviewer_status(request, code_owners)
        self.is_pending_for_code_owners = self._is_pending_for_code_owners(self.reviewer_status, self.review_groups)

    def is_submitted(self):
        return self.tag.casefold() == 'submitted'

    @staticmethod
    def _get_duration_in_days(request):
        current = datetime.now()
        request_time_added = datetime.strptime(request.time_added, '%Y-%m-%dT%H:%M:%SZ')
        return (current - request_time_added).total_seconds()/86400

    @staticmethod
    def _get_reviewer_status(request, code_owners):
        reviewer_status = []
        reviewers = [reviewer.title for reviewer in request.target_people if reviewer.title in code_owners]
        reviews = request.get_reviews()
        for reviewer in reviewers:
            has_shipit = any([r.ship_it for r in reviews if r.links.user.title == reviewer])
            reviewer_status.append(ReviewerStatus(reviewer, has_shipit))
        return reviewer_status

    @staticmethod
    def _is_pending_for_code_owners(reviewer_status, review_groups):
        return len(reviewer_status) > 0 or len(review_groups) > 0


class ReviewRequestCounter:
    def __init__(self, name):
        self.name = name
        self.reviews = []
        self.count = 0

    def add(self, review):
        self.count += 1
        self.reviews.append(review)
        return self


class ReviewOverallCounter:
    def __init__(self):
        self.counter_names = ['Unresolved', 'Submitted', 'Owner review', 'Internal review']
        self.counters = {name: ReviewRequestCounter(name) for name in self.counter_names}

    def add(self, review):
        if review.open_issue_count > 0:
            self.counters['Unresolved'].add(review)
        elif review.is_submitted():
            self.counters['Submitted'].add(review)
        elif review.is_pending_for_code_owners:
            self.counters['Owner review'].add(review)
        else:
            self.counters['Internal review'].add(review)

    def get_overall(self):
        return [
            {
                "description": counter.name,
                "count"      : counter.count,
                'urls'       : [review.url for review in counter.reviews]
            }
            for counter in self.counters.values()
        ]


class ReviewDurationsCounters:
    def __init__(self, max_days):
        self.counter_per_day = [ReviewOverallCounter() for _ in range(max_days)]
        self.names = ["1 day"] + [f'{x} days' for x in range(2, max_days + 1)]

    def add(self, review):
        days = math.ceil(review.duration_in_days)
        self.counter_per_day[days - 1].add(review) # 0-based index

    def get_durations(self):
        data = [
            {
                "status" : counter_name,
                "values" : [overall_counter.counters[counter_name].count for overall_counter in self.counter_per_day]
            }
            for counter_name in self.counter_per_day[0].counter_names
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
    reviewer_counters = dict() # {name : ReviewRequestCounter(name)}
    for review in review_list:
        if review.open_issue_count > 0:
            continue
        for rs in review.reviewer_status:
            if rs.name not in reviewer_counters:
                reviewer_counters[rs.name] = ReviewRequestCounter(rs.name)
            if not rs.has_shipit:
                reviewer_counters[rs.name].add(review)
    review_count_per_reviewer = dict()
    for reviewer, counter in reviewer_counters.items():
        review_count_per_reviewer[reviewer] = counter.count
    return review_count_per_reviewer


def get_review_duration(review_list):
    durations_counters = ReviewDurationsCounters(math.ceil(max([x.duration_in_days for x in review_list])))
    for review in review_list:
        durations_counters.add(review)
    return durations_counters.get_durations()


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
    print(json.dumps(res, indent=4))

