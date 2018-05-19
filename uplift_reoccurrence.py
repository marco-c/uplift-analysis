import csv
from collections import defaultdict
from datetime import datetime, timedelta
import re

from libmozdata.utils import as_utc, get_date_ymd

import get_bugs
import utils


bugs = get_bugs.get_all()
uplifts = utils.get_uplifts(bugs)

cloned_bug_map = utils.get_cloned_map(bugs)

uplift_num = defaultdict(int)
reopened = defaultdict(int)
cloned = defaultdict(int)
additionally_uplifted = defaultdict(int)
bm25_dupes = defaultdict(int)


def get_bug_from_id(bug_id):
    return [bug for bug in bugs if bug['id'] == int(bug_id)][0]


unclassified = 0
bm25_data = defaultdict(set)
with open('manual_classification/bm25_results_initial_after_auto.csv', 'r') as f:
    csv_reader = csv.reader(f)
    next(csv_reader)  # skip header
    for bug1_link, bug2_link, classification, title1, title2 in csv_reader:
        bug1_id = int(bug1_link[len('https://bugzilla.mozilla.org/show_bug.cgi?id='):])
        bug2_id = int(bug2_link[len('https://bugzilla.mozilla.org/show_bug.cgi?id='):])

        if not classification:
            unclassified += 1
            continue

        if classification == 'y' or classification == 'y?':
            bm25_data[bug1_id].add(bug2_id)
            bm25_data[bug2_id].add(bug1_id)


print(unclassified)


def is_reopened(bug, uplift_date):
    for history in bug['history']:
        history_date = get_date_ymd(history['when'])
        for change in history['changes']:
            if change['field_name'] == 'status' and change['added'] == 'REOPENED' and history_date > uplift_date:
                return True

    return False


def is_cloned(cloned_bug_map, bug, uplift_date):
    if bug['id'] in cloned_bug_map:
        for cloned_bug in cloned_bug_map[bug['id']]:
            creation_date = get_date_ymd(cloned_bug['creation_time'])
            if creation_date > uplift_date:
                return True

    return False


def is_additional_uplifts(uplift_dates):
    if len(uplift_dates) == 1:
        return False

    for uplift_date in uplift_dates[1:]:
        if uplift_date > (uplift_dates[0] + timedelta(3)):
            return True


def is_bm25(bug, uplift_date):
    if bug['id'] in bm25_data:
        dupes = bm25_data[bug['id']]
        for dupe in dupes:
            data = get_bug_from_id(dupe)
            if get_date_ymd(data['creation_time']) > uplift_date:
                return True

    return False


for uplift in uplifts:
    if uplift['component'] == 'Pocket':
        continue

    for channel in utils.uplift_approved_channels(uplift):
        uplift_dates = utils.get_uplift_dates(uplift, channel)
        if len(uplift_dates) == 0:
            continue

        uplift_date = uplift_dates[0]
        if uplift_date is None or uplift_date < as_utc(datetime(2014, 9, 1)) or uplift_date >= as_utc(datetime(2016, 8, 24)):
            continue

        uplift_num[channel] += 1

        if is_reopened(uplift, uplift_date):
            reopened[channel] += 1
            continue

        if is_cloned(cloned_bug_map, uplift, uplift_date):
            cloned[channel] += 1
            continue

        if is_additional_uplifts(uplift_dates):
            additionally_uplifted[channel] += 1
            continue

        if is_bm25(uplift, uplift_date):
            bm25_dupes[channel] += 1
            continue

for channel in ['release', 'beta', 'aurora']:
    print(channel)
    print('{} uplift bugs'.format(uplift_num[channel]))
    print('{} uplift bugs were reopened after being uplifted'.format(reopened[channel]))
    print('{} uplift bugs were cloned after being uplifted'.format(cloned[channel]))
    print('{} uplift bugs were fixed by multiple uplifts with a distance between them of at least 3 days'.format(additionally_uplifted[channel]))
    print('{} uplift bugs were found via bm25 data'.format(bm25_dupes[channel]))
    print('\n')
    print('\n')
