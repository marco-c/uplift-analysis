import json, re, string, pprint
import get_bugs

def relatedComments(bug_item, attach_id):
    for comment_item in bug_item['comments']:
        raw_comment = comment_item['text']
        matched = re.findall(r'Review of attachment ([0-9]+)', raw_comment)
        if len(matched):
            attach_id = matched[0]
            comment_times, comment_words = 0, 0
            for line in raw_comment.split('\n')[2:]:
                if not (line.startswith('>') or line.startswith('Review of attachment') or line.startswith('(In reply to')):
                    if re.search(r'[a-zA-Z]', line):
                        comment_words += len(re.findall(r'\S+', line.encode('utf-8').translate(None, string.punctuation)))
                        comment_times += 1
#            print comment_times, comment_words
    return

def requestAndFirstFlag(change_item, added, activity_date, review_history_dict, last_review_request_date):
    attach_id = change_item['attachment_id']
    if '?' in added:
        last_review_request_date = activity_date
        review_history_dict[attach_id] = {'request': activity_date}
        print '\t', attach_id, activity_date, added
    else:
        print '\t', attach_id, activity_date, added
        if attach_id in review_history_dict:
            if not '1st_flag' in review_history_dict[attach_id]:
                review_history_dict[attach_id]['1st_flag'] = activity_date
        else:
            review_history_dict[attach_id] = {'request': last_review_request_date, '1st_flag':activity_date}
    return review_history_dict, last_review_request_date

def reviewHistory(bug_item):
    review_history_dict = dict()
    last_request_date = None
    feedback_hisotory_dict = dict()
    for activity in bug_item['history']:
        activity_date = re.sub(r'[^0-9]', '', activity['when'])
        for change_item in activity['changes']:
            added = change_item['added']
            if len(added):
                if 'review' in added or 'feedback' in added:
                    attach_id = change_item['attachment_id']
                    if '?' in added:
                        last_request_date = activity_date
                        review_history_dict[attach_id] = {'request': activity_date}
                        print '\t', attach_id, activity_date, added
                    else:
                        print '\t', attach_id, activity_date, added
                        if attach_id in review_history_dict:
                            if 'review' in added:
                                if not '1st_review' in review_history_dict[attach_id]:
                                    review_history_dict[attach_id]['1st_review'] = activity_date
                            elif 'feedback' in added:
                                if not '1st_feedback' in review_history_dict[attach_id]:
                                    review_history_dict[attach_id]['1st_feedback'] = activity_date
                        else:
                            if 'review' in added:
                                review_history_dict[attach_id] = {'request': last_request_date, '1st_review': activity_date}
                            elif 'feedback' in added:
                                review_history_dict[attach_id] = {'request': last_request_date, '1st_feedback': activity_date}

    pprint.pprint(review_history_dict)
    return review_history_dict

if __name__ == '__main__':
    DEBUG = True
    
    '''print 'Loading bug reports ...'
    all_bugs = get_bugs.get_all()
    if DEBUG:
        bug_list = all_bugs[:5]
    else:
        bug_list = all_bugs'''
    
    ##### DEBUGING DATA #######
    bug_list = ()
    with open('all_bugs/all_bugs0.json') as f:
        bug_list = json.load(f)[:50]
    ##### DEBUGING DATA #######
    
    print 'Extracting metrics ...'
    output_list = list()
    for bug_item in bug_list:
        bug_id = bug_item['id']
        print bug_id
        for attach_item in bug_item['attachments']:
#            print attach_item
            if attach_item['is_patch']:
                if attach_item['content_type'] == 'text/plain':
                    attach_flags = attach_item['flags']
                    if len(attach_flags):
                        last_flag = attach_flags[-1]
                        reviewer = last_flag['setter']
                        review_date = re.sub(r'[^0-9]', '', last_flag['modification_date'])
                        review_status = last_flag['status']
                        # TODO: attachment ID
#                        print '\t', reviewer, review_status
        relatedComments(bug_item, '')
        review_history_dict = reviewHistory(bug_item)

                        