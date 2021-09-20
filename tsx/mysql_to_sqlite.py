from tsx.db import get_session
import sqlite3
import logging

log = logging.getLogger(__name__)

def init_sqlite(path):
    db = sqlite3.connect(path)
    db.enable_load_extension(True)
    # If this segfaults, it could be due to the import order of the 'fiona' package, along the lines of this bug:
    # https://github.com/Toblerity/Fiona/issues/383
    # It may be due to the import order in a completely unrelated file e.g. alpha_hull.py
    # Also other packages seem to be involved too e.g. pyproj
    db.load_extension("mod_spatialite")
    db.execute("SELECT InitSpatialMetaData()")
    return db

def export_to_sqlite(source_id, path):
    session = get_session()
    dest_db = init_sqlite(path)
    # tables = [table for (table,) in session.execute("show tables").fetchall()]
    tables = [
        ("t1_survey", "source_id = :source_id"),
        ("t1_site", "source_id = :source_id"),
        ("t1_sighting", "survey_id IN (SELECT id FROM t1_survey WHERE source_id = :source_id)"),
        ("taxon", "id IN (SELECT taxon_id FROM t1_sighting, t1_survey WHERE survey_id = t1_survey.id AND source_id = :source_id)"),
        ("aggregated_by_month", "FALSE"),
        ("aggregated_by_year", "FALSE"),
        ("taxon_group", None),
        ("taxon_status", None),
        ("search_type", None),
        ("source", "id = :source_id"),
        ("t2_site", "FALSE"),
        ("data_source", "source_id = :source_id"),
        ("region", "FALSE"),
        ("unit", None),
        ("taxon_source_alpha_hull", "FALSE"),
        ("intensive_management", None),
        ("experimental_design_type", None),
        ("response_variable_type", None),
        ("monitoring_program", None)
    ]

    for table, where_clause in tables:
        # print(table)
        copy_table_schema(session, table, dest_db)
        copy_table_data(session, table, dest_db, where_clause, { 'source_id': source_id })

    return path

def copy_db(session, dest_db):
    tables = [table for (table,) in session.execute("show tables").fetchall()]
    for table in tables:
        copy_table_schema(session, table, dest_db)
        copy_table_data(session, table, dest_db)

def drop_table(dest_db, table):
    dest_db.execute("SELECT DiscardGeometryColumn(f_table_name, f_geometry_column) FROM geometry_columns WHERE f_table_name = ?", (table,))
    dest_db.execute("DROP TABLE IF EXISTS %s" % table)

def copy_table_schema(session, table, dest_db):
    drop_table(dest_db, table)
    created = False
    field_defs = []
    # Note: we create columns one by one because that is the only supported way to create spatial columns
    # (https://www.gaia-gis.it/gaia-sins/spatialite-cookbook/html/new-geom.html)
    # However you can't create a table with no columns.
    for (name, datatype, nullable, key, default, extra) in session.execute("describe `%s`" % table).fetchall():
        datatype = datatype.decode("utf-8")
        if is_spatial_datatype(datatype):
            if created == False:
                raise "First column cannot be a spatial column"
            sql = "SELECT AddGeometryColumn('%s', '%s', -1, '%s', 'XY', %s)" % (table, name, datatype, {'YES': 0}.get(nullable, 1))
        else:
            field_def = "`%s` %s %s %s DEFAULT %s" % (
                name,
                datatype,
                { "NO": "NOT NULL" }.get(nullable, ""),
                # { "PRI": "PRIMARY KEY", "UNI": "UNIQUE" }.get(key, ""),
                { "auto_increment": "AUTOINCREMENT" }.get("extra", ""),
                "NULL" if default is None else default.decode("utf-8")
            )
            if not created:
                sql = "CREATE TABLE `%s` (%s)" % (table, field_def)
                created = True
            else:
                sql = "ALTER TABLE `%s` ADD COLUMN %s" % (table, field_def)

        # print(sql)
        dest_db.execute(sql)

def is_spatial_datatype(datatype):
    return datatype.lower() in ["geometry", "geometrycollection", "polygon", "multipolygon", "point", "multipoint", "linestring", "multilinestring"]

