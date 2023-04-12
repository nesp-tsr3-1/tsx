library(rlpi)
library(docopt)
#library(devtools)
#load_all('/home/uqebayra/rlpi')
####################################################################
## Collect arguments
args <- commandArgs(TRUE)
## Default setting when no arguments passed
if(length(args) != 12) {
  args <- c("--help")
}

original_wd <- getwd()

## Help section
if("--help" %in% args) {
  cat("
      The R Script
      Arguments:
      grouping
      state
      statusauth
      status
      management
      nationalpriority
      bootstrap
      referenceyear
      startyear
      plotmax
      input
      output
      --help
      ")
  q(save="no")
}
groupingArg <- args[1]
stateArg <- args[2]
statusAuthArg <- args[3]
statusArg <- args[4]
managementArg <- args[5]
nationalPriorityArg <- args[6]
bootstrapArg <- args[7]
referenceYearArg <- args[8]
startyearArg <- args[9]
plotMaxArg <- args[10]
inputArg <- args[11]
outputArg <- args[12]

####### values
in_file <- "lpi.csv"
taxonomicGroup <- NULL
groups <- NULL
subgroups <- NULL
states <- NULL
statusauth <- NULL
statuses <- NULL
management <- NULL
nationalpriority <- FALSE
bootstrap <- 1000
referenceyear <- 1970
plotmax <- 2019
output <- "output"
startyear <- "X1950"
endyear <- "X2019"
## using numbers or not
## lpi
if(!is.null(inputArg)){
  in_file <- inputArg
}
# output
if(!is.null(outputArg)){
  output <- outputArg
}
outdir <- output

groupingParts <- unlist(strsplit(groupingArg, ":", fixed=TRUE))
taxonomicGroupArg <- groupingParts[1]
groupArg <- groupingParts[2]
subGroupArg <- groupingParts[3]

# taxonomicGroup (e.g. Bird, Mammal, Plant)
if(!is.null(taxonomicGroupArg) && taxonomicGroupArg != "All"){
  outdir <- paste(outdir, "tgroup-", taxonomicGroupArg, "_", sep="")
  taxonomicGroup <- taxonomicGroupArg
}
# group (functional group e.g. Terrestrial, Marine)
if(!is.null(groupArg) && groupArg != "All"){
  outdir <- paste(outdir, "group-", groupArg, "_", sep="")
  groups <- unlist(strsplit(groupArg, "+", fixed=TRUE))
}
# subgroup
if(!is.null(subGroupArg) && subGroupArg != "All"){
  outdir <- paste(outdir, "subgroup-", subGroupArg, "_", sep="")
  subgroups <- unlist(strsplit(subGroupArg, "+", fixed=TRUE))
}
# state
if(!is.null(stateArg) && stateArg != "All"){
  outdir <- paste(outdir, "state-", stateArg, "_", sep="")
  states <- unlist(strsplit(stateArg, "+", fixed=TRUE))
}
# statusauth
if(!is.null(statusAuthArg) && statusAuthArg!= "All"){
  outdir <- paste(outdir, "statusauth-", statusAuthArg, "_", sep="")
  statusauth <- statusAuthArg
}
# status
if(!is.null(statusArg) && statusArg!= "All" ){
  outdir <- paste(outdir, "status-", statusArg, "_", sep="")
  statuses <- unlist(strsplit(statusArg, "+", fixed=TRUE))
}
# management
if(!is.null(managementArg) && managementArg!= "All sites"){
  outdir <- paste(outdir, "management-", managementArg, "_", sep="")
  management <- managementArg
}
# nationalpriority
if(nationalPriorityArg == "TRUE") {
  outdir <- paste(outdir, "priority-1_", sep="")
  nationalpriority <- TRUE
}
## bootstrap
if (!is.null(plotMaxArg)){
  bootstrap <- as.numeric(bootstrapArg)
}
#referenceyear
if (!is.null(referenceYearArg) ){
  referenceyear <- as.numeric(referenceYearArg)
}
#plotmax
if ( !is.null(plotMaxArg)){
  plotmax <- as.numeric(plotMaxArg)
  endyear <- paste("X", plotmax, sep = "")
}


if (file.exists(outdir)){
    setwd(outdir)
} else {
    dir.create(outdir, recursive = TRUE)
    setwd(outdir)
}

if ( !is.null(startyearArg)){
  startyear <- paste("X", as.numeric(startyearArg), sep = "")
}


#sprintf ("input='%s', bootstrap=%s, refenreceyear=%s, plotmax=%s",
#          in_file, bootstrap, referenceyear, plotmax)
# read the data
data <- read.csv(in_file, na.strings = "", quote = "\"",sep = ",")
## filter data

if(!is.null(taxonomicGroup)){
  data <- data[data$TaxonomicGroup == taxonomicGroup,]
  write("Filtering by taxonomic group", file="runoutput.txt", append=TRUE)
}

if(length(groups) > 0 | length(subgroups) > 0) {
  # Prepare a table which maps each time series ID to zero or more group/subgroups
  groups_per_row <- strsplit(as.character(data$FunctionalGroup), ",")
  groups_df <- data.frame(ID=rep(data$ID, times=lapply(groups_per_row, length)), FunctionalGroup=unlist(groups_per_row))
  groups_df$Group <- sapply(strsplit(as.character(groups_df$FunctionalGroup), ":"), "[", 1)
  groups_df$Subgroup <- sapply(strsplit(as.character(groups_df$FunctionalGroup), ":"), "[", 2)
}

if(length(groups) > 0){
#  data <- data[data$FunctionalGroup %in% groups,]
  data <- data[data$ID %in% groups_df[groups_df$Group %in% groups,]$ID,]
  write("Filtering by groups", file="runoutput.txt", append=TRUE)
  write(dim(data), file="runoutput.txt", append=TRUE)
}
if(length(subgroups) > 0){
#  data <- data[data$FunctionalSubGroup %in% subgroups,]
  data <- data[data$ID %in% groups_df[groups_df$Subgroup %in% subgroups,]$ID,]
  write("Filtering by subgroups", file="runoutput.txt", append=TRUE)
  write(dim(data), file="runoutput.txt", append=TRUE)
}
if(length(states) > 0){
  data <- data[data$State %in% states,]
  write("Filtering by states", file="runoutput.txt", append=TRUE)
  write(dim(data), file="runoutput.txt", append=TRUE)
}
statusauth_str <- paste(statusauth, "Status", sep="")
write(statusauth_str, file="runoutput.txt", append=TRUE)
write(statuses, file="runoutput.txt", append=TRUE)
write(length(statuses), file="runoutput.txt", append=TRUE)
if(length(statuses) > 0){
  data <- data[unlist(data[statusauth_str]) %in% statuses,]
  write("Filtering by status", file="runoutput.txt", append=TRUE)
  write(dim(data), file="runoutput.txt", append=TRUE)
}

if(!is.null(management)){
  data <- data[data$Management == management,]
}

if(nationalpriority) {
  data <- data[data$NationalPriorityTaxa==1,]
}

if(dim(data)[1] == 0){
  print ("Empty data. Quit")
  system(paste(original_wd, "/clean.sh \"", getwd(), "\"", sep=""))
  q(save = "no")
}

write.table(data, "lpi_input.csv", sep = ",")

taxonlist <- as.vector(data[['TaxonID']])
uniqueTaxonIDs <- unique(taxonlist)
write (paste("\nTaxonIDs:", uniqueTaxonIDs), file="runoutput.txt", append=TRUE)
if ( length(uniqueTaxonIDs) < 3 ) {
  print ("The number of taxa is less than 3. Quit!!!!")
  system(paste(original_wd, "/clean.sh \"", getwd(), "\"", sep=""))
  q(save="no")
}

start <- strtoi(substring(startyear, 2))
end <- strtoi(substring(endyear, 2))

ref_years <- c(referenceyear, referenceyear+5, referenceyear+10, referenceyear+15)
for (year in ref_years){
  # Check which time series have observations on or before reference year AND on or after reference year
  yearsBefore <- paste('X', start:year, sep="")
  yearsAfter <- paste('X', year:end, sep="")
  taxa = unique(data[!apply(is.na(data[yearsBefore]), 1, all) & !apply(is.na(data[yearsAfter]), 1, all), 'TaxonID'])
  if(length(taxa) < 3) {
    print(paste0("Skipping year due to insufficient data: ", year))
    next
  }

  yfname <- paste("nesp", year, sep="_")
  ytitle <- paste("lpi", year, sep="_")

  infile_name <- create_infile(data, name=yfname, start_col_name=startyear, end_col_name=endyear)
  nesp_lpi<-LPIMain(infile_name, REF_YEAR=year, PLOT_MAX=plotmax,
                    BOOT_STRAP_SIZE=bootstrap, VERBOSE=TRUE, goParallel=TRUE, title=ytitle, plot_lpi=0, save_plots=0)
  # ggplot_lpi(nesp_lpi)
}

system(paste(original_wd, "/clean.sh \"", getwd(), "\"", sep=""))
