import sys
import os
import copy
import json
import gzip
import math
from pprint import pprint

from libmozdata import bugzilla
from libmozdata import patchanalysis

bugs = []

i = 0
while True:
    try:
        with open('all_bugs/all_bugs' + str(i) + '.json', 'r') as f:
            bugs += json.load(f)
        i += 1
    except IOError:
        break

print('Loaded ' + str(len(bugs)) + ' bugs.')

# All RESOLVED/VERIFIED FIXED bugs in the Firefox and Core products filed between 2014-07-22 (release date of 31.0) and 2016-08-24 (release date of 48.0.2).
search_query = 'product=Core&product=Firefox&' +\
'bug_status=RESOLVED&bug_status=VERIFIED&resolution=FIXED&' +\
'f1=creation_ts&o1=greaterthan&v1=2014-07-22&f2=creation_ts&o2=lessthan&v1=2016-08-24&' +\
'limit=500&order=bug_id&f3=bug_id&o3=greaterthan&v3='

last_id = max([bug['id'] for bug in bugs])

found = []
finished = False
while not finished:
    bugs_dict = dict()

    def bughandler(bug):
        bugid = str(bug['id'])

        if bugid not in bugs_dict:
            bugs_dict[bugid] = dict()

        for k, v in bug.items():
            bugs_dict[bugid][k] = v

    def commenthandler(bug, bugid):
        bugid = str(bugid)

        if bugid not in bugs_dict:
            bugs_dict[bugid] = dict()

        bugs_dict[bugid]['comments'] = bug['comments']

    def historyhandler(bug):
        bugid = str(bug['id'])

        if bugid not in bugs_dict:
            bugs_dict[bugid] = dict()

        bugs_dict[bugid]['history'] = bug['history']

    bugzilla.Bugzilla(search_query + str(last_id), bughandler=bughandler, commenthandler=commenthandler, historyhandler=historyhandler).get_data().wait()

    found = [bug for bug in bugs_dict.values()]

    last_id = max([last_id] + [bug['id'] for bug in found])

    bugs += found

    print('Total number of bugs: ' + str(len(bugs)))

    if len(found) != 0 and (len(bugs) % 5000 == 0 or len(found) < 500):
        for i in range(0, int(math.ceil(float(len(bugs)) / 1000))):
            with open('all_bugs/all_bugs' + str(i) + '.json', 'w') as f:
                json.dump(bugs[i*1000:(i+1)*1000], f)

    if len(found) < 500:
        finished = True



# Example bug data: https://bugzilla.mozilla.org/rest/bug/679352
# Example bug comments data: https://bugzilla.mozilla.org/rest/bug/679352/comment
# Example bug history data: https://bugzilla.mozilla.org/rest/bug/679352/history



# If the bug contains these keywords, it's very likely a feature.
def feature_check_keywords(bug):
    keywords = [
        'feature'
    ]
    return any(keyword in bug['keywords'] for keyword in keywords)

feature_rules = [
    feature_check_keywords,
]


# If the bug has a crash signature, it is definitely a bug.
def has_crash_signature(bug):
    return bug['cf_crash_signature'] != ''

# If the bug has steps to reproduce, it is very likely a bug.
def has_str(bug):
    return 'cf_has_str' in bug and bug['cf_has_str'] == 'yes'

# If the bug has a regression range, it is definitely a bug.
def has_regression_range(bug):
    return 'cf_has_regression_range' in bug and bug['cf_has_regression_range'] == 'yes'

# If the bug has a URL, it's very likely a bug that the reported experienced
# on the given URL.
def has_url(bug):
    return bug['url'] != ''

# If the bug contains these keywords, it's definitely a bug.
def bug_check_keywords(bug):
    keywords = [
        'crash', 'regression', 'regressionwindow-wanted', 'jsbugmon',
        'hang', 'topcrash', 'assertion', 'coverity', 'infra-failure',
        'intermittent-failure', 'reproducible', 'stack-wanted',
        'steps-wanted', 'testcase-wanted', 'testcase',
    ]
    return any(keyword in bug['keywords'] for keyword in keywords)

# If the bug title contains these substrings, it's definitely a bug.
def bug_check_title(bug):
    keywords = [
        'failure', 'crash', 'bug', 'differential testing', 'error',
        'addresssanitizer', 'hang', 'jsbugmon', 'leak', 'permaorange',
        'random orange', 'intermittent', 'regression'
    ]
    return any(keyword in bug['summary'].lower() for keyword in keywords)

# If the first comment in the bug contains these substrings, it's likely a bug.
def check_first_comment(bug):
    keywords = [
        'steps to reproduce', 'crash', 'hang', 'assertion', 'failure',
        'leak', 'stack trace', 'regression',
    ]
    return any(keyword in bug['comments'][0]['text'].lower() for keyword in keywords)

# If any of the comments in the bug contains these substirngs, it's likely a bug.
def check_comments(bug):
    keywords = [
        'mozregression', 'safemode', 'safe mode',
        # mozregression messages.
        'Looks like the following bug has the changes which introduced the regression', 'First bad revision',
    ]
    return any(keyword in comment['text'].lower() for comment in bug['comments'] for keyword in keywords)

bug_rules = [
    has_crash_signature,
    has_str,
    has_regression_range,
    has_url,
    bug_check_keywords,
    bug_check_title,
    check_first_comment,
    check_comments,
]



actual_bugs = [bug for bug in bugs if any(rule(bug) for rule in bug_rules) and not any(rule(bug) for rule in feature_rules)]

print('Total number of actual bugs: ' + str(len(actual_bugs)))
