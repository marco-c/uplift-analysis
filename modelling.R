library(cvTools)
library(ROSE)
library(rms)
library(e1071)
library(plyr)

# Adjust the cavas proportion
#dev.new(height=7,width=10)

# Indicate the step we are
step = 'nonlinear'

# load data into data frames
df.basic = as.data.frame(read.csv('independent_metrics/basic.csv'))
df.review = as.data.frame(read.csv('independent_metrics/review_metrics.csv'))
df.senti = as.data.frame(read.csv('independent_metrics/senti_metrics.csv'))
df.code = as.data.frame(read.csv('independent_metrics/src_code_metrics.csv'))
df.inducing = as.data.frame(read.csv('independent_metrics/bug_inducing.csv'))
# merge data frames into one
df.merge = merge(df.inducing, df.basic, by='bug_id')
df.merge = merge(df.merge, df.review, by='bug_id')
df.merge = merge(df.merge, df.senti, by='bug_id')
df.merge = merge(df.merge, df.code, by='bug_id')

nrow(df.merge)
head(df.merge)
str(df.merge)

# Numeric variables for correlation analysis (variables that are not on review coverage)
xcol_varclus = c(colnames(df.merge)[3:6], colnames(df.merge)[-1:-7])
formula_varclus <- as.formula(paste('error_inducing ~ ', paste(xcol_varclus, collapse= '+')))

# Variables (that survive from varclus) for redundancy analysis
formula_redun <- update(formula_varclus, ~. -manager_pos -owner_pos -feedback_delay -code_churn_last_3_releases
											-developer_familiarity_last_3_releases -changes_add -reviewer_familiarity_last_3_releases
											-maxnesting -cnt_func -outdegree -betweenness -page_rank -indegree -review_iterations
											-reviewers -non_author_voters -response_delay -comment_times)

# Variables survived from correlation and redundancy analysis
formula_spearman <- update(formula_redun, ~. -changes_del -reviewer_familiarity_overall)

formula_spearman

if(step == 'varclus') {
	vcobj = varclus(formula_varclus, data=df.merge, trans='abs')
	plot(vcobj, labels=xcol_varclus)
	thresh = 0.7
	abline(h = 1 - thresh, col='grey', lty=2)
} else if(step == 'redun') {
	redun_obj = redun(formula_redun, data=df.merge, nk=0)
	cat('Redundant variables:\n')
	cat(paste(redun_obj$Out, collapse=", "))
} else if(step == 'spearman') {
	spearman2_obj = spearman2(formula_spearman, data=df.merge, p=2)
	plot(spearman2_obj)
} else if(step == 'nonlinear') {
	print('modelling')
	fit <- lrm(error_inducing ~ 
					rcs(modules_num,5) + rcs(backout_num,3) + rcs(release_delta,0) + rcs(response_delta,0) + 
					rcs(developer_familiarity_overall,0) + rcs(code_churn_overall,0) + rcs(test_changes_size,3) +
					rcs(landing_delta,3) + rcs(blocks,3) + rcs(changes_size,0) + rcs(comments,3) +
					rcs(r.ed_patches,0) + rcs(comment_words,0) + rcs(reviewer_comment_rate,0) + rcs(neg_review_rate,0) +
					rcs(review_duration,3) + rcs(feedback_count,0) + rcs(overall,3) + rcs(owner_neg,0) + 
					rcs(manager_neg,0) + rcs(LOC,0) + rcs(avg_cyclomatic,3) + rcs(ratio_comment,0),
				data=df.merge, x=TRUE, y=TRUE)
	fit
}