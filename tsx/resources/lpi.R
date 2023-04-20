library(rlpi)

## Usage: lpi.R input_file work_dir [refYear] [plotMax]

args <- commandArgs(TRUE)

inputFile <- args[1]
workDir <- args[2]

setwd(workDir)

data <- read.csv(inputFile, na.strings = "", quote = "\"",sep = ",")

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
