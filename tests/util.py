import os
import subprocess
import filecmp

def import_test_data(db_name, table_name):
    subprocess.run([
        "sh", "-c",
        "python -m tsx.mysql_csv import --delete %s %s < tests/data/%s.csv" % (db_name, table_name, table_name)
    ]).check_returncode()

def compare_output(db_name, table_name, output_dir):
    output_path = os.path.join(output_dir, '%s.csv' % table_name)
    expected_output_path = os.path.join('tests', 'data', '%s.csv' % table_name)
    subprocess.run(["sh", "-c", "python -m tsx.mysql_csv export %s %s > %s" % (db_name, table_name, output_path)]).check_returncode()
    assert filecmp.cmp(output_path, expected_output_path)

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
