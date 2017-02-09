library(earth)
#library('plyr')
library('ROSE')

channel = 'aurora'

# load data into data frames
df.basic = as.data.frame(read.csv(sprintf('independent_metrics/basic_%s.csv', channel)))
df.review = as.data.frame(read.csv('independent_metrics/review_metrics.csv'))
df.senti = as.data.frame(read.csv('independent_metrics/senti_metrics.csv'))
df.code = as.data.frame(read.csv('independent_metrics/src_code_metrics.csv'))
df.inducing = as.data.frame(read.csv('independent_metrics/bug_inducing.csv'))
# merge data frames into one
df = merge(df.inducing, df.basic, by='bug_id')
df = merge(df, df.review, by='bug_id')
df = merge(df, df.senti, by='bug_id')
df = merge(df, df.code, by='bug_id')
# only take uplifted issues into account
df = df[df['uplift_accepted'] == 'True',]

colnames(df)

drawplot <- function(df, target, metric) {
	df.sub1 <- df[df[ ,target]=='True',]
	df.sub2 <- df[df[ ,target]=='False',]
	boxplot(list(unlist(df.sub1[metric]), unlist(df.sub2[metric])), outline=FALSE, names=c('Faulty', 'Clean'), main=metric)
}

metric_list = c('changes_size', 'test_changes_size', 'code_churn_overall',
	         'avg_cyclomatic', 'cnt_func', 'ratio_comment', 'closeness', 'betweenness',
	         'release_delta',
	         'comments',
	         'developer_familiarity_overall', 'reviewer_cnt', 'review_duration', 'reviewer_familiarity_overall',
	         'min_neg', 'owner_neg', 'manager_neg',
	         'LOC', 'maxnesting',
	         'comment_words', 'reviewer_comment_rate', 'non_author_voters', 'neg_review_rate',
	         'backout_num', 'blocks', 'depends_on', 'landing_delta', 'modules_num', 'r.ed_patches')
for(i in 1:length(metric_list)) {
	metric_name = metric_list[i]
	drawplot(df, 'error_inducing', metric_name)
}
