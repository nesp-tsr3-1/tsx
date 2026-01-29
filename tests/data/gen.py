#!/usr/bin/env python

# Generate test data
from random import Random
from openpyxl import Workbook
import fiona
from shapely.geometry import shape
from shapely import minimum_bounding_radius
from fiona.transform import transform_geom
from freezegun import freeze_time
import csv
from datetime import datetime
import subprocess

num_sites_per_region = 5

def main():
    save_xlsx(gen_taxa(), "TaxonList", "tests/data/TaxonList.xlsx")
    save_csv(gen_t1_data(), "tests/data/t1_data.csv")

taxonomic_groups = [
    'Birds',
    'Amphibians',
    'Fish',
    'Invertebrates',
    'Mammals',
    'Plants',
    'Reptiles'
]

statuses = [
    'Least Concern',
    'Near Threatened',
    'Vulnerable',
    'Endangered',
    'Critically Endangered',
    'Critically Endangered (possibly extinct',
    'Extinct',
    ''
]

populations = [
    "Endemic",
    "Australian",
    "Non-breeding",
    "Domestic",
    "Introduced"
]

functional_groups = [
    ("Amphibians", "Chytrid-impacted"),
    ("Amphibians", "Terrestrial breeding"),
    ("Amphibians", "Chytrid impacted"),
    ("Amphibians", "Chytrid non-impacted"),
    ("Amphibians", "Wetland breeding"),
    ("Amphibians", "Stream breeding"),
    ("Birds", "Terrestrial:Mallee woodland"),
    ("Birds", "Terrestrial:Dry sclerophyll woodland/forest"),
    ("Birds", "Marine:Penguins"),
    ("Birds", "Terrestrial:Tropical savanna woodland"),
    ("Birds", "Terrestrial:Island endemic"),
    ("Birds", "Marine:Petrels and Shearwaters"),
    ("Birds", "Terrestrial:Grassland"),
    ("Birds", "Marine"),
    ("Birds", "Marine:Albatrosses and Giant-Petrels"),
    ("Birds", "Shoreline (resident)"),
    ("Mammals", "Marine"),
    ("Mammals", "Terrestrial:Volant"),
    ("Mammals", "Terrestrial:Arboreal"),
    ("Mammals", ">5000g"),
    ("Mammals", "50-5000g"),
    ("Mammals", "<50g"),
    ("Mammals", "Terrestrial"),
    ("Plants", "Shrub"),
    ("Plants", "Herbaceous"),
    ("Plants", "Orchid"),
    ("Plants", "Tree"),
    ("Plants", "Vine"),
    ("Plants", "Fern"),
    ("Plants", "Grass"),
    ("Plants", "Cycad"),
    ("Reptiles", "Terrestrial"),
    ("Reptiles", "Freshwater"),
    ("Reptiles", "Marine")
]

management_categories = [
    "Actively managed",
    "No management",
    "Unknown"
]

units = [
    ("Sample: Occupancy (# presences/# surveys)", "Binary"),
    ("Sample: abundance (counts)", "Continuous"),
    ("Sample: density (counts/fixed areas)", "Continuous"),
    ("Proportion of surveyed sites that had animal tracks/signs", "Percentage")
]

search_types = [
    "2ha 20 minute search",
    "500m Area search",
    "5km Area search",
    "Shorebird count area survey",
    "Breeding territory monitoring",
    "Incidental search",
    "Fixed route search"
]

def taxon_id_prefix(taxonomic_group):
    if taxonomic_group == "Birds":
        return ""
    else:
        return taxonomic_group[0].lower()

def singular(name):
    return name.removesuffix("s")

def save_xlsx(data, sheet_name, filename):
    # To avoid generated file changing each time due to created/modified timestamps
    with freeze_time("2000-01-01"):
        wb = Workbook()
        ws = wb.active
        ws.title = sheet_name

        for i, row in enumerate(data):
            if i == 0:
                ws.append(list(row.keys()))
            ws.append(list(row.values()))

        wb.save(filename)

    subprocess.run(["stripzip", filename])

