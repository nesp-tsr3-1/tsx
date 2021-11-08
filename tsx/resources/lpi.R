library(rlpi)

## Usage: lpi.R input_file work_dir

args <- commandArgs(TRUE)

inputFile <- args[1]
workDir <- args[2]

setwd(workDir)

data <- read.csv(inputFile, na.strings = "", quote = "\"",sep = ",")

yearCols <- grep("X[0-9]+", colnames(data), value=TRUE)
years <- strtoi(substr(yearCols, 2, 5))

infile_name <- create_infile(data, name='data', start_col_name=min(yearCols), end_col_name=max(yearCols))

nesp_lpi<-LPIMain(
  infile_name,
  REF_YEAR=min(years),
  PLOT_MAX=max(years),
  BOOT_STRAP_SIZE=1000,
  VERBOSE=TRUE,
  goParallel=FALSE,
  title="Title",
  plot_lpi=0,
  save_plots=0)
