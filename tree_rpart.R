library('rpart.plot')
library('plyr')

target = 'uplift_accepted'
channel = 'release'
doVIF = 'YES'

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

xcol = c('changes_size', 'code_churn_overall', 
		'avg_cyclomatic', 'cnt_func', 'maxnesting', 'ratio_comment', 
		'page_rank', 'betweenness', 'closeness', 'indegree', 'outdegree',
        'landing_delta', 'response_delta', 'release_delta', 'uplift_comment_length',
        'reviewer_familiarity_overall', 'test_changes_size',
        'max_pos', 'min_neg', 'owner_pos', 'owner_neg', 'manager_pos', 'manager_neg', 
		'reviewers', 'comments', 'reviewer_comment_rate')
formula = as.formula(sprintf('%s ~ %s', target, paste(xcol, collapse= '+')))


#	VIF analysis
if(doVIF == 'YES') {
	library(car)
	vif.fit = glm(formula, data = df, family = binomial())
	print(vif(vif.fit) >= 5)
}


tree.fit = rpart(formula, data=df)
#node.fun3 <- function(x, labs, digits, varlen)
#{
#    paste(labs, "\n\ndev", x$frame$dev)
#}
#prp(tree.fit, extra=6, node.fun=node.fun3)
rpart.plot(tree.fit)