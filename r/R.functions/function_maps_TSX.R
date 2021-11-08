######################################
#THE TSX MAP FUNCTION#################
######################################

create_maps<-function(df,map.df, onlydensity = FALSE, onlypoints=FALSE,ignore_extent=FALSE,
                      title)
{
 
  #first define your title
  if (missing(title)){
    your_title<-""
  }else{
    your_title<-ifelse(title == "species_from_list",as.character(df$CommonName[[1]]),title) 
  }
  
  if (onlypoints==TRUE)
  {
    #plot to display only distribution of sampling points
    onlypoints<-ggplot(df, aes(x=SurveysCentroidLongitude, y=SurveysCentroidLatitude)) +
      geom_point(size = 2, colour = "red")+ 
      theme_classic()+
      labs(colour='Number of surveys',face = "bold")+
      theme(axis.line=element_blank(),
            axis.text.x=element_blank(),
            axis.ticks.x=element_blank(),
            axis.text.y=element_blank(),
            axis.ticks.y = element_blank(),
            plot.title = element_text(hjust = 0.5))+
      labs(x = "",
           y = "", size=14)+
      geom_path(data=map.df,aes(x=long, y=lat,group=group), colour="black")+
      ggtitle(your_title)

      return(onlypoints)
  }
  
  if (onlydensity ==TRUE){
    a<-ggplot(df, aes(x=SurveysCentroidLongitude, y=SurveysCentroidLatitude)) +
      stat_density2d(aes(fill = ..level..), alpha=0.5, h =0.5, geom="polygon", bins = 1500)
    ab <- ggplot_build(a)
    ab<-as.data.frame(ab$data)
    if(nrow(ab)>0){
      if(ignore_extent==TRUE){
        onlydensity<- ggplot(df, aes(x=SurveysCentroidLongitude, y=SurveysCentroidLatitude)) +
          geom_hex(binwidth = 0.5,aes(fill = stat(log(count)))) 
        gb <- ggplot_build(onlydensity)
        gb<-as.data.frame(gb$data)
        colfunc <- colorRampPalette(c("#5ce4ff","#5c64ff","#64068a","#d11586"))
        onlydensity<- onlydensity+ 
          scale_fill_gradientn(colours=colfunc(3),breaks= c(min(log(gb$count)),(max(log(gb$count))+max(log(gb$count)))/2,max(log(gb$count))),
                               labels=c("Low","", "High"),
                               limits=c(min(log(gb$count)),max(log(gb$count))))+
          coord_fixed()+
          labs(fill='Sampling intensity',face = "bold")+
          theme_classic()+
          labs(colour='Number of surveys',face = "bold")+
          theme(axis.line=element_blank(),
                axis.text.x=element_blank(),
                axis.ticks.x=element_blank(),
                axis.text.y=element_blank(),
                axis.ticks.y = element_blank(),
                plot.title = element_text(hjust = 0.5))+
          labs(x = "",
               y = "", size=14)+
          geom_path(data=map.df,aes(x=long, y=lat,group=group), colour="black")+
          ggtitle(your_title)
        return(onlydensity)
      }else{
      if(max(df$SurveysCentroidLatitude)-min(df$SurveysCentroidLatitude) < 14 & 
         max(df$SurveysCentroidLongitude)-min(df$SurveysCentroidLongitude) < 14)
      {
        a<-ggplot(df, aes(x=SurveysCentroidLongitude, y=SurveysCentroidLatitude)) +
          stat_density2d(aes(fill = ..level..), alpha=0.5, h =0.5, geom="polygon", bins = 100)
        ab <- ggplot_build(a)
        ab<-as.data.frame(ab$data)
        colfunc <- colorRampPalette(c("#5ce4ff","#5c64ff","#64068a","#d11586"))
        onlydensity<-a+
          scale_fill_gradientn(colours=colfunc(5),breaks=quantile(ab$level),
                               labels=c("Low","","","", "High"),
                               limits=c(min(ab$level),max(ab$level)))+
          xlim(min(df$SurveysCentroidLongitude) - 1.5,max(df$SurveysCentroidLongitude)+1.5) +
          ylim(min(df$SurveysCentroidLatitude)-1.5,max(df$SurveysCentroidLatitude)+1.5)+
          coord_fixed()+
          labs(fill='Sampling intensity',face = "bold")+
          theme_classic()+
          labs(colour='Number of surveys',face = "bold")+
          theme(
            plot.title = element_text(hjust = 0.5),
            legend.position = "none",
            panel.border = element_rect(colour = "black", fill=NA, size=3))+
          labs(x = "",
               y = "", size=14)+
          geom_path(data=map.df,aes(x=long, y=lat,group=group), colour="black")+
          ggtitle(your_title)
        return(onlydensity)
      }else{
        onlydensity<- ggplot(df, aes(x=SurveysCentroidLongitude, y=SurveysCentroidLatitude)) +
          geom_hex(binwidth = 0.5,aes(fill = stat(log(count)))) 
        gb <- ggplot_build(onlydensity)
        gb<-as.data.frame(gb$data)
        colfunc <- colorRampPalette(c("#5ce4ff","#5c64ff","#64068a","#d11586"))
        onlydensity<- onlydensity+ 
          scale_fill_gradientn(colours=colfunc(3),breaks= c(min(log(gb$count)),(max(log(gb$count))+max(log(gb$count)))/2,max(log(gb$count))),
                               labels=c("Low","", "High"),
                               limits=c(min(log(gb$count)),max(log(gb$count))))+
          coord_fixed()+
          labs(fill='Sampling intensity',face = "bold")+
          theme_classic()+
          labs(colour='Number of surveys',face = "bold")+
          theme(axis.line=element_blank(),
                axis.text.x=element_blank(),
                axis.ticks.x=element_blank(),
                axis.text.y=element_blank(),
                axis.ticks.y = element_blank(),
                plot.title = element_text(hjust = 0.5))+
          labs(x = "",
               y = "", size=14)+
          geom_path(data=map.df,aes(x=long, y=lat,group=group), colour="black")+
          ggtitle(your_title)
        return(onlydensity)
      }
      }
      }else{
        #plot to display only distribution of sampling points
        onlypoints<-ggplot(df, aes(x=SurveysCentroidLongitude, y=SurveysCentroidLatitude)) +
          geom_point(size = 3, colour = "#b0008d")+ 
          theme_classic()+
          labs(colour='Number of surveys',face = "bold")+
          theme(axis.line=element_blank(),
                axis.text.x=element_blank(),
                axis.ticks.x=element_blank(),
                axis.text.y=element_blank(),
                axis.ticks.y = element_blank(),
                plot.title = element_text(hjust = 0.5))+
          labs(x = "",
               y = "", size=14)+
          geom_path(data=map.df,aes(x=long, y=lat,group=group), colour="black")+
          ggtitle(your_title)
        return(onlypoints)
      }
  }
  
    if(onlydensity==FALSE & onlypoints==FALSE)
    {
      a<-ggplot(df, aes(x=SurveysCentroidLongitude, y=SurveysCentroidLatitude)) +
        stat_density2d(aes(fill = ..level..), alpha=0.5, h =0.5, geom="polygon", bins = 1500)
      ab <- ggplot_build(a)
      ab<-as.data.frame(ab$data)
      colfunc <- colorRampPalette(c("#34ebeb","#3440eb","#ba34eb","#b0008d"))
        if(nrow(ab)>0){
          if(max(df$SurveysCentroidLatitude)-min(df$SurveysCentroidLatitude) < 14 & 
             max(df$SurveysCentroidLongitude)-min(df$SurveysCentroidLongitude) < 14)
          {
            #density estimates
            a<-ggplot(df, aes(x=SurveysCentroidLongitude, y=SurveysCentroidLatitude)) +
              stat_density2d(aes(fill = ..level..), alpha=0.5, h =0.5, geom="polygon", bins = 500)
            ab <- ggplot_build(a)
            ab<-as.data.frame(ab$data)
            b<- a+
              scale_fill_gradientn(colours=colfunc(5),breaks=quantile(ab$level),
                                   labels=c("Low","","","", "High"),
                                   limits=c(min(ab$level),max(ab$level)))+
              xlim(min(df$SurveysCentroidLongitude) - 1.5,max(df$SurveysCentroidLongitude)+1.5) +
              ylim(min(df$SurveysCentroidLatitude)-1.5,max(df$SurveysCentroidLatitude)+1.5)+
              coord_fixed()+
              labs(fill='Sampling intensity',face = "bold")+
              theme_classic()+
              labs(colour='Number of surveys',face = "bold")+
              theme(
                plot.title = element_text(hjust = 0.5),
                legend.position = "none",
                panel.border = element_rect(colour = "black", fill=NA, size=3))+
              labs(x = "",
                   y = "", size=14)+
              geom_path(data=map.df,aes(x=long, y=lat,group=group), colour="black")+
              ggtitle(your_title)
            c<-  ggplot(df, aes(x=SurveysCentroidLongitude, y=SurveysCentroidLatitude)) +
              geom_point(size = 2, colour = "red")+
              xlim(min(map.df$long),max(map.df$long)) +
              ylim(min(map.df$lat),max(map.df$lat))+
              theme_classic()+
              labs(colour='Number of surveys',face = "bold")+
              theme(axis.line=element_blank(),
                    axis.text.x=element_blank(),
                    axis.ticks.x=element_blank(),
                    axis.text.y=element_blank(),
                    axis.ticks.y = element_blank(),
                    plot.title = element_text(hjust = 0.5),
                    legend.position = "none")+
              labs(x = "",
                   y = "", size=14)+
              geom_path(data=map.df,aes(x=long, y=lat,group=group), colour="black")
            
            forlegend<- a+
              scale_alpha_continuous(limits=c(0,10))+
              scale_fill_gradientn(colours=colfunc(5),breaks=quantile(ab$level),
                                   labels=c("Low","","","", "High"),
                                   limits=c(min(ab$level),max(ab$level)))+
              xlim(min(df$SurveysCentroidLongitude) - 0.5,max(df$SurveysCentroidLongitude)+0.5) +
              ylim(min(df$SurveysCentroidLatitude)-0.5,max(df$SurveysCentroidLatitude)+0.5)+
              coord_fixed()+
              labs(fill='Sampling intensity',face = "bold")
            
            get_legend<-function(myggplot){
              tmp <- ggplot_gtable(ggplot_build(myggplot))
              leg <- which(sapply(tmp$grobs, function(x) x$name) == "guide-box")
              legend <- tmp$grobs[[leg]]
              return(legend)
            }
            legend <- get_legend(forlegend)
            
            g<- arrangeGrob(b,legend,c, ncol=4, nrow = 2,
                             layout_matrix = rbind(c(NA,1,1,NA),c(NA,3,2,NA)),
                             widths = c(1,1,1,0.5),
                             heights=c(2,1))
          return(g)
          }else{
            onlydensity<- ggplot(df, aes(x=SurveysCentroidLongitude, y=SurveysCentroidLatitude)) +
              geom_hex(binwidth = 0.5,aes(fill = stat(log(count)))) 
            gb <- ggplot_build(onlydensity)
            gb<-as.data.frame(gb$data)
            colfunc <- colorRampPalette(c("#5ce4ff","#5c64ff","#64068a","#d11586"))
            onlydensity<- onlydensity+ 
              scale_fill_gradientn(colours=colfunc(3),breaks= c(min(log(gb$count)),(max(log(gb$count))+max(log(gb$count)))/2,max(log(gb$count))),
                                   labels=c("Low","", "High"),
                                   limits=c(min(log(gb$count)),max(log(gb$count))))+
              coord_fixed()+
              labs(fill='Sampling intensity',face = "bold")+
              theme_classic()+
              labs(colour='Number of surveys',face = "bold")+
              theme(axis.line=element_blank(),
                    axis.text.x=element_blank(),
                    axis.ticks.x=element_blank(),
                    axis.text.y=element_blank(),
                    axis.ticks.y = element_blank(),
                    plot.title = element_text(hjust = 0.5))+
              labs(x = "",
                   y = "", size=14)+
              geom_path(data=map.df,aes(x=long, y=lat,group=group), colour="black")+
              ggtitle(your_title)
            return(onlydensity)
          }
      }else{
        #plot to display only distribution of sampling points
        onlypoints<-ggplot(df, aes(x=SurveysCentroidLongitude, y=SurveysCentroidLatitude)) +
          geom_point(size = 3, colour = "#b0008d")+ 
          theme_classic()+
          labs(colour='Number of surveys',face = "bold")+
          theme(axis.line=element_blank(),
                axis.text.x=element_blank(),
                axis.ticks.x=element_blank(),
                axis.text.y=element_blank(),
                axis.ticks.y = element_blank(),
                plot.title = element_text(hjust = 0.5))+
          labs(x = "",
               y = "", size=14)+
          geom_path(data=map.df,aes(x=long, y=lat,group=group), colour="black")+
          ggtitle(your_title)
        return(onlypoints)
      }
    }
}
