import json
import requests


try:
    with open('all_bugs/versions_data.json', 'r') as f:
        versions_data = json.load(f)
except IOError:
    versions_data = {}


def get_versions(bug_id):
    if bug_id not in versions_data:
        try:
            versions = set()

            data = requests.get('https://bugzilla.mozilla.org/rest/bug/{}'.format(bug_id)).json()

            data = data['bugs'][0]

            for key, val in data.items():
                if not key.startswith('cf_status_firefox'):
                    continue

                if key.startswith('cf_status_firefox_esr'):
                    continue

                version = key[len('cf_status_firefox'):]

                if version == '38_0_5':
                    version = '38.5'

                if val in ['fixed', 'verified']:
                    versions.add(float(version))

            target_milestone = data['target_milestone']
            if target_milestone != '---' and not any(target_milestone.startswith(s) for s in ['FxOS', '2.2']):
                versions.add(float(target_milestone[len('mozilla'):]))

            versions_data[bug_id] = list(versions)

            with open('all_bugs/versions_data.json', 'w') as f:
                json.dump(versions_data, f)
        except:
            print('Error with {}'.format(bug_id))
            print(data)
            raise

    return versions_data[bug_id]
