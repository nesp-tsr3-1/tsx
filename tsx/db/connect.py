from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from tsx.db.models import Base
from tsx.config import config
import mysql.connector
import os
import logging

log = logging.getLogger(__name__)

def get_database_url(database_config="database"):
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
def get_session_maker(database_config="database"):
    global last_pid
    if last_pid != os.getpid():
        last_pid = os.getpid()
        clear_session_maker_cache()

    if database_config not in cached_session_makers:
        engine = create_engine(get_database_url(database_config=database_config),
            convert_unicode=True,
            pool_recycle=600, # Avoid DB connection timeout
            connect_args = {'use_pure':True}) # This avoids weird intermittent 'Access denied for user' error (maybe due to a bug in the MySQL C connector?)

        cached_session_makers[database_config] = scoped_session(sessionmaker(bind=engine))

    return cached_session_makers[database_config]

def clear_session_maker_cache():
    global cached_session_makers
    cached_session_makers = {}

def get_session(database_config="database"):
    session = get_session_maker(database_config=database_config)()
    return session

Session = get_session_maker()
