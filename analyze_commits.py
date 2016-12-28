import os
import json
import pickle
import gzip
import argparse
import sys
from datetime import (datetime, timedelta)
from libmozdata import patchanalysis
from libmozdata import hgmozilla
from libmozdata import utils
from libmozdata.bugzilla import Bugzilla

import get_bugs

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Mine commit metrics')
    parser.add_argument('type', action='store', default='all_bugs', choices=['all_bugs', 'uplift_bugs'])
    args = parser.parse_args()

    DIR = args.type

    # Load list of uplifts.
    with open('bugs_and_commits.json', 'r') as f:
        bugs_and_commits = json.load(f)

    def get_bug_from_commit(commit):
        for channel, elems in bugs_and_commits.items():
            for elem in elems:
                if commit in elem['commits']:
                    return channel, elem['bug_id']

    uplifts = set(sum([elem['commits'] for elems in bugs_and_commits.values() for elem in elems], []))

    preloaded_bugs = {}
    for channel in ['release', 'beta', 'aurora']:
        preloaded_bugs[channel] = []
        try:
            with gzip.GzipFile('bugs_' + channel + '_uplifts.pickle.gz', 'rb') as f:
                preloaded_bugs[channel] += pickle.load(f)
        except IOError:
            pass

    other_preloaded_bugs = get_bugs.get_all()

    def load_bug(channel, bug_id):
        # Try loading from the pickle.
        for bug in preloaded_bugs[channel]:
            if int(bug['id']) == int(bug_id):
                return bug

        for bug in other_preloaded_bugs:
            if int(bug['id']) == int(bug_id):
                return bug

        return None


    try:
        with open(os.path.join(DIR, 'analyzed_commits.json'), 'r') as f:
            analyzed_commits = json.load(f)
    except:
        analyzed_commits = dict()

    remaining_uplifts = [commit for commit in uplifts if commit not in analyzed_commits]

    i = len(analyzed_commits)
    for commit in remaining_uplifts:
        channel, bug_id = get_bug_from_commit(commit)

        i += 1
        print(str(i) + ' out of ' + str(len(uplifts)) + ': ' + str(commit))

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
            if 'landings' in info:
                del info['landings']

            # Transform timedelta objects to number of seconds (to make them JSON-serializable).
            info['landing_delta'] = int(info['landing_delta'].total_seconds())
            info['response_delta'] = int(info['response_delta'].total_seconds())
            info['release_delta'] = int(info['release_delta'].total_seconds())

            analyzed_commits[commit] = info
        except Exception as e:
            print('Error with bug ' + str(bug_id) + ': ' + str(e))

        with open(os.path.join(DIR, 'analyzed_commits.json'), 'w') as f:
            json.dump(analyzed_commits, f)
