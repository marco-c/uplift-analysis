import csv
import re
from libmozdata import hgmozilla

import get_bugs

bug_inducing_commits = []
with open('all_bugs/bug_inducing_commits.csv', 'rb') as csv_file:
    csv_reader = csv.reader(csv_file)
    next(csv_reader)
    for row in csv_reader:
        bug_inducing_commits += [rev for rev in row[1].split('^') if rev != '']

bug_inducing_commits = list(set(bug_inducing_commits))

bug_pattern1 = re.compile('[\t ]*bug[\t ]*([0-9]+)')
bug_pattern2 = re.compile('b=([0-9]+)')
bug_pattern3 = re.compile('bug=([0-9]+)')

bug_inducing_bugs = list()

for commit in bug_inducing_commits:
    meta = hgmozilla.Revision.get_revision(channel='nightly', node=commit)
    desc = meta['desc'].lower()
    bug_id_match = re.search(bug_pattern1, desc)
    if not bug_id_match:
        bug_id_match = re.search(bug_pattern2, desc)
    if not bug_id_match:
        bug_id_match = re.search(bug_pattern3, desc)
    if bug_id_match:
        bug_inducing_bugs.append(int(bug_id_match.group(1)))
    else:
        print(meta)
        print('')

bug_inducing_bugs = list(set(bug_inducing_bugs))

all_bugs = [bug['id'] for bug in get_bugs.get_all()]

with open('independent_metrics/bug_inducing.csv', 'w') as output_file:
    csv_writer = csv.writer(output_file, ['bug_id', 'error_inducing'])
    csv_writer.writerow(['bug_id', 'error_inducing'])
    for bug in all_bugs:
        if bug in bug_inducing_bugs:
            csv_writer.writerow([bug, True])
        else:
            csv_writer.writerow([bug, False])
