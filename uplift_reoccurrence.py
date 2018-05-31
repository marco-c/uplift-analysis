import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta
import re

from libmozdata.bugzilla import Bugzilla
from libmozdata.utils import as_utc, get_date_ymd
import requests

import get_bugs
import utils


bugs = get_bugs.get_all()
uplifts = utils.get_uplifts(bugs)

cloned_bug_map = utils.get_cloned_map(bugs)

uplift_num = defaultdict(int)
reopened = defaultdict(int)
reopened_bugs = set()
cloned = defaultdict(int)
cloned_bugs = set()
additionally_uplifted = defaultdict(int)
additionally_uplifted_bugs = set()
bm25_dupes_opened_after = defaultdict(int)
bm25_dupes_opened_after_bugs = set()
bm25_dupes_resolved_after = defaultdict(int)
bm25_dupes_resolved_after_bugs = set()

id_to_channels = defaultdict(set)


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


try:
    with open('all_bugs/uplift_revs_data.json', 'r') as f:
        uplift_revs_data = json.load(f)
except IOError:
    uplift_revs_data = {
        'aurora': {},
        'beta': {},
        'release': {},
    }


def get_uplift_rev_data(channel, rev):
    if rev not in uplift_revs_data[channel]:
        r = requests.get('https://hg.mozilla.org/releases/mozilla-{}/json-rev/{}'.format(channel, rev))
        obj = r.json()
        assert obj['desc']
        uplift_revs_data[channel][rev] = obj

        with open('all_bugs/uplift_revs_data.json', 'w') as f:
            json.dump(uplift_revs_data, f)

    return uplift_revs_data[channel][rev]


def get_landed_uplift_dates(bug, channel):
    landing_comments = Bugzilla.get_landing_comments(bug['comments'], [channel])
    dates = []

    for lc in landing_comments:
        obj = get_uplift_rev_data(channel, lc['revision'])

        if 'a=test-only' in obj['desc']:
            continue

        if not 'bug {}'.format(bug['id']) in obj['desc'].lower():
            continue

        dates.append(get_date_ymd(lc['comment']['time']))

    return dates


def is_reopened(channel, bug, uplift_date):
    for history in bug['history']:
        history_date = get_date_ymd(history['when'])
        for change in history['changes']:
            if change['field_name'] == 'status' and change['added'] == 'REOPENED' and history_date > uplift_date:
                reopened_bugs.add(bug['id'])
                id_to_channels[bug['id']].add(channel)
                return True

    return False


def is_cloned(channel, cloned_bug_map, bug, uplift_date):
    ret = False
    if bug['id'] in cloned_bug_map:
        for cloned_bug in cloned_bug_map[bug['id']]:
            creation_date = get_date_ymd(cloned_bug['creation_time'])
            if creation_date > uplift_date:
                cloned_bugs.add((bug['id'], cloned_bug['id']))
                id_to_channels[bug['id']].add(channel)
                ret = True

    return ret


def is_additional_uplifts(channel, bug, uplift_dates):
    if len(uplift_dates) == 1:
        return False

    for uplift_date in uplift_dates[1:]:
        if uplift_date > (uplift_dates[0] + timedelta(3)):
            additionally_uplifted_bugs.add(bug['id'])
            id_to_channels[bug['id']].add(channel)
            return True


def is_bm25_opened_after(channel, bug, uplift_date):
    ret = False
    if bug['id'] in bm25_data:
        dupes = bm25_data[bug['id']]
        for dupe in dupes:
            data = get_bug_from_id(dupe)
            if get_date_ymd(data['creation_time']) > uplift_date:
                bm25_dupes_opened_after_bugs.add((bug['id'], dupe))
                id_to_channels[bug['id']].add(channel)
                ret = True

    return ret


def is_bm25_resolved_after(channel, bug, uplift_date):
    ret = False
    if bug['id'] in bm25_data:
        dupes = bm25_data[bug['id']]
        for dupe in dupes:
            data = get_bug_from_id(dupe)
            if get_date_ymd(data['cf_last_resolved']) > uplift_date:
                bm25_dupes_resolved_after_bugs.add((bug['id'], dupe))
                id_to_channels[bug['id']].add(channel)
                ret = True

    return ret


