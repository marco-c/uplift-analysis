import csv

import get_bugs
import utils


def removeCharacter(word):
    cleaned_word = ''
    unwanted_ch = ["'", '"', '|']
    for l in word:
        if not l in unwanted_ch:
           cleaned_word += l
    return cleaned_word



def removePunctuation(word):
    # remove quotes
    word = removeCharacter(word)
    if len(word):
        if word[-1] in '!*+,-.:;?_':
            return word[:-1]
    return word


def are_bugs_linked(bug1, bug2):
    in_history = False

    for history in bug1['history']:
        for change in history['changes']:
            if change['added'] == str(bug2['id']):
                in_history = True
                break

    for comment in bug1['comments']:
        if unicode(bug2['id']) in [removePunctuation(w) for w in comment['text'].split(' ')]:
            in_history = True
            break

    for history in bug2['history']:
        for change in history['changes']:
            if change['added'] == str(bug1['id']):
                in_history = True
                break

    for comment in bug2['comments']:
        if unicode(bug1['id']) in [removePunctuation(w) for w in comment['text'].split(' ')]:
            in_history = True
            break

    return bug1['id'] in bug2['depends_on'] or \
           bug1['id'] in bug2['blocks'] or\
           ('https://bugzilla.mozilla.org/show_bug.cgi?id=' + str(bug1['id'])) in bug2['see_also'] or\
           in_history


if __name__ == '__main__':
    bugs = get_bugs.get_all()
    cloned_bug_map = utils.get_cloned_map(bugs)


    def get_bug_from_id(bug_id):
        return [bug for bug in bugs if bug['id'] == int(bug_id)][0]


    total_count = 0
    unlinked_count = 0
    wrongly_classified_count = 0

    with open('manual_classification/bm25_results_initial_after_auto.csv', 'w') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(['bug1', 'bug2', '', 'title1', 'title2'])

        with open('manual_classification/bm25_results_initial.csv', 'r') as f:
            csv_reader = csv.reader(f)
            next(csv_reader)  # skip header
            for bug1_link, bug2_link, classification, title1, title2 in csv_reader:
                bug1_id = bug1_link[len('https://bugzilla.mozilla.org/show_bug.cgi?id='):]
                bug1 = get_bug_from_id(bug1_id)
                bug2_id = bug2_link[len('https://bugzilla.mozilla.org/show_bug.cgi?id='):]
                bug2 = get_bug_from_id(bug2_id)

                linked = are_bugs_linked(bug1, bug2)

                total_count += 1
                if not linked:
                    unlinked_count += 1

                auto_classification = ''

                if bug1['id'] in cloned_bug_map:
                    for bug in cloned_bug_map[bug1['id']]:
                        if bug2['id'] == bug['id']:
                            auto_classification = 'y'
                            break

                if bug2['id'] in cloned_bug_map:
                    for bug in cloned_bug_map[bug2['id']]:
                        if bug1['id'] == bug['id']:
                            auto_classification = 'y'
                            break

                if not auto_classification and not linked:
                    auto_classification = 'n'

                if classification and auto_classification and auto_classification != classification:
                    wrongly_classified_count += 1

                if not classification:
                    classification = auto_classification

                csv_writer.writerow([bug1_link, bug2_link, classification, title1, title2])


print('{} out of {} are unlinked'.format(unlinked_count, total_count))
print('{} out of {} are wrongly classified by the heuristic'.format(wrongly_classified_count, total_count))
