import subprocess
from tests.util import compare_output

def test_import_taxa(fresh_database, db_name, output_dir):
    for cmd in [
        "python -m tsx.import_taxa tests/data/TaxonList.xlsx"
        ]:
        subprocess.run(cmd.split(" ")).check_returncode()

    compare_output(db_name, "taxon", output_dir)
