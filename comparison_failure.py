import pandas as pd
from comparison_acceptation import *

if __name__ == '__main__':
    channel = 'release'
    # import R packages
    effsize = importr('effsize')
    rcliff = robjects.r['cliff.delta']
    # initialize variables
    metric_list = ['changes_size', 'code_churn_overall', 'avg_cyclomatic', 'closeness',
            'landing_delta', 'response_delta', 'release_delta', 'uplift_comment_length',
            'developer_familiarity_overall', 'reviewer_familiarity_overall', 
            'reviewers', 'comments']
    # load data
    df_failure = pd.read_csv('independent_metrics/bug_inducing.csv')
    df = pd.merge(loadData(channel), df_failure, on='bug_id')
    # split data into different categories
    df_fault = df.loc[df.error_inducing == True]
    df_clean = df.loc[df.error_inducing == False]
    # statistical analyses
    result_list = statisticalAnalyses(df_fault, df_clean, metric_list)
    # output results
    df_res = pd.DataFrame(result_list, columns=['metric', 'fault', 'clean', 'p-value', 'effect_size'])
    print channel
    print df_res
    