#!/bin/bash

# Usage: run.sh | parallel

## Note: the 'GROUPING' parameter below is generated using the following SQL query:
##
## SET SESSION group_concat_max_len = 4096;
## SELECT GROUP_CONCAT('"', x, '"' SEPARATOR " ") FROM (
##   SELECT DISTINCT CONCAT(taxonomic_group, ':', group_name, ':', COALESCE(subgroup_name, 'All')) AS x
##     FROM taxon
##     JOIN taxon_group ON taxon.id = taxon_id
##   UNION
##   SELECT DISTINCT CONCAT(taxonomic_group, ':', group_name, ':All')
##     FROM taxon
##     JOIN taxon_group ON taxon.id = taxon_id
##   UNION
##   SELECT DISTINCT CONCAT(taxonomic_group, ':All:All')
##     FROM taxon
##   UNION
##   SELECT 'All:All:All' UNION SELECT 'All:Marine:All' UNION SELECT 'All:Terrestrial:All'
## ) t
##

GROUPING=("Birds:Shoreline (migratory):All" "Birds:Marine:Petrels and Shearwaters" "Mammals:50-5000g:All" "Mammals:Terrestrial:All" "Mammals:>5000g:All" "Mammals:Marine:All" "Mammals:Terrestrial:Arboreal" "Mammals:<50g:All" "Mammals:Terrestrial:Volant" "Plants:Shrub:All" "Plants:Herbaceous:All" "Plants:Orchid:All" "Plants:Tree/Shrub:All" "Plants:Tree:All" "Plants:Grass:All" "Birds:Marine:Tropicbirds Frigatebirds Gannets Boobies" "Birds:Marine:Gulls Terns Noddies Skuas Jaegers" "Birds:Wetland:All" "Birds:Terrestrial:Grassland" "Birds:Terrestrial:Island endemic" "Birds:Terrestrial:All" "Birds:Terrestrial:Rainforest" "Birds:Terrestrial:Dry sclerophyll woodland/forest" "Birds:Terrestrial:Tropical savanna woodland" "Birds:Terrestrial:Heathland" "Birds:Terrestrial:Mallee woodland" "Birds:Marine:Albatrosses and Giant-Petrels" "Birds:Marine:All" "Birds:All:All" "Mammals:All:All" "Plants:All:All" "All:All:All" "All:Marine:All" "All:Terrestrial:All")

STATE=("All" "Australian Capital Territory" "Commonwealth" "Queensland" "New South Wales" "Northern Territory" "South Australia" "Western Australia" "Tasmania" "Victoria" "Australian Capital Territory+New South Wales")

STATUSAUTH=("Max" "EPBC" "IUCN" "BirdActionPlan")

STATUS=("Vulnerable+Endangered+Critically Endangered" "Near Threatened+Vulnerable+Endangered+Critically Endangered" "Near Threatened")

MANAGEMENT=("All sites" "Actively managed" "No known management")

export OUTPUT_DIR=output-$(date +%Y-%m-%d)
export INPUT="$(pwd)/lpi-filtered.csv"
export LPI_SCRIPT=lpi_run1.R
export START_YEAR=1950
export END_YEAR=2019

mkdir -p "$OUTPUT_DIR"

# Foregoing indentation for readability
for grouping in "${GROUPING[@]}"; do
for state in "${STATE[@]}"; do
for statusauth in "${STATUSAUTH[@]}"; do
for status in "${STATUS[@]}"; do
for management in "${MANAGEMENT[@]}"; do

	echo Rscript \"$LPI_SCRIPT\" \"$grouping\" \"$state\" \"$statusauth\" \"$status\" \"$management\" FALSE 1000 1985 $START_YEAR $END_YEAR \"$INPUT\" \"$OUTPUT_DIR/\"

done; done; done; done; done;

for management in "${MANAGEMENT[@]}"; do
	grouping="All:All:All"
	state="All"
	statusauth="All"
	status="All"
	echo Rscript \"$LPI_SCRIPT\" \"$grouping\" \"$state\" \"$statusauth\" \"$status\" \"$management\" TRUE 1000 1985 $START_YEAR $END_YEAR \"$INPUT\" \"$OUTPUT_DIR/\"
done
