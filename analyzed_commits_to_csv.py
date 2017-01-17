import os
import json
import csv

if __name__ == '__main__':
    DIR = 'all_bugs'

    # Load list of uplifts.
    with open('bugs_and_commits.json', 'r') as f:
        bugs_and_commits = json.load(f)

    def get_bug_from_commit(commit):
        for channel, elems in bugs_and_commits.items():
            for elem in elems:
                if commit in elem['commits']:
                    return channel, elem['bug_id']

    uplifts = set(sum([elem['commits'] for elems in bugs_and_commits.values() for elem in elems], []))

    with open(os.path.join(DIR, 'analyzed_commits.json'), 'r') as f:
        analyzed_commits = json.load(f)

    for commit in analyzed_commits.keys():
        analyzed_commits[commit]['landing_delta'] = int(round(float(analyzed_commits[commit]['landing_delta']) / 86400))
        analyzed_commits[commit]['response_delta'] = int(round(float(analyzed_commits[commit]['response_delta']) / 86400))
        analyzed_commits[commit]['release_delta'] = int(round(float(analyzed_commits[commit]['release_delta']) / 86400))

    analyzed_bugs = {}
    for commit in uplifts:
        channel, bug_id = get_bug_from_commit(commit)

        if commit in analyzed_commits:
            data = analyzed_commits[commit].copy()

            if 'languages' in data:
                del data['languages']

            if bug_id in analyzed_bugs:
                for key in ['developer_familiarity_overall', 'code_churn_overall', 'backout_num', 'code_churn_last_3_releases', 'reviewer_familiarity_overall', 'changes_size', 'reviewer_familiarity_last_3_releases', 'changes_del', 'test_changes_size', 'modules_num', 'changes_add', 'developer_familiarity_last_3_releases']:
                    analyzed_bugs[bug_id][key] += data[key]
            else:
                analyzed_bugs[bug_id] = {
                    'bug_id': bug_id,
                }
                analyzed_bugs[bug_id].update(data)

    with open('independent_metrics/basic.csv', 'w') as output_file:
        keys = list(list(analyzed_bugs.values())[0].keys())
        keys.remove('bug_id')
        csv_writer = csv.DictWriter(output_file, ['bug_id'] + sorted(keys))
        csv_writer.writeheader()
        csv_writer.writerows(analyzed_bugs.values())
