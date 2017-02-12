library(earth)
library('plyr')
library('ROSE')

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
# only take uplifted issues into account
df = df[df['uplift_accepted'] == 'True',]

df <- rename(df, c('min_neg_senti'='developer_sentiment','owner_neg_senti'='owner_sentiment'))

xcol = scan(sprintf('vif/%s_metric_list.txt', channel), what='', sep='\n')
formula = as.formula(sprintf('error_inducing ~ %s', paste(xcol, collapse= '+')))

#	VIF analysis
if(doVIF == 'YES') {
	library(car)
	fit = glm(formula, data=df, family=binomial())
	vfit = vif(fit)
	if(is.vector(vfit)) {
		print (vfit >= 5)
	} else {
		print (vfit[,3] >= sqrt(5))
	}
	# remove correlated variables
	formula.reduced = update(formula, ~. -developer_familiarity_last_3_releases -reviewer_familiarity_last_3_releases
										-reviewer_familiarity_overall -developer_familiarity_overall -component)
	fit.new = glm(formula.reduced, data=df, family=binomial())
	vfit.new = vif(fit.new)
	print ('Check VIF again')
	if(is.vector(vfit.new)) {
		print (vfit.new >= 5)
	} else {
		print (vfit.new[,3] >= sqrt(5))
	}
} else {
	# balance data between the target subset and the other category
	df = ovun.sample(formula, data=df, p=0.5, seed=1, method='both')$data
	# model building
	mars.model = earth(formula, data=df)
	print(summary(mars.model))
	print(evimp(mars.model))
}