def placeholder(datatype):
    if is_spatial_datatype(datatype):
        return "ST_GeomFromWKB(?, -1)"
    else:
        return "?"

def quote_identifier(name):
    return "`%s`" % name

def select_expr(name, datatype):
    if is_spatial_datatype(datatype):
        return "ST_AsWKB(%s)" % quote_identifier(name)
    elif datatype.lower().startswith("decimal("):
        return "CAST(%s AS DOUBLE)" % quote_identifier(name)
    elif datatype.lower() == "time":
        return "CAST(%s AS CHAR(10))" % quote_identifier(name)
    else:
        return quote_identifier(name)


def copy_table_data(session, table, dest_db, select_where_clause = None, select_params = {}):
    fields = [(name, datatype.decode('utf-8')) for (name, datatype, nullable, key, default, extra) in session.execute("describe `%s`" % table).fetchall()]
    select_exprs = ", ".join(select_expr(name, datatype) for (name, datatype) in fields)
    insert_exprs = ", ".join(quote_identifier(name) for (name, datatype) in fields)
    placeholders = ', '.join(placeholder(datatype) for (name, datatype) in fields)

    select_sql = "SELECT %s FROM `%s`" % (select_exprs, table)
    if select_where_clause:
        select_sql = select_sql + " WHERE " + select_where_clause
    insert_sql = "INSERT INTO %s (%s) VALUES (%s)" % (table, insert_exprs, placeholders)

    # print(select_sql)
    # print(insert_sql)

    if fields[0] == 'id':
        pos = 0
        while True:
            select_params['pos'] = pos
            rows = session.execute(select_sql + " WHERE id > :pos ORDER BY id LIMIT 10000", select_params).fetchall()
            if len(rows) == 0:
                break
            else:
                pos = rows[-1][0]
            dest_db.executemany(insert_sql, rows)
            dest_db.commit()
    else:
        result = session.execute(select_sql, select_params)
        def flush(rows):
            if len(rows) > 0:
                # print(rows[0])
                dest_db.executemany(insert_sql, rows)
                dest_db.commit()
        rows = []
        while True:
            row = result.fetchone()
            if not row:
                flush(rows)
                break
            rows.append(row)
            if len(rows) > 1000:
                flush(rows)
                rows = []

# Helper to make logging and progress bar work together
class TqdmStream(object):
    def write(self, x):
        tqdm.write(x.strip())
    def flush(self):
        pass

def main():
    logging.basicConfig(stream=TqdmStream(), level=logging.INFO, format='%(asctime)-15s %(levelname)-8s %(message)s')

    parser = argparse.ArgumentParser(description='TSX processing utility')

    parser.add_argument('--species', '-s', help='Comma separated list of species numbers (SPNO) to process')
    parser.add_argument('--commit', '-c', action='store_true', dest='commit', help='Commit changes to database (default is dry-run)')

    subparsers = parser.add_subparsers(help = 'command', dest = 'command')

    p = subparsers.add_parser('alpha_hull')
    p = subparsers.add_parser('export')

    p.add_argument('layers', nargs='+', choices=['alpha', 'ultrataxa', 'pa', 'grid'], help='Layers to export')

    p = subparsers.add_parser('range_ultrataxon')
    p = subparsers.add_parser('pseudo_absence')
    p = subparsers.add_parser('t1_aggregation')
    p = subparsers.add_parser('response_variable')
    p = subparsers.add_parser('export_lpi')

    p.add_argument('--monthly', '-m', action='store_true', dest='monthly', help='Output a column for each month')
    p.add_argument('--filter', '-f', action='store_true', dest='filter', help='Filter output')
    p.add_argument('--all-years', '-a', action='store_true', dest='include_all_years_data', help='Include data for all years')

    p = subparsers.add_parser('spatial_rep')
    p = subparsers.add_parser('filter_time_series')
    p = subparsers.add_parser('clear')
    p = subparsers.add_parser('all')
    p = subparsers.add_parser('simple')

    p = subparsers.add_parser('single_source')
    p.add_argument('source_id', type=int, help='Source ID to process')

    args = parser.parse_args()

    # export_to_sqlite(args.source_id)

if __name__ == '__main__':
    main()
