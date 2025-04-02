from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


#url de la base de datos , toca que cambien la contraseña a la de ustedes cada vez que quieran probar


#URL_DB="mysql+mysqlconnector://root:osjdiaz123@localhost:3306/racadi_academy"
URL_DB="mysql+mysqlconnector://db_admin:admin_adso*@localhost:3306/racadi_academy"

crear=create_engine(URL_DB)
SessionLocal=sessionmaker(autocommit=False,autoflush=False, bind=crear)
base=declarative_base()


def get_db():
    conex=SessionLocal()
    try:
        yield conex
    finally: 
        conex.close()