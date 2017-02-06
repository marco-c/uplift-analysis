library(ggplot2)

dev.new(height=6, width=18)


							
df = read.csv('uplift_dates.csv', header=TRUE, sep=',')

# Shadow dataframe
shadow = data.frame(x.min=c(-0.3,2.1,24.1), x.max=c(1.9,23.9,27.2), y.min=c(0,0,0), y.max=c(250,250,250), Periods=c('Removed ','Selected ','Removed '))

ggplot(data=df, aes(x=Month, y=Number_of_uplifts, shape=Channel)) + 
	geom_line(size=0.5) + 
	scale_x_continuous(breaks=c(0:max(df$Month)), expand=c(0,0.3)) +
	geom_point(size=5) + 
	scale_shape(solid = FALSE) +
	xlab('Time period') + ylab('Upliftd issues') +
	ggtitle('Number of uplifted issues per month') +
	theme_bw() + 			# white background
	theme(plot.title=element_text(size = 25), text=element_text(size=22), axis.text.x=element_text(size=19), legend.position='top') +
	geom_rect(data=shadow, mapping=aes(xmin=x.min, xmax=x.max, ymin=y.min, ymax=y.max, fill=Periods), alpha=0.2, inherit.aes=FALSE)