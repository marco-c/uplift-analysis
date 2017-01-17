import os
import json
import pickle
import gzip
import argparse
import sys
import csv
from datetime import (datetime, timedelta)
from libmozdata import patchanalysis
from libmozdata import hgmozilla
from libmozdata import utils
from libmozdata.bugzilla import Bugzilla

import get_bugs

author_cache = {
    'andrei.br92@gmail.com': ['aoprea@mozilla.com'],
    'bcheng.gt@gmail.com': ['brandon.cheng@protonmail.com'],
    'jwein@mozilla.com': ['jaws@mozilla.com'],
    'Olli.Pettay@helsinki.fi': ['bugs@pettay.fi'],
    'karlt+@karlt.net': ['karlt@mozbugz.karlt.net'],
    'mozilla@jorgk.com': ['jorgk@jorgk.com'],
    'Boris Zbarsky': ['bzbarsky@mit.edu'],
    'dholbert@cs.stanford.edu': ['dholbert@mozilla.com'],
    'nnethercote@mozilla.com': ['n.nethercote@gmail.com'],
    'billm@mozilla.com': ['wmccloskey@mozilla.com'],
    'romain.gauthier@monkeypatch.me': ['rgauthier@mozilla.com'],
    'dougt@dougt.org': ['doug.turner@gmail.com'],
    'seth@mozilla.com': ['seth.bugzilla@blackhail.net'],
    'dao@mozilla.com': ['dao+bmo@mozilla.com'],
    'bsmith@mozilla.com': ['brian@briansmith.org'],
    'georg.fritzsche@googlemail.com': ['gfritzsche@mozilla.com'],
    'kevina@gnu.org': ['kevin.bugzilla@atkinson.dhs.org', 'kevin.firefox.bugzilla@atkinson.dhs.org'],
    'Callek@gmail.com': ['bugspam.Callek@gmail.com'],
    'gavin@gavinsharp.com': ['gavin.sharp@gmail.com'],
    'jwalden@mit.edu': ['jeff.walden@gmail.com', 'jwalden+bmo@mit.edu', 'jwalden+fxhelp@mit.edu', 'jwalden+spammybugs@mit.edu'],
    'mikeperry': ['mikepery@fscked.org', 'mikeperry.unused@gmail.com', 'mikeperry@torproject.org'],
    'kgupta@mozilla.com': ['bugmail@mozilla.staktrace.com'],
    'Shane Caraveo': ['shanec@ActiveState.com', 'mixedpuppy@gmail.com', 'scaraveo@mozilla.com'],
    'scaraveo@mozilla.com': ['Shane Caraveo', 'shanec@ActiveState.com', 'mixedpuppy@gmail.com'],
    'justin.lebar@gmail.com': ['justin.lebar+bug@gmail.com'],
    'sylvestre@mozilla.com': ['sledru@mozilla.com'],
    'mrbkap@gmail.com': ['mrbkap@mozilla.com'],
    'archaeopteryx@coole-files.de': ['aryx.bugmail@gmx-topmail.de'],
    'matspal@gmail.com': ['mats@mozilla.com'],
    'neil@mozilla.com': ['enndeakin@gmail.com'],
    'mfinkle@mozilla.com': ['mark.finkle@gmail.com'],
    'dtownsend@oxymoronical.com': ['dtownsend@mozilla.com'],
    'robert@ocallahan.org': ['roc@ocallahan.org'],
    'andrei.eftimie@softvision.ro': ['andrei@eftimie.com'],
    'sriram@mozilla.com': ['sriram.mozilla@gmail.com'],
    'amccreight@mozilla.com': ['continuation@gmail.com'],
    'mcsmurf@mcsmurf.de': ['bugzilla@mcsmurf.de', 'bugzilla2@mcsmurf.de'],
    'sikeda@mozilla.com': ['sotaro.ikeda.g@gmail.com'],
    'quanxunzhen@gmail.com': ['xidorn+moz@upsuper.org'],
    'jones.chris.g@gmail.com': ['cjones.bugs@gmail.com', 'cjones@mozilla.com']
}

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
            info = patchanalysis.bug_analysis(bug if bug is not None else bug_id, channel, author_cache)

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
