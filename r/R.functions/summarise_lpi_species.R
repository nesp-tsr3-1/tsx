summarise_lpi_species <- function(infile) {
  require(data.table)
  require(tidyverse)
  # Bit of a hack to avoid NOTE during R CMD check
  # Sets the variables used in ggplot2::aes to NULL
  summarise <- Binomial <- year <- ID <- species <- pop <- duration <- nspecies <- minyear <- maxyear <- NULL

  FileTable = read.table(infile, header = TRUE)
  FileNames = FileTable$FileName
  Binomial= FileTable$Binomial
  Group = FileTable[2]
  NoFiles = max(dim(Group))

  for (FileNo in 1:NoFiles) {
    filename <- toString(FileNames[FileNo])
    Data = read.table(filename, header=TRUE)

    minpop_year = plyr::ddply(Data, c('Binomial', 'ID'), plyr::summarise, minyear = min(as.numeric(year)))
    maxpop_year = plyr::ddply(Data, c('Binomial', 'ID'), plyr::summarise, maxyear = max(as.numeric(year)))
    pop_range = merge(minpop_year, maxpop_year, by=c('Binomial', 'ID'))
    dt <- data.table(pop_range)
    counts <- dt[, list(year = seq(minyear, maxyear)), by = c("Binomial", "ID")]
    year = plyr::ddply(counts, c('year'), plyr::summarise, year = unique(year))
    npop = plyr::ddply(counts, c('year'), plyr::summarise, npop = length(unique(ID)))
    nsp = plyr::ddply(counts, c('year'), plyr::summarise, nsp = length(unique(Binomial)))
    final_count <- merge (npop, nsp,by = "year")
    final_count$filename <- filename

    outfile <- paste(infile, ".summary_sp.csv", sep="")
    write.table(final_count, file=outfile, sep=",", row.names=FALSE)

    return(final_count)
  }
}
