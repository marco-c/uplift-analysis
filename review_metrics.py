from __future__ import division
import json, re, string, pprint
from datetime import datetime
import get_bugs

def relatedComments(bug_item, attach_id):
    total_times, total_words = 0, 0
    commenter_set = set()
    for comment_item in bug_item['comments']:
        commenter_set.add(comment_item['author'])
        raw_comment = comment_item['text']
        matched = re.findall(r'Review of attachment ([0-9]+)', raw_comment)
        if len(matched):
            if attach_id == int(matched[0]):
                comment_times, comment_words = 0, 0
                for line in raw_comment.split('\n')[2:]:
                    if not (line.startswith('>') or line.startswith('Review of attachment') or line.startswith('(In reply to')):
                        if re.search(r'[a-zA-Z]', line):
                            comment_words += len(re.findall(r'\S+', line.encode('utf-8').translate(None, string.punctuation)))
                            comment_times += 1
                total_times += comment_times
                total_words += comment_words
    return total_times, total_words, commenter_set

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

# Compute date interval between two date strings
def dateDiff(d1_str, d2_str):
    d1 = datetime.strptime(d1_str, '%Y%m%d%H%M%S')
    d2 = datetime.strptime(d2_str, '%Y%m%d%H%M%S')
    return round((d2 - d1).total_seconds()/3600, 2)

def reviewHistory(bug_item):
    review_history_dict = dict()
    last_request_date = None
    reviewer_dict = dict()
    reviewer_set, feedbacker_set = set(), set()
    decision_dict = dict()
    for activity in bug_item['history']:
        activity_date = re.sub(r'[^0-9]', '', activity['when'])
        activity_person = activity['who']
        for change_item in activity['changes']:
            added = change_item['added']
            if len(added):
                if added.startswith('review') or added.startswith('feedback') or added.startswith('superreview'):
                    attach_id = change_item['attachment_id']
#                    print '\t', attach_id, activity_date, added.split(', ')
                    for added_flag in added.split(', '):
                        if '?' in added_flag:
                            last_request_date = activity_date
                            if not attach_id in review_history_dict:
                                review_history_dict[attach_id] = {'request': activity_date}
                        else:
                            if 'review' in added_flag:
                                # count unique reviewers
                                reviewer_set.add(activity_person)
                                if attach_id in reviewer_dict:
                                    reviewer_dict[attach_id].add(activity_person)
                                else:
                                    reviewer_dict[attach_id] = set([activity_person])
                                # review decision (+/-)
                                if '+' in added_flag:
                                    if attach_id in decision_dict:
                                        decision_dict[attach_id]['pos'] += 1
                                    else:
                                        decision_dict[attach_id] = {'pos': 1, 'neg': 0}
                                else:
                                    if attach_id in decision_dict:
                                        decision_dict[attach_id]['neg'] += 1
                                    else:
                                        decision_dict[attach_id] = {'pos': 0, 'neg': 1}
                                # find the 1st review
                                if attach_id in review_history_dict:
                                    if not '1st_review' in review_history_dict[attach_id]:
                                        review_history_dict[attach_id]['1st_review'] = activity_date
                                        review_history_dict[attach_id]['iteration'] = 1
                                    else:
                                        review_history_dict[attach_id]['iteration'] += 1
                                else:
                                    review_history_dict[attach_id] = {'request': last_request_date, '1st_review': activity_date, 'iteration': 1}
                                # review iteration
                            elif 'feedback' in added_flag:
                                # count unique people who give feedbacks
                                feedbacker_set.add(activity_person)
                                # find the 1st feedback
                                if attach_id in review_history_dict:
                                    if not '1st_feedback' in review_history_dict[attach_id]:
                                        review_history_dict[attach_id]['1st_feedback'] = activity_date
                                else:
                                    review_history_dict[attach_id] = {'request': last_request_date, '1st_feedback': activity_date}
#    pprint.pprint(review_history_dict, indent=4)
    return review_history_dict, len(reviewer_set), len(feedbacker_set), reviewer_dict, decision_dict


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
        total_patches, obsolete_cnt = 0, 0
        review_history_dict, reviewer_cnt, feedbacker_cnt, reviewer_dict, decision_dict = reviewHistory(bug_item)
