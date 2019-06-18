#!/bin/bash

set -e

python -m tsx.import_taxa sample-data/TaxonList.xlsx
python -m tsx.importer --type 1 -c sample-data/type_1_sample.csv
python -m tsx.importer --type 2 -c sample-data/type_2_sample.csv
python -m tsx.import_region sample-data/spatial/Regions.shp

python -m tsx.import_processing_method sample-data/processing_method.csv
python -m tsx.process -c t1_aggregation
python -m tsx.import_incidental sample-data/incidental_sightings.csv
python -m tsx.import_range sample-data/spatial/species-range
python -m tsx.process -c alpha_hull
python -m tsx.process -c range_ultrataxon
python -m tsx.import_t2_site sample-data/spatial/t2_site.shp
python -m tsx.import_grid sample-data/spatial/10min_mainland.shp
python -m tsx.process -c pseudo_absence
python -m tsx.process -c response_variable
python -m tsx.process -c spatial_rep
python -m tsx.import_data_source sample-data/data_source.csv
python -m tsx.process -c filter_time_series
python -m tsx.process export_lpi
python -m tsx.process export_lpi --filter

echo "WORKFLOW TEST SUCCESSFUL"
