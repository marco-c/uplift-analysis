import random
import json
import argparse
import os

import get_bugs

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Mine commit metrics')
    parser.add_argument('type', action='store', choices=['generate', 'validate'])
    parser.add_argument('-n', '--num', action='store', choices=['1', '2'])
    args = parser.parse_args()

    if args.type == 'generate':
        bugs = get_bugs.__download_bugs('all_bugs', get_bugs.__get_all_bugs_query())

        # 380 is the size of the sample needed to get a 95% confidence level with 5% interval for 35815.
        bugs_sample = random.sample(bugs, 380)

        actual_bugs = get_bugs.__filter_bugs(bugs_sample)

        print(str(len(actual_bugs)) + ' identified as actual bugs out of a sample of ' + str(len(bugs_sample)) + ' bugs (the total is ' + str(len(bugs)) + ')')

        to_save = [{ 'id': bug['id'], 'is_bug': bug in actual_bugs, 'correct': None } for bug in bugs_sample]

        with open('all_bugs/bugs_to_validate_1.json', 'w') as f:
            json.dump(to_save, f)
        with open('all_bugs/bugs_to_validate_2.json', 'w') as f:
            json.dump(to_save, f)
    elif args.type == 'validate':
        if args.num is None:
            parser.print_help()
            raise Exception('Missing \'num\' argument.')

        with open('all_bugs/bugs_to_validate_' + args.num + '.json', 'r') as f:
            bugs = json.load(f)

        for bug in [b for b in bugs if b['correct'] is None]:
            os.system('firefox https://bugzilla.mozilla.org/show_bug.cgi?id=' + str(bug['id']))

            progress = str(len([e for e in bugs if e['correct']])) + ' / ' + str(len([e for e in bugs if e['correct'] is not None]))

            v = raw_input(progress + ' - Is bug ' + str(bug['id']) + ' a bug (b) or a feature (f)? (e) to exit: ')

            if v in ['e', 'exit']:
                break

            bug['correct'] = (bug['is_bug'] and v in ['b', 'bug']) or (not bug['is_bug'] and v in ['f', 'feature'])

        with open('all_bugs/bugs_to_validate_' + args.num + '.json', 'w') as f:
            json.dump(bugs, f)
