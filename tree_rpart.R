library('rpart.plot')
library('plyr')
library('ROSE')

channel = 'aurora'
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


xcol = scan(sprintf('metric_list.txt', channel), what='', sep=',')
formula = as.formula(sprintf('error_inducing ~ %s', paste(xcol, collapse= '+')))

# balance data between the target subset and the other category
df = ovun.sample(formula, data=df, p=0.5, seed=1, method='both')$data

#	VIF analysis
if(doVIF == 'YES') {
	library(car)
	fit = glm(formula, data=df, family=binomial())
	print(vif(fit) >= 5)
}

tree.fit = rpart(formula, data=df)
print(tree.fit)
printcp(tree.fit)
bestcp <- tree.fit$cptable[which.min(tree.fit$cptable[,"xerror"]),"CP"]
tree.pruned <- prune(tree.fit, cp = bestcp)

conf.matrix <- table(df$error_inducing, predict(tree.pruned,type="class"))
rownames(conf.matrix) <- paste("Actual", rownames(conf.matrix), sep = ":")
colnames(conf.matrix) <- paste("Pred", colnames(conf.matrix), sep = ":")
print(conf.matrix)

prp(tree.fit, extra=106, varlen=0, under=TRUE)
prp(tree.pruned, faclen = 0, cex = 0.8, extra = 1)

