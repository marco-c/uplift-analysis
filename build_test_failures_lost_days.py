import csv
import json

from libmozdata.bugzilla import Bugzilla
from libmozdata.utils import get_date_ymd

import get_bugs
import utils


bugs = get_bugs.get_all()

def get_bug_from_id(bug_id):
    return [bug for bug in bugs if bug['id'] == int(bug_id)][0]

uplift_failure_bugs = set()

for path, typ in [('reopened', 1), ('cloned', 2), ('additionally_uplifted', 1), ('bm25_opened_after', 2), ('bm25_resolved_after', 2)]:

    with open('manual_classification/reoccurrence/{}.csv'.format(path), 'r') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)

        if typ == 1:
            for bug, classification in csv_reader:
                if 'test failure' in classification or 'build failure' in classification:
                    uplift_failure_bugs.add(bug)
        elif typ == 2:
            for bug1, bug2, classification in csv_reader:
                if 'test failure' in classification or 'build failure' in classification:
                    uplift_failure_bugs.add(bug1)


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


def get_backout_dates(bug, channel):
    landing_comments = Bugzilla.get_landing_comments(bug['comments'], [channel])
    dates = []

    for lc in landing_comments:
        obj = get_uplift_rev_data(channel, lc['revision'])

        if not 'bug {}'.format(bug['id']) in obj['desc'].lower():
            continue

        if not ('backout' in obj['desc'].lower() or 'backed out' in obj['desc'].lower()) :
            continue

        dates.append(get_date_ymd(lc['comment']['time']))

    return dates


for uplift_failure_bug in uplift_failure_bugs:
    bug = get_bug_from_id(uplift_failure_bug)
    for channel in utils.uplift_approved_channels(bug):
        print('{} - {}'.format(uplift_failure_bug, channel))
        uplift_request_dates = []
        for entry in bug['history']:
            for change in entry['changes']:
                if 'approval-mozilla-{}?'.format(channel) in change['added']:
                    uplift_request_dates.append(get_date_ymd(entry['when']))

        backout_dates = get_backout_dates(bug, channel)

        print(uplift_request_dates)
        print(backout_dates)
        if len(uplift_request_dates) == 1 and len(backout_dates) == 1:
            print((uplift_request_dates[0] - backout_dates[0]).total_seconds())
