
ggplot_tsx_survey <- function (d, col = "grey", line_col = "darkblue", title = "", 
          ylims = c(0, 2), xlims = NULL, trans = "identity", yrbreaks = 5, 
          lpi_breaks = 0.2) 
{
  df <- data.frame(years = as.numeric(as.character(rownames(d))), 
                   lpi = d$LPI_final, lwr = d$CI_low, upr = d$CI_high)
  if (is.null(xlims)) {
    xlims = c(min(df$years), max(df$years))
  }
  g <- ggplot2::ggplot(data = df, ggplot2::aes_string(x = "years", 
                                                      y = "lpi", group = 1))
  if (!is.null(d$CI_low)) {
    g <- g + ggplot2::geom_ribbon(data = df, ggplot2::aes_string(ymin = "lwr", 
                                                                 ymax = "upr", group = 1), alpha = 0.2, fill = col)
  }
  g <- g + ggplot2::geom_line(size = 0.8, col = line_col)
  g <- g + ggplot2::geom_hline(yintercept = 1, alpha = 0.8)
  g <- g + ggplot2::coord_cartesian(ylim = ylims, xlim = xlims) + 
    ggplot2::theme_bw() + theme(panel.grid.major = element_blank(), panel.grid.minor = element_blank())
  g <- g + ggplot2::theme(axis.title.x=element_blank(), text = ggplot2::element_text(size = 16), 
                          axis.text.x = ggplot2::element_text(size = 16, angle = 90, hjust = 1))
  g <- g + ggplot2::theme(text = ggplot2::element_text(size = 20), 
                          axis.text.y = ggplot2::element_text(size = 16, hjust = 1))
  g <- g + ggplot2::ggtitle(title)
  g <- g + ggplot2::ylab(paste("Index", REF_YEAR," = 1", sep=" "))
  g <- g + ggplot2::scale_y_continuous(trans = trans, breaks = seq(ylims[1], 
                                                                   ylims[2], lpi_breaks))
  g <- g + ggplot2::scale_x_continuous(breaks = seq(xlims[1], 
                                                    xlims[2], yrbreaks))
  
  print(g)
}