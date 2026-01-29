import subprocess
from tests.util import import_test_data, compare_output

def test_t1_aggregation(fresh_database, db_name, output_dir):
    import_test_data(db_name, 'unit')
    import_test_data(db_name, 'source')
    import_test_data(db_name, 'taxon_level')
    import_test_data(db_name, 'taxon')
    import_test_data(db_name, 't1_site')
    import_test_data(db_name, 't1_survey')
    import_test_data(db_name, 't1_sighting')
    import_test_data(db_name, 'processing_method')

    for cmd in [
        ["python", "-m", "tsx.process", "-c", "t1_aggregation"]
        ]:
        subprocess.run(cmd).check_returncode()

    for table in ["aggregated_by_month", "aggregated_by_year"]:
        compare_output(db_name, table, output_dir)
