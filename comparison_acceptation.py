import pandas as pd
from scipy import stats
from numpy import nanmedian
import rpy2.robjects as robjects
from rpy2.robjects.packages import importr

def bonferroniCorrection(p_value, num_tests):
    if p_value * num_tests < 1:
        return p_value * num_tests
    return 1

def effectSize(series1, series2, rcliff):
    list1 = robjects.FloatVector(list(series1))
    list2 = robjects.FloatVector(list(series2))
    effect_size = rcliff(list1, list2).rx('magnitude')[0].levels[0]
    return effect_size

def loadData(channel):
    df_basic = pd.read_csv('independent_metrics/basic_{}.csv'.format(channel))
    df_review = pd.read_csv('independent_metrics/review_metrics.csv')
    df_senti = pd.read_csv('independent_metrics/senti_metrics.csv')
    df_code = pd.read_csv('independent_metrics/src_code_metrics.csv')
    df = pd.merge(df_basic, df_review, on='bug_id')
    df = pd.merge(df, df_senti, on='bug_id')
    df = pd.merge(df, df_code, on='bug_id')
    return df

def statisticalAnalyses(df_sub1, df_sub2, metric_list):
    # import R packages
    effsize = importr('effsize')
    rcliff = robjects.r['cliff.delta']
    # list to save the results
    result_list = list()
    # Wilcoxon rank sum test & effect size
    num_tests = len(metric_list)
    for metric in metric_list:
        statistic,p_value = stats.mannwhitneyu(df_sub1[metric], df_sub2[metric])
        corrected_p = bonferroniCorrection(p_value, num_tests)
        effect_size = '--'
        if corrected_p < 0.05:
            effect_size = effectSize(df_sub1[metric], df_sub2[metric], rcliff)            
        sub1_median = nanmedian(df_sub1[metric])
        sub2_median = nanmedian(df_sub2[metric])
        result_list.append([metric, sub1_median, sub2_median, corrected_p, effect_size])
    return result_list

if __name__ == '__main__':
    for channel in ['aurora', 'beta', 'release']:
        # initialize variables
        metric_list = ['changes_size', 'code_churn_overall', 'avg_cyclomatic', 'closeness',
<<<<<<< HEAD
                'developer_familiarity_overall', 'reviewer_familiarity_overall',
                'reviewer_cnt', 'comments',
                'landing_delta', 'response_delta', 'release_delta']
=======
                'landing_delta', 'response_delta', 'release_delta',
                'developer_familiarity_overall', 'reviewer_familiarity_overall',
                'review_duration', 'comments']
>>>>>>> bd29caab2451dc5ca9542e13c9f5c3d374a23216
        # load data
        df = loadData(channel)
        # split data into different categories
        df_accept = df.loc[df.uplift_accepted == True]
        df_reject = df.loc[df.uplift_accepted == False]
        # statistical analyses
        result_list = statisticalAnalyses(df_accept, df_reject, metric_list)
        # output results
        df_res = pd.DataFrame(result_list, columns=['metric', 'accepted', 'rejected', 'p-value', 'effect_size'])
        print(channel.upper())
        print(df_res)
        print('\n')
