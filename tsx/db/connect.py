from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from tsx.db.models import Base
from tsx.config import config
import mysql.connector
import os
import logging
import sqlite3

log = logging.getLogger(__name__)

# database_config can be a config file section, or a database connection url (e.g. for sqlite)
def get_database_url(database_config=None):
    if database_config == None:
        database_config = "database"

    if ":" in database_config:
        return database_config

    type = config.get(database_config, "type").strip()
    host = config.get(database_config, "host").strip()
    username = config.get(database_config, "username").strip()
    password = config.get(database_config, "password").strip()
    name = config.get(database_config, "name").strip()

    # url = dialect[+driver]://user:password@host/dbname
    url = "%s://%s:%s@%s/%s" % (type, username, password, host, name)

    return url

# We detect process ID so we can automatically start a new engine for new processes
last_pid = os.getpid()

cached_session_makers = {}
def get_session_maker(database_config=None):
    if database_config == None:
        database_config = "database"
    global last_pid
    if last_pid != os.getpid():
        last_pid = os.getpid()
        clear_session_maker_cache()

    if database_config not in cached_session_makers:
        url = get_database_url(database_config=database_config)
        connect_args = {}
        if url.startswith("mysql"):
            connect_args['use_pure'] = True
        engine = create_engine(url,
            pool_recycle=600, # Avoid DB connection timeout
            connect_args = connect_args,
            future=True) # This avoids weird intermittent 'Access denied for user' error (maybe due to a bug in the MySQL C connector?)

        @event.listens_for(engine, "connect")
        def connect(dbapi_connection, connection_record):
            if dbapi_connection.__class__ == sqlite3.Connection:
                setup_sqlite_conn(dbapi_connection)


        cached_session_makers[database_config] = scoped_session(sessionmaker(bind=engine, future=True))

    return cached_session_makers[database_config]

def setup_sqlite_conn(conn):
    # Load spatialite extension
    conn.enable_load_extension(True)
    conn.load_extension("mod_spatialite")
    conn.enable_load_extension(False)
    # Add a couple of functions for MySQL compatibility
    conn.create_function('CONCAT', -1, sqlite_concat, deterministic=True)
    conn.create_function('LPAD', 3, sqlite_lpad, deterministic=True)

def sqlite_concat(*args):
    return "".join(str(x) for x in args)

def sqlite_lpad(s, padlen, padstr):
    strlen = len(s)
    if strlen < padlen:
        return padstr * (padlen - strlen) + s
    else:
        return s[0..padlen]

def clear_session_maker_cache():
    global cached_session_makers
    cached_session_makers = {}

def get_session(database_config=None):
    if database_config == None:
        database_config = "database"
    session = get_session_maker(database_config=database_config)()
    return session

Session = get_session_maker()
