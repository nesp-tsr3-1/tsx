library(rlpi)
library(dplyr)
library(tidyr)

## Usage: lpi.R input_file work_dir [refYear] [plotMax] [--filter-rows] [--log-linear]

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

refYear <- ifelse(is.na(strtoi(args[3])), min(years), strtoi(args[3]))
plotMax <- ifelse(is.na(strtoi(args[4])), max(years), strtoi(args[4]))

# Always end plot where the available data ends
dataMaxYear <- data %>%
  select(all_of(yearCols)) %>%
  pivot_longer(all_of(yearCols)) %>%
  filter(!is.na(value)) %>%
  summarise(max(name)) %>%
  pull %>%
  substr(2,5) %>%
  strtoi

plotMax <- min(plotMax, dataMaxYear)

# Remove rows with all zeroes or only one value within range
filterRows <- any(args == '--filter-rows')
if(filterRows) {
  cat("Rows before filtering:", nrow(data), "\n")
  yearColsInRange <- yearCols[years >= refYear & years <= plotMax]
  data <- dplyr::filter(data, apply(!is.na(data[yearColsInRange]), 1, sum) > 1)
  data <- dplyr::filter(data, apply(data[yearColsInRange], 1, max, na.rm=TRUE) > 0)
  cat("Rows after filtering:", nrow(data), "\n")
  if(nrow(data) == 0) {
    stop("No data to process")
  }
}

logLinear <- any(args == '--log-linear')

infile_name <- create_infile(data, name='data', start_col_name=min(yearCols), end_col_name=max(yearCols))

nesp_lpi<-LPIMain(
  infile_name,
  REF_YEAR=refYear,
  PLOT_MAX=plotMax - 1, # Note: this is because rlpi adds an extra year for some reason
  BOOT_STRAP_SIZE=1000,
  GAM_GLOBAL_FLAG=ifelse(logLinear, 0, 1),
  VERBOSE=TRUE,
  goParallel=FALSE,
  title="Title",
  plot_lpi=0,
  save_plots=0)

# Extra processing to add number of species for each year

outputData <- read.table('data_infile_Results.txt', header=TRUE)

if(nSpecies == 1) {
  # Reset binomial for calculations below
  data$Binomial <- "Species"
}

speciesPerYear <- data %>%
  select(Binomial, ID, all_of(yearCols)) %>%
  pivot_longer(all_of(yearCols)) %>%
  mutate(value2 = value) %>%
  group_by(ID) %>%
  fill(value, .direction = 'down') %>%
  fill(value2, .direction='up') %>%
  filter(!is.na(value) & !is.na(value2)) %>%
  ungroup() %>%
  mutate(year = as.numeric(substring(name, 2)), Binomial, .keep="none") %>%
  group_by(year) %>%
  summarise(numSpecies = n_distinct(Binomial), numTimeSeries = n())

outputData <- outputData %>%
  tibble::rownames_to_column('year') %>%
  mutate(year = as.numeric(year)) %>%
  left_join(speciesPerYear, by='year') %>%
  tibble::column_to_rownames('year')

write.table(outputData, 'data_infile_Results.txt', col.names=TRUE)
