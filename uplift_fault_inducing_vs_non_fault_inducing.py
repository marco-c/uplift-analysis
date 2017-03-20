import csv
import re
import random
from collections import defaultdict
from datetime import datetime
from libmozdata import hgmozilla
from libmozdata.utils import as_utc
import get_bugs
import utils

bug_inducing_bugs = defaultdict(set)

bug_pattern1 = re.compile('[\t ]*bug[\t ]*([0-9]+)')
bug_pattern2 = re.compile('b=([0-9]+)')
bug_pattern3 = re.compile('bug=([0-9]+)')

bug_inducing_commits = []
with open('all_bugs/bug_inducing_commits.csv', 'rb') as csv_file:
    csv_reader = csv.reader(csv_file)
    next(csv_reader)
    for row in csv_reader:
        caused_bug_id = int(row[0])
        bug_inducing_commits = [rev for rev in row[1].split('^') if rev != '']
        for commit in bug_inducing_commits:
            meta = hgmozilla.Revision.get_revision(channel='nightly', node=commit)
            desc = meta['desc'].lower()
            bug_id_match = re.search(bug_pattern1, desc)
            if not bug_id_match:
                bug_id_match = re.search(bug_pattern2, desc)
            if not bug_id_match:
                bug_id_match = re.search(bug_pattern3, desc)

            if bug_id_match:
                bug_inducing_bugs[int(bug_id_match.group(1))].add(caused_bug_id)
            else:
                print(meta)
                print('')

bugs = get_bugs.get_all()
uplifts = utils.get_uplifts(bugs)

channels = ['release', 'beta', 'aurora']
uplifts_per_channel = {}
sample_per_channel = {}
for channel in channels:
    uplifts_per_channel[channel] = {
        'fault': set(),
        'nonfault': set(),
    }

sample_per_channel['release'] = {
    'fault': 18,
    'nonfault': 151,
}
sample_per_channel['beta'] = {
    'fault': 133,
    'nonfault': 327,
}
sample_per_channel['aurora'] = {
    'fault': 192,
    'nonfault': 350,
}

for bug in bugs:
    for channel in utils.uplift_channels(bug):
        uplift_date = utils.get_uplift_date(bug, channel)

        if uplift_date is None or uplift_date < as_utc(datetime(2014, 9, 1)) or uplift_date >= as_utc(datetime(2016, 8, 24)):
            continue

        if int(bug['id']) in bug_inducing_bugs:
            uplifts_per_channel[channel]['fault'].add(bug['id'])
        else:
            uplifts_per_channel[channel]['nonfault'].add(bug['id'])

for channel in channels:
    print(channel)

    print(len(uplifts_per_channel[channel]['fault']))
    print(len(uplifts_per_channel[channel]['nonfault']))
    print(sample_per_channel[channel]['fault'])
    print(sample_per_channel[channel]['nonfault'])

    with open('uplift_fault_inducing_vs_non_fault_inducing_' + channel + '.csv', 'w') as output_file:
        csv_writer = csv.writer(output_file)
        csv_writer.writerow(['Uplift ID', 'Fault IDs', 'Reason for uplift', 'Reason for failure'])

        fault_inducing = list(uplifts_per_channel[channel]['fault'])
        fault_inducing = random.sample(fault_inducing, sample_per_channel[channel]['fault'])
        for bug_id in fault_inducing:
            csv_writer.writerow([bug_id, '^'.join([str(bid) for bid in list(bug_inducing_bugs[bug_id])]), '', ''])

        non_fault_inducing = list(uplifts_per_channel[channel]['nonfault'])
        non_fault_inducing = random.sample(non_fault_inducing, sample_per_channel[channel]['nonfault'])
        for bug_id in non_fault_inducing:
            csv_writer.writerow([bug_id, '', '', ''])