def save_csv(data, filename):
    with open(filename, 'w') as file:
        writer = csv.writer(file)
        for i, row in enumerate(data):
            if i == 0:
                writer.writerow(list(row.keys()))
            writer.writerow(list(str(x) for x in row.values()))


def gen_taxa():
    random = Random("gen_taxa")
    result = []
    next_id = 1
    for taxonomic_group in taxonomic_groups:
        groups = [g for t, g in functional_groups if t == taxonomic_group]
        groups.append("")
        for i, status in enumerate(statuses):
            row = {
                "TaxonomicGroup": taxonomic_group,
                "UltrataxonID": "",
                "TaxonLevel": "sp",
                "SpNo": "",
                "TaxonID": "%s%s" % (taxon_id_prefix(taxonomic_group), next_id),
                "TaxonCommonName": "%s #%s" % (singular(taxonomic_group), i + 1),
                "TaxonScientificName": "%s #%s SciName" % (singular(taxonomic_group), i + 1),
                "FamilyCommonName": "%s Family" % singular(taxonomic_group),
                "FamilyScientificName": "%s Family SciName" % singular(taxonomic_group),
                "Order": "%s Order" % singular(taxonomic_group),
                "Population": random.choice(populations),
                "EPBCStatus": random.choice(statuses),
                "IUCNStatus": status,
                "FunctionalGroup": random.choice(groups),
                "NationalPriorityTaxa": random.random() < 0.2
            }
            result.append(row)
            next_id += 1

    return result

def gen_t1_sites():
    random = Random("t1_sites")
    sites = []
    next_id = 1
    with fiona.open("tests/data/regions/regions.shp") as shp:
        for feature in shp:
            geometry = shape(transform_geom(shp.crs, 'EPSG:4326', feature['geometry']))
            geometry = geometry.buffer(0)
            centroid = geometry.centroid
            radius = minimum_bounding_radius(geometry)

            for i in range(0, num_sites_per_region):
                x = random.gauss(centroid.x, radius / 2)
                y = random.gauss(centroid.y, radius / 2)
                sites.append({
                    "X": x,
                    "Y": y,
                    "SiteName": "Site %s" % next_id,
                    "ManagementCategory": random.choice(management_categories)
                })
                next_id += 1

    return sites

def gen_t1_data():
    random = Random("t1_data")
    next_id = 1
    result = []
    sites = gen_t1_sites()
    taxa = gen_taxa()
    source_name = "T1 Source"
    unit, unit_type = random.choice(units)
    search_type = random.choice(search_types)
    source_taxa = taxa

    for site in random.sample(sites, 5):
        for taxon in random.sample(source_taxa, 5):
            a = random.randrange(1950, 2025, 1)
            b = random.randrange(1950, 2025, 1)
            (min_year, max_year) = (min(a, b), max(a, b))

            for y in range(min_year, max_year + 1):
                m = random.randrange(1, 13, 1)
                d = random.randrange(1, 29, 1)

                if random.random() < 0.9:
                    row = {
                        "SourcePrimaryKey": "%s - %s" % (source_name, next_id),
                        "SourceType": "custodian",
                        "SourceDesc": source_name,
                        "DataProcessingType": "None (data are raw data)",
                        "SearchTypeDesc": search_type,
                        "ProjectionReference": "EPSG:4326",
                        "StartDate": "%s/%s/%s" % (d, m, y),
                        "FinishDate": "%s/%s/%s" % (d, m, y),
                        "TaxonID": taxon["TaxonID"],
                        "ScientificName": taxon["TaxonScientificName"],
                        "Count": random.randrange(0, 10, 1),
                        "UnitOfMeasurement": unit,
                        "UnitType": unit_type,
                        **site
                    }
                    result.append(row)
                    next_id += 1
    return result

if __name__ == '__main__':
    main()
