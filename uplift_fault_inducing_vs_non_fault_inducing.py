import csv
import re
import random
import json
import argparse
from collections import defaultdict
from datetime import datetime
from libmozdata import hgmozilla
from libmozdata.utils import as_utc
import get_bugs
import utils

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Mine commit metrics')
    parser.add_argument('type', action='store', choices=['generate', 'diff', 'same'])
    args = parser.parse_args()

    channels = ['release', 'beta', 'aurora']

    if args.type == 'generate':
        try:
            with open('all_bugs/bug_inducing_bugs.json', 'r') as f:
                bug_inducing_bugs = json.load(f)
        except:
            bug_inducing_bugs = defaultdict(set)

            bug_pattern1 = re.compile('[\t ]*bug[\t ]*([0-9]+)')
            bug_pattern2 = re.compile('b=([0-9]+)')
            bug_pattern3 = re.compile('bug=([0-9]+)')

            bug_inducing_commits = []
            with open('all_bugs/bug_inducing_commits.csv', 'rb') as csv_file:
                csv_reader = csv.reader(csv_file)
                next(csv_reader)
                for row in csv_reader:
                    caused_bug_id = str(row[0])
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
                            bug_inducing_bugs[str(bug_id_match.group(1))].add(caused_bug_id)
                        else:
                            print(meta)
                            print('')

            for bug_id in bug_inducing_bugs.keys():
                bug_inducing_bugs[bug_id] = list(bug_inducing_bugs[bug_id])

            with open('all_bugs/bug_inducing_bugs.json', 'w') as f:
                json.dump(bug_inducing_bugs, f)

        bugs = get_bugs.get_all()
        uplifts = utils.get_uplifts(bugs)

        uplifts_per_channel = {}
        sample_per_channel = {}
        for channel in channels:
            uplifts_per_channel[channel] = {
                'fault': set(),
                'nonfault': set(),
            }

        sample_per_channel['release'] = {
            'fault': 17,
            'nonfault': 137,
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
            if bug['component'] == 'Pocket':
                continue

            for channel in utils.uplift_channels(bug):
                uplift_date = utils.get_uplift_date(bug, channel)

                if uplift_date is None or uplift_date < as_utc(datetime(2014, 9, 1)) or uplift_date >= as_utc(datetime(2016, 8, 24)):
                    continue

                if str(bug['id']) in bug_inducing_bugs:
                    uplifts_per_channel[channel]['fault'].add(str(bug['id']))
                else:
                    uplifts_per_channel[channel]['nonfault'].add(str(bug['id']))

        for channel in channels:
            print(channel)

            print("Total fault-inducing uplifts: " + str(len(uplifts_per_channel[channel]['fault'])))
            print("Total non-fault-inducing uplifts: " + str(len(uplifts_per_channel[channel]['nonfault'])))
            print("Sample fault-inducing uplifts: " + str(sample_per_channel[channel]['fault']))
            print("Sample non-fault-inducing uplifts: " + str(sample_per_channel[channel]['nonfault']))

            with open('uplift_fault_inducing_vs_non_fault_inducing_' + channel + '.csv', 'w') as output_file:
                csv_writer = csv.writer(output_file)
                csv_writer.writerow(['Uplift ID', 'Fault IDs', 'Reason for uplift', 'Reason for failure', 'Evaluation of risks'])

                fault_inducing = list(uplifts_per_channel[channel]['fault'])
                fault_inducing = random.sample(fault_inducing, sample_per_channel[channel]['fault'])
                for bug_id in fault_inducing:
                    csv_writer.writerow([bug_id, '^'.join(bug_inducing_bugs[bug_id]), '', ''])

                non_fault_inducing = list(uplifts_per_channel[channel]['nonfault'])
                non_fault_inducing = random.sample(non_fault_inducing, sample_per_channel[channel]['nonfault'])
                for bug_id in non_fault_inducing:
                    csv_writer.writerow([bug_id, '', '', ''])
    elif args.type == 'diff':
        for channel in channels:
            with open('manual_classification/result_le/uplift_fault_inducing_vs_non_fault_inducing_' + channel + '.csv', 'r') as input_file_1:
                with open('manual_classification/result_marco/uplift_fault_inducing_vs_non_fault_inducing_' + channel + '.csv', 'r') as input_file_2:
                    csv_reader_1 = csv.reader(input_file_1)
                    csv_reader_2 = csv.reader(input_file_2)
                    results = zip(csv_reader_1, csv_reader_2)
                    print('Uplift categorization')
                    for (row_1, row_2) in results:
                        reasons_for_uplift_1 = row_1[2].split('^')
                        reasons_for_uplift_2 = row_2[2].split('^')
                        if set(reasons_for_uplift_1) != set(reasons_for_uplift_2):
                            print('Difference for bug ' + row_1[0])
                            print(reasons_for_uplift_1)
                            print(reasons_for_uplift_2)

                    print('Failure categorization')
                    for (row_1, row_2) in results:
                        reasons_for_failure_1 = row_1[3].split('^')
                        reasons_for_failure_2 = row_2[3].split('^')
                        if set(reasons_for_failure_1) != set(reasons_for_failure_2):
                            print('Difference for bug ' + row_1[0])
                            print(reasons_for_failure_1)
                            print(reasons_for_failure_2)
    elif args.type == 'same':
        for channel in channels:
            with open('manual_classification/result_le/uplift_fault_inducing_vs_non_fault_inducing_' + channel + '.csv', 'r') as input_file_1:
                with open('manual_classification/result_marco/uplift_fault_inducing_vs_non_fault_inducing_' + channel + '.csv', 'r') as input_file_2:
                    csv_reader_1 = csv.reader(input_file_1)
                    csv_reader_2 = csv.reader(input_file_2)
                    results = zip(csv_reader_1, csv_reader_2)
                    print('Uplift categorization')
                    for (row_1, row_2) in results:
                        reasons_for_uplift_1 = row_1[2].split('^')
                        reasons_for_uplift_2 = row_2[2].split('^')
                        if set(reasons_for_uplift_1) == set(reasons_for_uplift_2):
                            print(row_1[0], reasons_for_uplift_1)
