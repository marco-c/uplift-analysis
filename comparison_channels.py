import pandas as pd
from comparison_acceptation import *

if __name__ == '__main__':
    for channels in [['beta', 'release'], ['aurora', 'beta'], ['aurora', 'release']]:
        # initialize variables
        metric_list = ['changes_size', 'code_churn_overall', 'avg_cyclomatic', 'closeness',
                'landing_delta', 'response_delta', 'release_delta', 'uplift_comment_length',
                'developer_familiarity_overall', 'reviewer_familiarity_overall',
                'comments']
        # load data
        df1 = loadData(channels[0])
        df2 = loadData(channels[1])
        # split data into different categories
        df1 = df1.loc[df1.uplift_accepted == True]
        df2 = df2.loc[df2.uplift_accepted == True]
        # statistical analyses
        result_list = statisticalAnalyses(df1, df2, metric_list)
        # output results
        df_res = pd.DataFrame(result_list, columns=['metric', channels[0], channels[1], 'p-value', 'effect_size'])
        print(channels)
        print(df_res)
        print('\n')
