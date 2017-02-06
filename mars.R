library(earth)
#library('plyr')
library('ROSE')

# select uplift_accepted or error_inducing
target = 'error_inducing'
channel = 'release'
doVIF = 'NO'

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


if (target == 'error_inducing'){
	df = df[df['uplift_accepted'] == 'True',]
}

xcol = c('changes_size', 'code_churn_overall', 'test_changes_size',
         'avg_cyclomatic', 'cnt_func', 'ratio_comment', 'page_rank', 'closeness', 'indegree', 'outdegree',
         'release_delta',
         'comments',
         'component',
         'developer_familiarity_overall', 'reviewer_familiarity_overall', 'reviewer_cnt',
         'min_neg', 'owner_neg'
         )
formula = as.formula(sprintf('%s ~ %s', target, paste(xcol, collapse= '+')))

# balance data between the target subset and the other category
df = ovun.sample(formula, data=df, p=0.5, seed=1, method='both')$data

#	VIF analysis
if(doVIF == 'YES') {
	library(car)
	fit = glm(formula, data=df, family=binomial())
	print(vif(fit) >= 5)
}


mars.model = earth(formula, data=df)
summary(mars.model)
evimp(mars.model)
