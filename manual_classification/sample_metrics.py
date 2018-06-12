import csv
import pandas as pd
from numpy import nanmedian
from scipy import stats

metric_names = {
    'changes_size': 'Code churn',
    'test_changes_size': 'Test churn',
    'code_churn_overall': 'Prior changes',
    'LOC': 'LOC',
    'avg_cyclomatic': 'Average cyclomatic',
    'cnt_func': 'Number of functions',
    'maxnesting': 'Maximum nesting',
    'ratio_comment': 'Comment ratio',
    'modules_num': 'Module number',
    'page_rank': 'PageRank',
    'betweenness': 'Betweenness',
    'closeness': 'Closeness',
    'developer_familiarity_overall': 'Developer exp.',
    'reviewer_familiarity_overall': 'Reviewer exp.',
    'comments': 'Number of comments',
    'comment_words': 'Comment words',
    'review_duration': 'Review duration',
    'min_neg': 'Developer sentiment',
    'owner_neg': 'Owner sentiment',
    'landing_delta': 'Landing delta',
    'response_delta': 'Response delta',
    'release_delta': 'Release delta',
}

def loadMetrics():
    with open('../metric_list.txt') as f:
        return [line.rstrip('\n') for line in f]
    
def loadData():
    df_aurora = pd.read_csv('../independent_metrics/basic_aurora.csv')
    df_beta = pd.read_csv('../independent_metrics/basic_beta.csv')
    df_release = pd.read_csv('../independent_metrics/basic_release.csv')
    df_review = pd.read_csv('../independent_metrics/review_metrics.csv')
    df_src = pd.read_csv('../independent_metrics/src_code_metrics.csv')
    df_senti = pd.read_csv('../independent_metrics/senti_metrics.csv')
#    df_basic = pd.concat([df_aurora, df_beta, df_release]).drop_duplicates()
    df_basic = df_beta
    df = pd.merge(df_basic, df_review, on='bug_id')
    df = pd.merge(df, df_senti, on='bug_id')
    df = pd.merge(df, df_src, on='bug_id')
    # Convert deltas from seconds to days.
    df.landing_delta = df.landing_delta / 86400
    df.response_delta = df.response_delta / 86400
    df.release_delta = df.release_delta / 86400
    # Ignore uplifts in the 'Pocket' component.
    df = df[df.component != 'Pocket']
    return df

def subCategories(df, df_input, tag, value):
    df = pd.merge(df_input, df, on='bug_id')
    df_sub1 = df[df[tag] == value]
    df_sub2 = df[df[tag] != value]
    return df_sub1, df_sub2

def bonferroniCorrection(p_value, num_tests):
    if p_value * num_tests < 1:
        return p_value * num_tests
    return 1

def outputResults(df_sub1, df_sub2, cat1):
    output_list = list()
    for metric in metric_list:
        sub1_median = nanmedian(df_sub1[metric])
        sub2_median = nanmedian(df_sub2[metric])
        
        statistic,p_value = stats.mannwhitneyu(df_sub1[metric], df_sub2[metric])
        corrected_p = bonferroniCorrection(p_value, 22)
        
        output_list.append([metric_names[metric], sub1_median, sub2_median, corrected_p])
        
    print pd.DataFrame(output_list, columns=['metric', cat1, 'others', 'p-value']).round(2)
    return


df = loadData()
metric_list = loadMetrics()

# more severe vs. others
df_input = pd.read_csv('severity_beta.csv')
df_input = df_input[df_input['Severity'].notnull()]
df_input.rename(columns={'Uplift ID':'bug_id'}, inplace=True)
df_sub1, df_sub2 = subCategories(df, df_input, 'Severity', 'R')
df_sub1[metric_list].rename(columns=metric_names).to_csv('plot_severity_1.csv', index=False)
df_sub2[metric_list].rename(columns=metric_names).to_csv('plot_severity_2.csv', index=False)


# easily preventable vs. others
df_beta = pd.read_csv('regressions_shipped_to_users_beta_clean.csv')
easily_preventable_beta1 = df_beta[
    (df_beta[u'how_found'] == 'found on a widely used feature/website/config') &
    ((df_beta[u'reproducible'] == 'reproducible') | (df_beta[u'reproducible'] == 'reproducible (but not by everyone)'))
] 
easily_preventable_beta2 = df_beta[
    (df_beta[u'how_found'] == 'found via telemetry') &
    ((df_beta[u'reproducible'] == 'not reproducible') | (df_beta[u'reproducible'] == 'not reproducible (except by reporter)'))
]

df_input = pd.concat([easily_preventable_beta1,easily_preventable_beta2])
df_input.rename(columns={'uplift_id':'bug_id'}, inplace=True)
df_sub1, df_sub2 = subCategories(df, df_input, 'reproducible', 'reproducible')

# partially fixed vs. others
def partiallyFixed(filename):
    partially_fixed_bugs = set()
    with open('reoccurrence/%s' %filename) as f:
        reader = csv.reader(f)
        for row in reader:
            if 'partially fixed' in row[-2]:
                partially_fixed_bugs.add(int(row[0]))
    return partially_fixed_bugs
partially_fixed_bugs = partiallyFixed('additionally_uplifted_with_channels.csv')
partially_fixed_bugs |= partiallyFixed('bm25_opened_after_with_channels.csv')
partially_fixed_bugs |= partiallyFixed('bm25_resolved_after_with_channels.csv')
partially_fixed_bugs |= partiallyFixed('cloned_with_channels.csv')
partially_fixed_bugs |= partiallyFixed('reopened_with_channels.csv')

df_sub1 = df[df['bug_id'].isin(partially_fixed_bugs)]
df_sub2 = df[~df['bug_id'].isin(partially_fixed_bugs)]