for uplift in uplifts:
    if uplift['component'] == 'Pocket':
        continue

    for channel in utils.uplift_approved_channels(uplift):
        uplift_request_date = utils.get_uplift_date(uplift, channel)
        if uplift_request_date is None or uplift_request_date < as_utc(datetime(2014, 9, 1)) or uplift_request_date >= as_utc(datetime(2016, 8, 24)):
            continue

        uplift_num[channel] += 1

        uplift_dates = get_landed_uplift_dates(uplift, channel)
        if len(uplift_dates) == 0:
            # print(uplift['id'])
            continue
        first_uplift_date = uplift_dates[0]

        if is_reopened(channel, uplift, first_uplift_date):
            reopened[channel] += 1
        elif is_additional_uplifts(channel, uplift, uplift_dates):
            additionally_uplifted[channel] += 1

        if is_cloned(channel, cloned_bug_map, uplift, first_uplift_date):
            cloned[channel] += 1
        elif is_bm25_opened_after(channel, uplift, first_uplift_date):
            bm25_dupes_opened_after[channel] += 1
        elif is_bm25_resolved_after(channel, uplift, first_uplift_date):
            bm25_dupes_resolved_after[channel] += 1

for channel in ['release', 'beta', 'aurora']:
    print(channel)
    print('{} uplift bugs'.format(uplift_num[channel]))
    print('{} uplift bugs were reopened after being uplifted'.format(reopened[channel]))
    print('{} uplift bugs were cloned after being uplifted'.format(cloned[channel]))
    print('{} uplift bugs were fixed by multiple uplifts with a distance between them of at least 3 days'.format(additionally_uplifted[channel]))
    print('{} uplift bugs were found as duplicate via bm25 data, opened after the uplift'.format(bm25_dupes_opened_after[channel]))
    print('{} uplift bugs were found as duplicate via bm25 data, resolved after the uplift'.format(bm25_dupes_resolved_after[channel]))
    print('\n')
    print('\n')


def save_csv(path, new_bugs, typ):
    bugs = {}

    with open('manual_classification/reoccurrence/{}.csv'.format(path), 'r') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)

        if typ == 1:
            for bug, classification in csv_reader:
                bugs[int(bug)] = classification
        elif typ == 2:
            for bug1, bug2, classification in csv_reader:
                bugs[(int(bug1), int(bug2))] = classification

    for entry in new_bugs:
        if entry not in bugs:
            bugs[entry] = ''

    with open('manual_classification/reoccurrence/{}.csv'.format(path), 'w') as f:
        csv_writer = csv.writer(f)

        if typ == 1:
            csv_writer.writerow(['uplift_id', 'why'])
            for bug, classification in sorted(list(bugs.items())):
                csv_writer.writerow([bug, classification])
        elif typ == 2:
            csv_writer.writerow(['uplift_id', 'cloned_id', 'why'])
            for (bug1, bug2), classification in sorted(list(bugs.items())):
                csv_writer.writerow([bug1, bug2, classification])

    with open('manual_classification/reoccurrence/{}_with_channels.csv'.format(path), 'w') as f:
        csv_writer = csv.writer(f)

        if typ == 1:
            csv_writer.writerow(['uplift_id', 'why', 'channels'])
            for bug, classification in sorted(list(bugs.items())):
                csv_writer.writerow([bug, classification, '^'.join(id_to_channels[int(bug)])])
        elif typ == 2:
            csv_writer.writerow(['uplift_id', 'cloned_id', 'why', 'channels'])
            for (bug1, bug2), classification in sorted(list(bugs.items())):
                csv_writer.writerow([bug1, bug2, classification, '^'.join(id_to_channels[int(bug1)])])

save_csv('reopened', reopened_bugs, 1)
save_csv('cloned', cloned_bugs, 2)
save_csv('additionally_uplifted', additionally_uplifted_bugs, 1)
save_csv('bm25_opened_after', bm25_dupes_opened_after_bugs, 2)
save_csv('bm25_resolved_after', bm25_dupes_resolved_after_bugs, 2)
