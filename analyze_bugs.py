# stdbuf --output=0 --error=0 python analyze_bugs.py all_bugs >> all_bugs/analyze_bugs.log 2>&1
# tail -f all_bugs/analyze_bugs.log

import os
import json
import argparse
import csv
import utils
import traceback
from libmozdata import patchanalysis

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
    'jones.chris.g@gmail.com': ['cjones.bugs@gmail.com', 'cjones@mozilla.com'],
    'kit@yakshaving.ninja': ['kit@mozilla.com', 'kitcambridge@mozilla.com', 'kcambridge@mozilla.com'],
    'kit@mozilla.com': ['kit@yakshaving.ninja', 'kitcambridge@mozilla.com', 'kcambridge@mozilla.com'],
    'kitcambridge@mozilla.com': ['kit@mozilla.com', 'kit@yakshaving.ninja', 'kcambridge@mozilla.com'],
    'kcambridge@mozilla.com': ['kit@mozilla.com', 'kitcambridge@mozilla.com', 'kit@yakshaving.ninja'],
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Mine commit metrics')
    parser.add_argument('type', action='store', default='all_bugs', choices=['all_bugs', 'uplift_bugs'])
    args = parser.parse_args()

    DIR = args.type

    bugs = get_bugs.get_all()
    all_uplifts = utils.get_uplifts(bugs)

    try:
        with open(os.path.join(DIR, 'analyzed_bugs.json'), 'r') as f:
            analyzed_bugs = json.load(f)
    except:
        analyzed_bugs = dict()

    remaining_uplifts = [bug for bug in all_uplifts if str(bug['id']) not in analyzed_bugs]

    i = len(analyzed_bugs)
    for bug in remaining_uplifts:
        i += 1
        print(str(i) + ' out of ' + str(len(all_uplifts)) + ': ' + str(bug['id']))

        uplift_channels = utils.uplift_channels(bug)

        try:
            info = patchanalysis.bug_analysis(bug, uplift_channels[0], author_cache)

            # Translate sets into lists, as sets are not JSON-serializable.
            info['users']['authors'] = list(info['users']['authors'])
            info['users']['reviewers'] = list(info['users']['reviewers'])
  
            del info['uplift_accepted']
            del info['uplift_comment']
            del info['uplift_author']
            del info['landing_delta']
            del info['response_delta']
            del info['release_delta']
            del info['landings']

            info['component'] = bug['component']
            info['channels'] = uplift_channels
            info['types'] = get_bug_types(bug)

            for channel in uplift_channels:
                uplift_info = patchanalysis.uplift_info(bug, channel)
                del uplift_info['landings']
                info[channel + '_uplift_info'] = uplift_info
                # Transform timedelta objects to number of seconds (to make them JSON-serializable).
                info[channel + '_uplift_info']['landing_delta'] = int(uplift_info['landing_delta'].total_seconds())
                info[channel + '_uplift_info']['response_delta'] = int(uplift_info['response_delta'].total_seconds())
                info[channel + '_uplift_info']['release_delta'] = int(uplift_info['release_delta'].total_seconds())

            analyzed_bugs[str(bug['id'])] = info
        except Exception as e:
            print('Error with bug ' + str(bug['id']) + ': ' + str(e))
            traceback.print_exc()

        with open(os.path.join(DIR, 'analyzed_bugs.json'), 'w') as f:
            json.dump(analyzed_bugs, f)


    rows = []
    row_keys = set()
    rows_any = []
    rows_per_channel = {
      'release': [],
      'beta': [],
      'aurora': [],
    }
    row_per_channel_keys = set()
    for bug_id, info in analyzed_bugs.iteritems():
        info['bug_id'] = bug_id

        # Merge info from commits.
        for commit, commit_info in info['patches'].items():
            for key in ['developer_familiarity_overall', 'code_churn_overall', 'code_churn_last_3_releases', 'reviewer_familiarity_overall', 'changes_size', 'reviewer_familiarity_last_3_releases', 'changes_del', 'test_changes_size', 'modules_num', 'changes_add', 'developer_familiarity_last_3_releases', 'languages']:
                if key in info:
                    info[key] += commit_info[key]
                else:
                    info[key] = commit_info[key]
        del info['patches']

        # Add info regarding users.
        info['bug_creator'] = info['users']['creator']['name']
        info['bug_assignee'] = info['users']['assignee']['name']
        info['patch_authors'] = '^'.join(info['users']['authors'])
        info['patch_reviewers'] = '^'.join(info['users']['reviewers'])
        del info['users']

        # Expand arrays.
        for key in info.keys():
            if isinstance(info[key], list):
                info[key] = '^'.join(list(set(info[key])))

        # Add uplift-related info.
        info_before = info.copy()
        del info_before['channels']
        for channel in ['release', 'beta', 'aurora']:
            if (channel + '_uplift_info') in info_before:
                del info_before[channel + '_uplift_info']

        any_added = False
        for channel in ['release', 'beta', 'aurora']:
            if (channel + '_uplift_info') not in info:
                continue

            row_per_channel = info_before.copy()

            info[channel + '_landing_delta'] = info[channel + '_uplift_info']['landing_delta']
            info[channel + '_response_delta'] = info[channel + '_uplift_info']['response_delta']
            info[channel + '_release_delta'] = info[channel + '_uplift_info']['release_delta']
            info[channel + '_uplift_comment_length'] = len(info[channel + '_uplift_info']['uplift_comment']['text']) if info[channel + '_uplift_info']['uplift_comment'] is not None else 0
            info[channel + '_uplift_requestor'] = info[channel + '_uplift_info']['uplift_comment']['author'] if info[channel + '_uplift_info']['uplift_comment'] is not None else ''
            info[channel + '_uplift_accepted'] = info[channel + '_uplift_info']['uplift_accepted']
            del info[channel + '_uplift_info']

            row_per_channel['landing_delta'] = info[channel + '_landing_delta']
            row_per_channel['response_delta'] = info[channel + '_response_delta']
            row_per_channel['release_delta'] = info[channel + '_release_delta']
            row_per_channel['uplift_comment_length'] = info[channel + '_uplift_comment_length']
            row_per_channel['uplift_requestor'] = info[channel + '_uplift_requestor']
            rows_per_channel[channel].append(row_per_channel)

            if not any_added:
                rows_any.append(row_per_channel)
                any_added = True

            row_per_channel_keys |= set(row_per_channel.keys())

        # Add keys to the set of keys.
        row_keys |= set(info.keys())

        rows.append(info)


    row_keys.remove('bug_id')
    row_keys = ['bug_id'] + sorted(list(row_keys))

    with open('independent_metrics/basic.csv', 'w') as output_file:
        csv_writer = csv.DictWriter(output_file, row_keys)
        csv_writer.writeheader()
        csv_writer.writerows(rows)


    row_per_channel_keys.remove('bug_id')
    row_per_channel_keys = ['bug_id'] + sorted(list(row_per_channel_keys))

    with open('independent_metrics/basic_any.csv', 'w') as output_file:
        csv_writer = csv.DictWriter(output_file, row_per_channel_keys)
        csv_writer.writeheader()
        csv_writer.writerows(rows_any)

    for channel in ['release', 'beta', 'aurora']:
        with open('independent_metrics/basic_' + channel + '.csv', 'w') as output_file:
            csv_writer = csv.DictWriter(output_file, row_per_channel_keys)
            csv_writer.writeheader()
            csv_writer.writerows(rows_per_channel[channel])
