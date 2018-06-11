library('beanplot')

dev.new(height=10,width=6.2)

df.sub1 = as.data.frame(read.csv('plot_severity_1.csv', check.names=FALSE))
df.sub2 = as.data.frame(read.csv('plot_severity_2.csv', check.names=FALSE))

head(df.sub1)

removeOutlier <- function(x) {
	return (x[!x %in% boxplot.stats(x)$out])
}


for (metric in colnames(df.sub1)) {
	df1 = removeOutlier(df.sub1[[metric]])
	df2 = removeOutlier(df.sub2[[metric]])
	#beanplot(df1, df2, side='both', bw="nrd0", col=list('black', c('grey', 'white')))
	boxplot(list(unlist(df.sub1[metric]), unlist(df.sub2[metric])), outline=FALSE, names=c('more severe', 'others'), col=c('grey', 'white'), cex.axis=2)
	title(main=metric, line=0.5, cex.main=2)
}