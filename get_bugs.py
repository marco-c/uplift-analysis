import sys
import os
import copy
import json
import gzip
from pprint import pprint

from libmozdata import bugzilla
from libmozdata import patchanalysis

bugs = []
try:
    with gzip.GzipFile('all_bugs.json.gz', 'rb') as f:
        bugs += json.load(f)
except IOError:
    pass

print('Loaded ' + str(len(bugs)) + ' bugs.')

# All RESOLVED/VERIFIED FIXED bugs in the Firefox and Core products between 2014-07-22 (release date of 31.0) and 2016-08-24 (release date of 48.0.2).
search_query = 'product=Core&product=Firefox&'
'bug_status=RESOLVED&bug_status=VERIFIED&resolution=FIXED&'
'f1=creation_ts&o1=greaterthan&v1=2014-07-22&f2=creation_ts&o2=lessthan&v1=2016-08-24'

found = []
finished = False
while not finished:
    bugs_dict = dict()

    def bughandler(bug, data):
        bugid = str(bug['id'])

        if bugid not in bugs_dict:
            bugs_dict[bugid] = dict()

        for k, v in bug.items():
            bugs_dict[bugid][k] = v

    def commenthandler(bug, bugid, data):
        bugid = str(bugid)

        if bugid not in bugs_dict:
            bugs_dict[bugid] = dict()

        bugs_dict[bugid]['comments'] = bug['comments']

    def historyhandler(bug, data):
        bugid = str(bug['id'])

        if bugid not in bugs_dict:
            bugs_dict[bugid] = dict()

        bugs_dict[bugid]['history'] = bug['history']

    bugzilla.Bugzilla(search_query + '&limit=500&offset=' + str(len(bugs)), bughandler=bughandler, commenthandler=commenthandler, historyhandler=historyhandler).get_data().wait()

    found = [bug for bug in bugs_dict.values()]

    print('Found ' + str(len(found)) + ' bugs.')

    bugs += found

    if len(bugs) % 5000 == 0 or len(found) < 500:
        with gzip.GzipFile('all_bugs.json.gz', 'wb') as f:
            json.dump(bugs, f)

    if len(found) < 500:
        finished = True

print('Total number of bugs: ' + str(len(bugs)))



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
      'crash', 'regression', 'regressionwindow-wanted', 'jsbugmon'
    ]
    return any(keyword in bug['keywords'] for keyword in keywords)

# If the bug title contains these substrings, it's definitely a bug.
def bug_check_title(bug):
    keywords = [
      'failure', 'crash', 'bug', 'differential testing', 'error', 'addresssanitizer'
    ]
    return any(keyword in bug['summary'].lower() for keyword in keywords)

bug_rules = [
  has_crash_signature,
  has_str,
  has_regression_range,
  has_url,
  bug_check_keywords,
  bug_check_title,
]



actual_bugs = [bug for bug in bugs if any(rule(bug) for rule in bug_rules) and not any(rule(bug) for rule in feature_rules)]

print('Total number of actual bugs: ' + str(len(actual_bugs)))
