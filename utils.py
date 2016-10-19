from libmozdata import bugzilla

# Assume query ends with 'limit=500&order=bug_id&fXXX=bug_id&oXXX=greaterthan&vXXX='.
def get_ids(query):
    ids = []

    while True:
        new_ids = []

        def bughandler(bug):
            ids.append(bug['id'])
            new_ids.append(bug['id'])

        bugzilla.Bugzilla(query + str(max(ids) if len(ids) > 0 else 0) + '&include_fields=id', bughandler=bughandler).get_data().wait()

        if len(new_ids) < 500:
            break

    return ids


# Given a list of bugs and a query, returns the IDs of the bugs that
# the query returns and that are not in the list.
def get_missing_bugs(bugs, query):
    return set(get_ids(query)).difference(set([bug['id'] for bug in bugs]))
