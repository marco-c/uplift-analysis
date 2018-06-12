library('beanplot')

dev.new(height=10,width=6.2)


removeOutlier <- function(x) {
	return (x[!x %in% boxplot.stats(x)$out])
}

drawPlot <- function(df.sub1, df.sub2, show.metrics, cat1) {
	for (metric in colnames(df.sub1)) {
		if (metric %in% show.metrics) { 
			boxplot(list(unlist(df.sub1[metric]), unlist(df.sub2[metric])), outline=FALSE, names=c(cat1, 'others'), col=c('grey', 'white'), cex.axis=2)
			title(main=metric, line=0.5, cex.main=2)
			#df1 = removeOutlier(df.sub1[[metric]])
			#df2 = removeOutlier(df.sub2[[metric]])
			#beanplot(df1, df2, side='both', bw="nrd0", col=list('black', c('grey', 'white')), main=metric)
		}
	}
}

# plots for severity
df.sub1 = as.data.frame(read.csv('plot_severity_1.csv', check.names=FALSE))
df.sub2 = as.data.frame(read.csv('plot_severity_2.csv', check.names=FALSE))
show.metrics = c('Release delta', 'Review duration', 'Comment words')
#drawPlot(df.sub1, df.sub2, show.metrics, 'more severe')


df.sub1 = as.data.frame(read.csv('plot_preventable_1.csv', check.names=FALSE))
df.sub2 = as.data.frame(read.csv('plot_preventable_2.csv', check.names=FALSE))
show.metrics = c('Landing delta', 'Release delta')
#drawPlot(df.sub1, df.sub2, show.metrics, 'preventable')

df.sub1 = as.data.frame(read.csv('plot_recurring_1.csv', check.names=FALSE))
df.sub2 = as.data.frame(read.csv('plot_recurring_2.csv', check.names=FALSE))
show.metrics = c('Code churn', 'Module number', 'Number of comments', 'Landing delta')
drawPlot(df.sub1, df.sub2, show.metrics, 'partially fixed')
