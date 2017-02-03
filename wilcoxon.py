from __future__ import division
import os
import pandas as pd
from scipy import stats
from numpy import nanmedian
# import rpy2
os.environ['R_HOME'] = '/Library/Frameworks/R.framework/Resources'
import rpy2.robjects as robjects
from rpy2.robjects.packages import importr

def bonferroniCorrection(p_value, num_tests):
    if p_value * num_tests < 1:
        return p_value * num_tests
    return 1

def effectSize(series1, series2):
    list1 = robjects.FloatVector(list(series1))
    list2 = robjects.FloatVector(list(series2))
    effect_size = rcliff(list1, list2).rx('magnitude')[0].levels[0]
    return effect_size

if __name__ == '__main__':
    channel = 'aurora'
    # import R packages
    effsize = importr('effsize')
    rcliff = robjects.r['cliff.delta']
    # initialize variables
    metric_list = ['changes_size', 'code_churn_overall', 'avg_cyclomatic', 'closeness',
            'landing_delta', 'response_delta', 'release_delta', 'uplift_comment_length',
            'developer_familiarity_overall', 'reviewer_familiarity_overall', 
            'reviewers', 'comments']
    num_tests = len(metric_list)
    # load data
    df_basic = pd.read_csv('independent_metrics/basic_{}.csv'.format(channel))
    df_review = pd.read_csv('independent_metrics/review_metrics.csv')
    df_senti = pd.read_csv('independent_metrics/senti_metrics.csv')
    df_code = pd.read_csv('independent_metrics/src_code_metrics.csv')
    df = pd.merge(df_basic, df_review, on='bug_id')
    df = pd.merge(df, df_senti, on='bug_id')
    df = pd.merge(df, df_code, on='bug_id')
    # split data into different categories
    df_accept = df.loc[df.uplift_accepted == True]
    df_reject = df.loc[df.uplift_accepted == False]
    # statistical analyses
    result_list = list()
    for metric in metric_list:
        statistic,p_value = stats.mannwhitneyu(df_accept[metric], df_reject[metric])
        corrected_p = bonferroniCorrection(p_value, num_tests)
        effect_size = 'NA'
        if corrected_p < 0.05:
            effect_size = effectSize(df_accept[metric], df_reject[metric])            
        accept_median = nanmedian(df_accept[metric])
        reject_median = nanmedian(df_reject[metric])
        result_list.append([metric, accept_median, reject_median, corrected_p, effect_size])
    # output results
    df_res = pd.DataFrame(result_list, columns=['metric', 'accpeted', 'rejected', 'p-value', 'effect_size'])
    print channel
    print df_res
