from __future__ import division
import os
import pandas as pd
from scipy import stats
from numpy import nanmedian
#os.environ['R_HOME'] = '/Library/Frameworks/R.framework/Resources'
#import rpy2.robjects as robjects
#from rpy2.robjects.packages import importr
#from numpy import median

def bonferroniCorrection(p_value, num_tests):
    if p_value * num_tests < 1:
        return p_value * num_tests
    return 1

if __name__ == '__main__':
    # initialisation
#    effsize = importr('effsize')
#    rwilcox = robjects.r['wilcox.test']
#    rcliff = robjects.r['cliff.delta']
    
    channel = 'beta'
    
    metric_list = ['changes_size', 'code_churn_overall', 'avg_cyclomatic', 'closeness',
            'landing_delta', 'response_delta', 'release_delta', 'uplift_comment_length',
            'developer_familiarity_overall', 'reviewer_familiarity_overall', 
            'reviewers', 'comments']
    num_tests = len(metric_list)
    
    df_basic = pd.read_csv('independent_metrics/basic_{}.csv'.format(channel))
    df_review = pd.read_csv('independent_metrics/review_metrics.csv')
    df_senti = pd.read_csv('independent_metrics/senti_metrics.csv')
    df_code = pd.read_csv('independent_metrics/src_code_metrics.csv')
    df = pd.merge(df_basic, df_review, on='bug_id')
    df = pd.merge(df, df_senti, on='bug_id')
    df = pd.merge(df, df_code, on='bug_id')
    
    df_accept = df.loc[df.uplift_accepted == True]
    df_reject = df.loc[df.uplift_accepted == False]
    
    result_list = list()
    for metric in metric_list:
        statistic,p_value = stats.mannwhitneyu(df_accept[metric], df_reject[metric])
        corrected_p = bonferroniCorrection(p_value, num_tests)
        accept_median = nanmedian(df_accept[metric])
        reject_median = nanmedian(df_reject[metric])
        result_list.append([metric, accept_median, reject_median, corrected_p])
    df_res = pd.DataFrame(result_list, columns=['metric', 'accepted', 'rejected', 'p-value'])
    print channel
    print df_res
