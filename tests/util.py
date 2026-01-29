import os
import subprocess
import filecmp
import tempfile
import textwrap

def import_test_data(db_name, table_name, *, csv_file=None, csv_data=None):
    """
    Import CSV data into the specific database and table

    If csv_file is specified, data will be loaded from the file at that path
    If csv_data is specified, that data will be loaded directly
    If neither is specified, data will be loaded from tests/data/<table_name>.csv
    """
    if csv_file is None:
        if csv_data is None:
            csv_file = os.path.join("tests", "data", "%s.csv" % table_name)
        else:
            with tempfile.NamedTemporaryFile(delete_on_close=False) as f:
                f.write(textwrap.dedent(csv_data).encode("utf8"))
                f.close()
                return import_test_data(db_name, table_name, csv_file = f.name)
    else:
        if csv_data is not None:
            raise ValueError("Cannot specify csv_file and csv_data at the same time")


    subprocess.run([
        "sh", "-c",
        "python -m tsx.mysql_csv import --delete %s %s < %s" % (db_name, table_name, csv_file)
    ]).check_returncode()

def compare_output(db_name, table_name, output_dir):
    output_path = os.path.join(output_dir, '%s.csv' % table_name)
    expected_output_path = os.path.join('tests', 'data', '%s.csv' % table_name)
    subprocess.run(["sh", "-c", "python -m tsx.mysql_csv export %s %s > %s" % (db_name, table_name, output_path)]).check_returncode()
    assert filecmp.cmp(output_path, expected_output_path)

def get_csv_data(db_name, table_name):
    result = subprocess.run(
        ["python", "-m", "tsx.mysql_csv", "export", db_name, table_name],
        capture_output=True,
        text=True)
    result.check_returncode()
    return result.stdout

def get_single(conn, query):
    with conn.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()
        return result[0][0]

def seed_db(connection_maker, seed_file):
    conn = connection_maker()
    with conn.cursor() as cursor:
        with open(os.path.join('tests', 'seed', "%s.sql" % seed_file)) as f:
            sql = f.read()

        for _ in cursor.execute(sql, multi=True):
            pass

    conn.commit()
    conn.close()
