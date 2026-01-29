import subprocess
from tests.util import import_test_data, compare_output
import os
import filecmp

def test_import_type1(fresh_database, db_name, output_dir):
    import_test_data(db_name, 'source')
    import_test_data(db_name, 'taxon_level')
    import_test_data(db_name, 'taxon')

    for cmd in [
        ["python", "-m", "tsx.importer",
            "--type", "1",
            "-c",
            "-s", "1",
            "tests/data/t1_data.csv"]
        ]:
        subprocess.run(cmd).check_returncode()

    for table in ["t1_sighting", "t1_survey", "t1_site"]:
        compare_output(db_name, table, output_dir)
