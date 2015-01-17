from sqlalchemy import create_engine
engine = create_engine('sqlite:///:memory:', echo=True)
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer
class T1(Base):
    __tablename__ = 't1'
    f1 = Column(Integer, primary_key=True)
Base.metadata.create_all(engine)
r1 = T1(f1=33)
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
session = Session()
session.add(r1)
from sqlalchemy.sql import exists
assert session.query(exists().where(T1.f1 == 33)).scalar()
assert not session.query(exists().where(T1.f1 == 99)).scalar()
