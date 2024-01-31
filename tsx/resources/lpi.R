library(rlpi)
library(dplyr)
library(tidyr)

## Usage: lpi.R input_file work_dir [refYear] [plotMax]

args <- commandArgs(TRUE)

inputFile <- args[1]
workDir <- args[2]

setwd(workDir)

data <- read.csv(inputFile, na.strings = "", quote = "\"",sep = ",")

# If this is a single-species trend, treat each time series as a separate
# species in order to generate confidence intervals based on variations in
# population trends
nSpecies <- nrow(unique(data['Binomial']))
if(nSpecies == 1) {
  data$Binomial <- paste(data$Binomial, rownames(data), sep = "_")
}

yearCols <- grep("X[0-9]+", colnames(data), value=TRUE)
years <- strtoi(substr(yearCols, 2, 5))

refYear <- ifelse(is.na(args[3]), min(years), strtoi(args[3]))
plotMax <- ifelse(is.na(args[4]), max(years), strtoi(args[4]))

infile_name <- create_infile(data, name='data', start_col_name=min(yearCols), end_col_name=max(yearCols))

nesp_lpi<-LPIMain(
  infile_name,
  REF_YEAR=refYear,
  PLOT_MAX=plotMax - 1, # Note: this is because rlpi adds an extra year for some reason
  BOOT_STRAP_SIZE=1000,
  VERBOSE=TRUE,
  goParallel=FALSE,
  title="Title",
  plot_lpi=0,
  save_plots=0)

# Extra processing to add number of species for each year

outputData <- read.table('data_infile_Results.txt', header=TRUE)

if(nSpecies == 1) {
  outputData$numSpecies = 1
} else {
  lpi <- read.csv("lpi.csv", header=TRUE)
  n <- names(lpi)
  yearCols <-  n[startsWith(n, "X")]

  speciesPerYear <- lpi %>%
    select(Binomial, ID, all_of(yearCols)) %>%
    pivot_longer(all_of(yearCols)) %>% mutate(value2 = value) %>%
    group_by(ID) %>%
    fill(value, .direction = 'down') %>%
    fill(value2, .direction='up') %>%
    filter(!is.na(value) & !is.na(value2)) %>%
    ungroup() %>%
    mutate(year = as.numeric(substring(name, 2)), Binomial, .keep="none") %>%
    group_by(year) %>%
    summarise(numSpecies = n_distinct(Binomial))

  outputData <- outputData %>%
    tibble::rownames_to_column('year') %>%
    mutate(year = as.numeric(year)) %>%
    left_join(speciesPerYear, by='year') %>%
    tibble::column_to_rownames('year')
}

write.table(outputData, 'data_infile_Results.txt', col.names=TRUE)
