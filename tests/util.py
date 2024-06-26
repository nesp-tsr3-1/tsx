import os

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
