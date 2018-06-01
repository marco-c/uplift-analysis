import csv
from collections import defaultdict
from datetime import datetime, timedelta
import json
import re

import requests
from libmozdata import hgmozilla
from libmozdata.utils import as_utc, get_date_ymd

import get_bugs
import utils
import versions


bugs = get_bugs.get_all()
uplifts = utils.get_uplifts(bugs)

with open('all_bugs/bug_inducing_bugs.json', 'r') as f:
    bug_inducing_bugs = json.load(f)

try:
    with open('all_bugs/shipped_to_users.json', 'r') as f:
        regressions_shipped_to_users = json.load(f)
except:
    regressions_shipped_to_users = {}

for uplift in uplifts:
    if uplift['component'] == 'Pocket':
        continue

    if str(uplift['id']) not in bug_inducing_bugs:
        continue

    if str(uplift['id']) in regressions_shipped_to_users:
        continue

    regressions = bug_inducing_bugs[str(uplift['id'])]
    regressions = [[bug for bug in bugs if bug['id'] == int(regression)][0] for regression in regressions]

    to_ignore = True
    for channel in utils.uplift_channels(uplift):
        uplift_date = utils.get_uplift_date(uplift, channel)

        if uplift_date is None or uplift_date < as_utc(datetime(2014, 9, 1)) or uplift_date >= as_utc(datetime(2016, 8, 24)):
            continue

        to_ignore = False

    if to_ignore:
        continue

    uplift_versions = versions.get_versions(uplift)
    if len(uplift_versions) == 0:
        print(uplift['id'])
        continue
    uplift_version = min(uplift_versions)

    shipped_to_users = set()
    for regression in regressions:
        regression_fix_versions = versions.get_versions(regression)
        if len(regression_fix_versions) == 0:
            print(regression['id'])
            continue

        regression_fix_version = min(regression_fix_versions)
        if uplift_version < regression_fix_version:
            shipped_to_users.add(regression['id'])

    regressions_shipped_to_users[str(uplift['id'])] = list(shipped_to_users)

    with open('all_bugs/shipped_to_users.json', 'w') as f:
        json.dump(regressions_shipped_to_users, f)


for channel in ['aurora', 'beta', 'release']:
    with open('all_bugs/shipped_to_users_{}.csv'.format(channel), 'w') as output_file:
        csv_writer = csv.writer(output_file, ['uplift_id', 'regression_ids'])
        csv_writer.writerow(['bug_id', 'regression_ids'])

        for uplift in uplifts:
            if str(uplift['id']) not in regressions_shipped_to_users:
                continue

            regression_ids = regressions_shipped_to_users[str(uplift['id'])]
            if len(regression_ids) == 0:
                continue

            channels = utils.uplift_channels(uplift)
            if channel not in channels:
                continue

            csv_writer.writerow([uplift['id'], '^'.join([str(i) for i in regression_ids])])

    with open('manual_classification/regressions_shipped_to_users_{}.csv'.format(channel), 'w') as output_file:
        csv_writer = csv.writer(output_file, ['uplift_id', 'regression_id', 'reproducible'])
        csv_writer.writerow(['uplift_id', 'regression_id', 'reproducible'])

        for uplift in uplifts:
            if str(uplift['id']) not in regressions_shipped_to_users:
                continue

            regression_ids = regressions_shipped_to_users[str(uplift['id'])]
            if len(regression_ids) == 0:
                continue

            channels = utils.uplift_channels(uplift)
            if channel not in channels:
                continue

            for regression_id in regression_ids:
                csv_writer.writerow([uplift['id'], regression_id, ''])
