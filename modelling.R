
# load data into data frames
df.basic = as.data.frame(read.csv('independent_metrics/basic.csv'))
df.review = as.data.frame(read.csv('independent_metrics/review_metrics.csv'))
df.senti = as.data.frame(read.csv('independent_metrics/senti_metrics.csv'))
df.code = as.data.frame(read.csv('independent_metrics/src_code_metrics.csv'))
# merge data frames into one
df.merge = merge(df.basic, df.review, by='bug_id')
df.merge = merge(df.merge, df.senti, by='bug_id')
df.merge = merge(df.merge, df.code, by='bug_id')

xcol_vaclus = colnames(df.merge)[-1]
xcol_vaclus
#formula_varclus <- as.formula(paste('crash_inducing ~ ', paste(xcol_varclus, collapse= '+')))