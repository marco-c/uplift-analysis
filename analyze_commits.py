import os
import json
import pickle
import gzip
from datetime import (datetime, timedelta)
from libmozdata import patchanalysis
from libmozdata import hgmozilla
from libmozdata import utils
from libmozdata.bugzilla import Bugzilla

# Directory that holds the results ('bug_inducing_uplifts_fixed_by_uplifts' and 'bug_inducing_uplifts_fixed_by_commits').
# 'bug_inducing_uplifts_fixed_by_uplifts' holds the analysis of uplifts inducing bugs fixed by other uplifts;
# 'bug_inducing_uplifts_fixed_by_commits' holds the analysis of uplifts inducing bugs fixed by generic commits.
DIR = 'bug_inducing_uplifts_fixed_by_uplifts'

# Load list of uplifts.
with open('bugs_and_commits.json', 'r') as f:
    bugs_and_commits = json.load(f)

def get_bug_from_commit(commit):
    for channel, elems in bugs_and_commits.items():
        for elem in elems:
            if commit in elem['commits']:
                return channel, elem['bug_id']

uplifts = set(sum([elem['commits'] for elems in bugs_and_commits.values() for elem in elems], []))

# Load list of bug-inducing commits.
with open(os.path.join(DIR, 'bug_inducing_commits.json'), 'r') as f:
    bug_inducing_commits_by_bug = json.load(f)

bug_inducing_commits = set(sum(bug_inducing_commits_by_bug.values(), []))

# The bug-inducing uplifts are given by the intersection between the uplifts and the bug-inducing commits.
bug_inducing_uplifts = uplifts.intersection(bug_inducing_commits)

preloaded_bugs = {}
for channel in ['release', 'beta', 'aurora']:
    preloaded_bugs[channel] = []
    try:
        with gzip.GzipFile('bugs_' + channel + '_uplifts.pickle.gz', 'rb') as f:
            preloaded_bugs[channel] += pickle.load(f)
    except IOError:
        pass

def load_bug(channel, bug_id):
    # Try loading from the pickle.
    for bug in preloaded_bugs[channel]:
        if str(bug['id']) == str(bug_id):
            return bug

    return None


analyzed_commits = {}

i = 1
for commit in bug_inducing_uplifts:
    print(str(i) + ' out of ' + str(len(bug_inducing_uplifts)))
    i += 1

    channel, bug_id = get_bug_from_commit(commit)

    bug = load_bug(channel, bug_id)

    try:
        info = patchanalysis.bug_analysis(bug if bug is not None else bug_id, channel)

        # Remove unneeded info.
        info.update(info['patches'][commit])
        del info['source']
        del info['url']
        del info['patches']
        del info['uplift_accepted']
        del info['uplift_comment']
        del info['users']
        del info['uplift_author']

        # Transform timedelta objects to number of seconds (to make them JSON-serializable).
        info['landing_delta'] = int(info['landing_delta'].total_seconds())
        info['response_delta'] = int(info['response_delta'].total_seconds())
        info['release_delta'] = int(info['release_delta'].total_seconds())

        analyzed_commits[commit] = info
    except Exception as e:
        print('Error with bug ' + str(bug_id) + ': ' + str(e))

with open(os.path.join(DIR, 'analyzed_commits.json'), 'w') as f:
    json.dump(analyzed_commits, f)
