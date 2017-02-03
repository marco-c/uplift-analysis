
# Adjust the cavas proportion
dev.new(height=15,width=15)


# load data into data frames
df.basic = as.data.frame(read.csv('independent_metrics/basic_aurora.csv'))
df.review = as.data.frame(read.csv('independent_metrics/review_metrics.csv'))
df.senti = as.data.frame(read.csv('independent_metrics/senti_metrics.csv'))
df.code = as.data.frame(read.csv('independent_metrics/src_code_metrics.csv'))
df.inducing = as.data.frame(read.csv('independent_metrics/bug_inducing.csv'))
# merge data frames into one
df = merge(df.inducing, df.basic, by='bug_id')
df = merge(df, df.review, by='bug_id')
df = merge(df, df.senti, by='bug_id')
df = merge(df, df.code, by='bug_id')

nrow(df)
#head(df)

xcol_varclus = c('changes_size', 'code_churn_overall', 'avg_cyclomatic', 'closeness',
            'landing_delta', 'response_delta', 'release_delta', 'uplift_comment_length',
            'developer_familiarity_overall', 'reviewer_familiarity_overall', 
            'reviewers', 'comments')
formula = as.formula(paste('error_inducing ~ ', paste(xcol_varclus, collapse= '+')))

formula

library(party)
fit = ctree(formula, data=df)
plot(fit, 
	title='the plot', 
	type='simple', 
	inner_panel=node_inner(fit, id = FALSE), 
	terminal_panel=node_terminal(fit, digits=2, id=FALSE))
