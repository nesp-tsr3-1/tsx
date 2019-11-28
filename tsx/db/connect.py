from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from tsx.db.models import Base
from tsx.config import config
import mysql.connector
from tsx.util import memoized

def get_database_url(database_config="database"):
    type = config.get(database_config, "type").strip()
    host = config.get(database_config, "host").strip()
    username = config.get(database_config, "username").strip()
    password = config.get(database_config, "password").strip()
    name = config.get(database_config, "name").strip()

    # url = dialect[+driver]://user:password@host/dbname
    url = "%s://%s:%s@%s/%s" % (type, username, password, host, name)

    return url

@memoized
def get_session_maker(database_config="database"):
    engine = create_engine(get_database_url(database_config=database_config),
        convert_unicode=True,
        pool_recycle=600, # Avoid DB connection timeout
        connect_args = {'use_pure':True}) # This avoids weird intermittent 'Access denied for user' error (maybe due to a bug in the MySQL C connector?)

    return scoped_session(sessionmaker(bind=engine))

def get_session(database_config="database"):
    session = get_session_maker(database_config=database_config)()
    return session

Session = get_session_maker()