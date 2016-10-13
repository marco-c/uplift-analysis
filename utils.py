from libmozdata import bugzilla

# Given a list of bugs and a query, returns the IDs of the bugs that
# the query returns and that are not in the list.
def get_missing_bugs(bugs, query, last_used_field_number)
    ids = []

    field_number = last_used_field_number + 1

    while True:
        new_ids = []

        def bughandler(bug, data):
            ids.append(bug['id'])
            new_ids.append(bug['id'])

        bugzilla.Bugzilla(query + '&limit=500&order=bug_id&f' + str(field_number) + '=bug_id&o' + str(field_number) + '=greaterthan&v' + str(field_number) + '=' + str(max(ids) if len(ids) > 0 else 0) + '&include_fields=id', bughandler=bughandler).get_data().wait()

        if len(new_ids) < 500:
            break

    return set(ids).difference(set([bug['id'] for bug in bugs]))
