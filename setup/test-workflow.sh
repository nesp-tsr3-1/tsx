#!/bin/bash

set -e

echo IMPORT TAXON LIST
python -m tsx.import_taxa sample-data/TaxonList.xlsx

echo IMPORT TYPE 1 DATA
python -m tsx.importer --type 1 -c sample-data/type_1_sample.csv

echo IMPORT TYPE 2 DATA
python -m tsx.importer --type 2 -c sample-data/type_2_sample.csv

echo IMPORT REGIONS
python -m tsx.import_region sample-data/spatial/Regions-simplified.shp

echo IMPORT PROCESSING METHODS
python -m tsx.import_processing_method sample-data/processing_method.csv

echo TYPE 1 DATA AGGREGATION
python -m tsx.process -c t1_aggregation

echo IMPORT INCIDENTAL SIGHTINGS
python -m tsx.import_incidental sample-data/incidental_sightings.csv

echo IMPORT SPECIES RANGES
python -m tsx.import_range sample-data/spatial/species-range

echo GENERATE ALPHA HULLS
python -m tsx.process -c alpha_hull

echo TYPE 2 DATA AGGREGATION
python -m tsx.process -c t2_aggregation

echo CALCULATE SPATIAL REPRESENTATIVENESS
python -m tsx.process -c spatial_rep

echo IMPORT DATA SOURCE METADATA
python -m tsx.import_data_source sample-data/data_source.csv

echo FILTER TIME SERIES
python -m tsx.process -c filter_time_series

echo EXPORT TIME SERIES
python -m tsx.process export_lpi

echo GENERATE PERMUTATIONS
python -m tsx.run_permutations data/export/lpi.csv data/export/results-test.db 2015

echo EXPORT TIME SERIES AND TAXA FOR VISUALISER
python -m tsx.export_results data/export/lpi.csv data/export/results-test.db

echo "WORKFLOW TEST SUCCESSFUL"
