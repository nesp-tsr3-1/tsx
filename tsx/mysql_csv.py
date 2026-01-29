import logging
import argparse
import mysql.connector
import os
import re
import csv
import sys

log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler(sys.stderr))
log.setLevel(logging.DEBUG)

pagesize = 10000

def main():
    parser = argparse.ArgumentParser(description='Export and import MySQL tables in CSV format')

    parser.add_argument('command', help='Import or export', choices=['import', 'export'])
    parser.add_argument('database', help='Database name')
    parser.add_argument('table', help='Table to export')

    parser.add_argument('--host', help='MySQL hostname')
    parser.add_argument('--user', '-u', help='MySQL user')
    parser.add_argument('--password', '-p', help='MySQL password')
    parser.add_argument('--port', '-P', type=int, help='MySQL port')
    parser.add_argument('--delete', action='store_true', dest='delete', help='Delete existing data before importing')

    args = parser.parse_args()

    table = args.table

    if not is_safe_identifier(table):
        log.error("Invalid table name: %s" % table)
        log.error("This tool only supports table names that consist of alphanumeric characters and underscores, not starting with a digit.")
        exit(1)

    connect_args = [
        ('option_files', os.path.expanduser('~/.my.cnf')),
        ('database', args.database),
        ('user', args.user),
        ('host', args.host),
        ('port', args.port),
        ('password', args.password)
    ]
    connect_args = {k: v for k, v in connect_args if v is not None}

    cnx = mysql.connector.connect(**connect_args)

    if args.command == 'export':
        perform_export(table, cnx)
    elif args.command == 'import':
        perform_import(table, cnx, args.delete)
    else:
        raise ValueError("invalid command: %s" % args.command)

def perform_export(table, cnx):
    # Note: we could probably go faster with raw=True, ensuring that we are connected with the correct charset
    cur = cnx.cursor(buffered=False, raw=False)

    columns = get_columns(cur, table)
    primary_key_columns = get_primary_key(cur, table) or [col for (col, type) in columns]

    if not columns_ok(columns):
        exit(1)

    sql = """SELECT %s FROM %s ORDER BY %s""" % (
        ",\n".join(select_clause(col, type) for col, type in columns),
        quote_identifier(table),
        ", ".join("%s.%s" % (quote_identifier(table), quote_identifier(col)) for col in primary_key_columns)
    )

    log.debug(sql)

    cur.execute(sql)
    writer = csv.writer(sys.stdout)
    writer.writerow([name for (name, type) in columns])
    while True:
        rows = cur.fetchmany(pagesize)
        if len(rows):
            for row in rows:
                writer.writerow([export_val(val) for val in row])
        else:
            break

def perform_import(table, cnx, delete):
    cur = cnx.cursor(buffered=False, raw=False)

    columns = get_columns(cur, table)
    primary_key_columns = get_primary_key(cur, table)

    if not columns_ok(columns):
        exit(1)

    db_column_names = [name for name, type in columns]

    # Check that CSV column names match database
    reader = csv.reader(sys.stdin)
    is_header = True
    sql = None
    current_batch = []

    if delete:
        cur.execute("DELETE FROM %s" % quote_identifier(table))

    for row in reader:
        if is_header:
            csv_column_names = row
            unknown_columns = set(csv_column_names) - set(db_column_names)
            if len(unknown_columns):
                log.error("CSV contains unknown column names: %s" % unknown_columns)
                exit(1)
            missing_columns = set(db_column_names) - set(csv_column_names)
            if len(missing_columns):
                log.error("CSV is missing columns: %s" % missing_columns)
                exit(1)
            sql = """INSERT INTO %s (%s) VALUES (%s)""" % (
                quote_identifier(table),
                ",\n".join(quote_identifier(col) for col in csv_column_names),
                ", ".join(insert_clause(col, type) for col, type in columns)
            )
            log.debug(sql)
            is_header = False
        else:
            assert len(row) == len(columns)
            current_batch.append([import_val(val) for val in row])
            if len(current_batch) >= pagesize:
                cur.executemany(sql, current_batch)
                current_batch = []

    if len(current_batch):
        cur.executemany(sql, current_batch)

    cnx.commit()

def columns_ok(columns):
    for (name, type) in columns:
        if not is_safe_identifier(name):
            log.error("Invalid column name: %s" % name)
            log.error("This tool only supports column names that consist of alphanumeric characters and underscores, not starting with a digit.")
            return False
    return True

def import_val(val):
    if val == "NULL":
        return None
    else:
        return val

def export_val(val):
    if val is None:
        return "NULL"
    else:
        return str(val)

def quote_identifier(identifier):
    if not is_safe_identifier(identifier):
        raise ValueError('Unsafe identifier: %s' % identifier)
    return "`%s`" % identifier

def select_clause(column, type):
    if type in [
        'geometry',
        'point',
        'linestring',
        'polygon',
        'multipoint',
        'multilinestring',
        'multipolygon',
        'geometrycollection',
        'binary',
        'blob',
        'longblob',
        'mediumblob',
        'varbinary']:
        return "hex(%s) AS %s" % (quote_identifier(column), quote_identifier(column))
    elif type in [
        'varchar',
        'timestamp',

        'char',
        'text',
        'decimal',
        'longtext',
        'mediumtext',

        'datetime',
        'time',
        'enum',
        'float',

        'double',
        'tinyint',
        'smallint',
        'mediumint',
        'int',
        'bigint',

        'date',
        'json',

        'year',
        'set']:
        return "cast(%s AS CHAR) AS %s" % (quote_identifier(column), quote_identifier(column))
        # return quote_identifier(column)
    else:
        log.warning('Unknown data type %s for column %s' % type, column)
        return quote_identifier(column)

def insert_clause(column, type):
    if type in [
        'geometry',
        'point',
        'linestring',
        'polygon',
        'multipoint',
        'multilinestring',
        'multipolygon',
        'geometrycollection',
        'binary',
        'blob',
        'longblob',
        'mediumblob',
        'varbinary']:
        return "unhex(%s)"
    elif type in [
        'varchar',
        'timestamp',

        'char',
        'text',
        'decimal',
        'longtext',
        'mediumtext',

        'datetime',
        'time',
        'enum',
        'float',

        'double',
        'tinyint',
        'smallint',
        'mediumint',
        'int',
        'bigint',

        'date',
        'json',

        'year',
        'set']:
        return "%s"
    else:
        log.warning('Unknown data type %s for column %s' % type, column)
        return "%s"

# Note: we could allow funky table/column names and sys.quote_identifier to safely quote them.
safe_identifier_pattern = re.compile("^[a-zA-Z_][a-zA-Z0-9_]*$")
def is_safe_identifier(identifier):
    return bool(safe_identifier_pattern.match(identifier))

def get_columns(cur, table):
    cur.execute("""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = %s
        AND GENERATION_EXPRESSION = ''
        ORDER BY ORDINAL_POSITION
        """, (table,))
    return cur.fetchall()

def get_primary_key(cur, table):
    cur.execute("""
        SELECT COLUMN_NAME
        FROM information_schema.KEY_COLUMN_USAGE
        JOIN information_schema.TABLE_CONSTRAINTS USING (TABLE_SCHEMA, TABLE_NAME, CONSTRAINT_NAME)
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = %s
        AND CONSTRAINT_TYPE = 'PRIMARY KEY'
        ORDER BY ORDINAL_POSITION;
    """, (table,))
    return [col for (col,) in cur.fetchall()]


if __name__ == '__main__':
    main()
