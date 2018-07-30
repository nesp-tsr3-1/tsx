from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tsx.db.models import Base
from tsx.config import config

def get_database_url():
    type = config.get("database", "type").strip()
    host = config.get("database", "host").strip()
    username = config.get("database", "username").strip()
    password = config.get("database", "password").strip()
    name = config.get("database", "name").strip()
    # url = dialect[+driver]://user:password@host/dbname
    url = "%s://%s:%s@%s/%s" % (type, username, password, host, name)
    return url


def get_session():
    session = Session()
    return session

engine = create_engine(get_database_url(),
    convert_unicode=True,
    pool_recycle=600) # Avoid DB connection timeout

Session = sessionmaker(bind=engine)
