library(ggplot2)

dev.new(height=6, width=18)
							
df = read.csv('uplift_dates.csv', header=TRUE, sep=',')
month_label = unique(df$Month)

# Shadow dataframe
shadow = data.frame(x.min=c(-0.3,2.1), x.max=c(1.9,25.3), y.min=c(0,0), y.max=c(250,250), Periods=c('Removed ','Selected '))

ggplot(data=df, aes(x=Delta, y=Number_of_uplifts, shape=Channel)) + 
	geom_line(size=0.5) + 
	scale_x_continuous(breaks=c(0:(length(month_label)-1)), label=month_label, expand=c(0,0.3)) +
	geom_point(size=5) + 
	scale_shape(solid = FALSE) +
	xlab('Time period') + ylab('Upliftd issues') +
	theme_bw() + 			# white background
	theme(plot.title=element_text(size = 25), text=element_text(size=22), axis.title=element_blank(), axis.text.x=element_text(size=19,angle=45,hjust=1), legend.position='top')  +
	geom_rect(data=shadow, mapping=aes(xmin=x.min, xmax=x.max, ymin=y.min, ymax=y.max, fill=Periods), alpha=0.2, inherit.aes=FALSE)
