import subprocess
from tests.util import get_single, seed_db

def test_type1_import(fresh_database):
    seed_db(fresh_database, 'sample_taxa')

    for cmd in [
        "python -m tsx.importer --type 1 -c sample-data/type_1_sample.csv"
        ]:
        subprocess.run(cmd.split(" "))

    conn = fresh_database()
    assert(get_single(conn, 'select count(*) from t1_survey') == 253)
    conn.close()


def test_type2_import(fresh_database):
    seed_db(fresh_database, 'sample_taxa')
    for cmd in [
        "python -m tsx.importer --type 2 -c sample-data/type_2_sample.csv"
        ]:
        subprocess.run(cmd.split(" "))

    conn = fresh_database()
    # TODO: use smaller dataset
    assert(get_single(conn, 'select count(*) from t2_survey') == 48937)
    conn.close()