#        pprint.pprint(review_history_dict, indent=4)
        for attach_item in bug_item['attachments']:
#            print attach_item
            if attach_item['is_patch']:
                if attach_item['content_type'] == 'text/plain':
                    total_patches += 1
                    attach_id = attach_item['id']
                    attach_flags = attach_item['flags']
                    attach_author = attach_item['creator']
                    attach_date = re.sub(r'[^0-9]', '', attach_item['creation_time'])
                    is_obsolete = attach_item['is_obsolete']
                    # count obsolete patches in a bug
                    if is_obsolete == 1:
                        obsolete_cnt += 1
                    # analyze patches (including the obsolete ones)
                    if len(attach_flags):
                        last_flag = attach_flags[-1]
                        reviewer = last_flag['setter']
                        last_review_date = re.sub(r'[^0-9]', '', last_flag['modification_date'])
                        '''if attach_id in review_history_dict:
                            request_date = review_history_dict[attach_id]['request']
                            if '1st_review' in review_history_dict[attach_id]:
                                first_review_date = review_history_dict[attach_id]['1st_review']
                                response_delay = dateDiff(request_date, first_review_date)
                                review_duration = dateDiff(request_date, last_review_date)
                            if '1st_feedback' in review_history_dict[attach_id]:
                                fist_feedback_date = review_history_dict[attach_id]['1st_feedback']'''
                        
                        '''if request_date == fist_feedback_date:
                            feedback_delay = dateDiff(creation)
                        feedback_delay = dateDiff(request_date, fist_feedback_date)
                        print '\t', attach_id, feedback_delay'''
                        
                        last_review_status = last_flag['status']
                        total_comment_times, total_comment_words, commenter_set = relatedComments(bug_item, attach_id)
                        
                        
                        print 'attach:', attach_id
                        review_iterations = 0
                        feedback_cnt, neg_feedbacks = 0, 0
                        reviewer_set = set()
                        first_review_date, last_review_date, first_feedback_date = None, None, None
                        pos_votes, neg_votes = 0, 0
                        for a_flag in attach_flags:
                            if 'review' in a_flag['name']:
                                if first_review_date == None:
                                    first_review_date = re.sub(r'[^0-9]', '', a_flag['modification_date'])
                                last_review_date = re.sub(r'[^0-9]', '', a_flag['modification_date'])
                                reviewer_set.add(a_flag['setter'])
                                if a_flag['status'] == '+':
                                    pos_votes += 1
                                elif a_flag['status'] == '-':
                                    neg_votes += 1
                                review_iterations += 1
                            elif 'feedback' in a_flag['name']:
                                if first_feedback_date == None:
                                    first_feedback_date = re.sub(r'[^0-9]', '', a_flag['modification_date'])
                                if a_flag['status'] == '-':
                                    neg_feedbacks += 1
                                feedback_cnt += 1
                        # proportion of negative reviews
                        if pos_votes + neg_votes:
                            neg_review_rate =  round(neg_votes/(pos_votes+neg_votes), 2)
                        else:
                            neg_review_rate = -1
                        # proportion of negative feedbacks
                        if feedback_cnt:
                            neg_feedback_rate = round(neg_feedbacks/feedback_cnt, 2)
                        else:
                            neg_feedback_rate = -1
                        # non author voters
                        non_author_voters = len(reviewer_set - set([attach_author]))  
                        # review delay and review duration
                        if first_review_date:
                            response_delay = dateDiff(attach_date, first_review_date)
                            review_duration = dateDiff(attach_date, last_review_date)
                        else:
                            response_delay = -1
                            review_duration = -1
                        # feedback delay
                        if first_feedback_date:
                            feedback_delay = dateDiff(attach_date, first_feedback_date)
                        else:
                            feedback_delay = -1
                        print feedback_delay
                        print '-'*30
        if total_patches:
            obsolete_patch_rate = round(obsolete_cnt/total_patches, 2)
        else:
            obsolete_patch_rate = round(0, 2)
        