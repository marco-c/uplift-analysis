library(cvTools)
library(ROSE)
library(randomForest)	

# Adjust the cavas proportion
#dev.new(height=7,width=10)

# Indicate the channel to analyze
channel = 'aurora'

tree_number = 100

# Set random seed
set.seed(99)

# load data into data frames
df.basic = as.data.frame(read.csv(sprintf('independent_metrics/basic_%s.csv', channel)))
df.review = as.data.frame(read.csv('independent_metrics/review_metrics.csv'))
df.senti = as.data.frame(read.csv('independent_metrics/senti_metrics.csv'))
df.code = as.data.frame(read.csv('independent_metrics/src_code_metrics.csv'))
df.inducing = as.data.frame(read.csv('independent_metrics/bug_inducing.csv'))
# merge data frames into one
df.merge = merge(df.inducing, df.basic, by='bug_id')
df.merge = merge(df.merge, df.review, by='bug_id')
df.merge = merge(df.merge, df.senti, by='bug_id')
#df.merge = merge(df.merge, df.code, by='bug_id')

df = df.merge

head(df)
nrow(df)

xcol = c(colnames(df)[3:6], colnames(df)[-1:-7])
formula <- as.formula(paste('error_inducing ~ ', paste(xcol, collapse= '+')))
formula = update(formula, ~. -bug_assignee -bug_creator -languages -patch_authors 
				-patch_reviewers -uplift_requestor -component)


# Separate data into k folds
k = 10
folds = cvFolds(nrow(df), K = k, type = 'random')

# Initialise result values
tp.sum = tn.sum = fp.sum = fn.sum <- 0
false.positives <- matrix(nrow=k, ncol=2, dimnames=list(c(),c('round', 'false_positive')))
false.negatives <- matrix(nrow=k, ncol=2, dimnames=list(c(),c('round', 'false_negatives')))

#	Iteratively run validation
for(i in 1:k) {
	print(sprintf('Round no. %d', i))
	#	Split training and testing data
	trainIndex <- folds$subsets[folds$which != i]	# Extract training index
	testIndex <- folds$subsets[folds$which == i]	# Extract testing index			
	trainset <- df[trainIndex, ] 		# Set the training set
  	testset <- df[testIndex, ] 			# Set the validation set
	#	Balance crash-inducing and crash-free data in the training set
	train.balanced <- ovun.sample(error_inducing~., data=trainset, p=0.5, seed=1, method='both')$data
	# feed data into the model
	fit <- randomForest(formula, data=train.balanced, ntree=tree_number, mtry=5, importance=TRUE)
  	testset[, 'predict'] <- predict(fit, newdata = testset)
#	varImpPlot(fit, cex = 1, main = '')
	
	# analyze prediction results
	t <- table(observed = testset[, 'error_inducing'], predicted = testset[, 'predict'])
	actualYES <- testset[testset['error_inducing'] == 'True', ]
	actualNO <- testset[testset['error_inducing'] == 'False', ]
	# calculate the confusion matrix
	tp <- nrow(actualYES[actualYES[,'predict'] == 'True',])
	tn <- nrow(actualNO[actualNO[, 'predict'] == 'False',])
	fp <- nrow(actualNO[actualNO[, 'predict'] == 'True',])
	fn <- nrow(actualYES[actualYES[,'predict'] == 'False',])
	tp.sum <- tp.sum + tp
	tn.sum <- tn.sum + tn
	fp.sum <- fp.sum + fp
	fn.sum <- fn.sum + fn	
	# extract false positives 
	fp.revision = actualNO[actualNO[, 'predict'] == 'YES',]$revision
	fp.str = paste(as.character(fp.revision), collapse = ' ')
	false.positives[i,] = c(i, fp.str)
	# extract false negatives
	fn.revision = actualYES[actualYES[,'predict'] == 'NO',]$revision
	fn.str = paste(as.character(fn.revision), collapse = ' ')
	false.negatives[i,] = c(i, fn.str)
	
	cat(sprintf('\tpre: %.3f\n', tp/(tp+fp)))
	cat(sprintf('\trec: %.3f\n',tp/(tp+fn)))
}

acc = (tn.sum+tp.sum) / (tn.sum+fp.sum+fn.sum+tp.sum)
pre = tp.sum/(tp.sum+fp.sum)
rec = tp.sum/(tp.sum+fn.sum)
fm = 2 * (pre * rec) / (pre + rec)
npre <- tn.sum/(tn.sum+fn.sum)
nrec <- tn.sum/(tn.sum+fp.sum)
nfm <- 2 * npre * nrec / (npre + nrec)

print(sprintf('accuracy: %.1f%%', acc * 100))
print(sprintf('error-inducing pre: %.1f%%', pre * 100))
print(sprintf('error-inducing rec: %.1f%%', rec * 100))
print(sprintf('error-inducing f-measure: %.1f%%', fm * 100))
print(sprintf('error-free pre: %.1f%%', npre * 100))
print(sprintf('error-free rec: %.1f%%', nrec * 100))
print(sprintf('error-free f-measure: %.1f%%', nfm * 100))


