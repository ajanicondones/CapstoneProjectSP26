from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

# base
Base = declarative_base()

# engine
engine = create_engine("sqlite:///WHOInfo.db", echo=True)

# model
class Health(Base):
    __tablename__ = "health_data"
    id = Column(Integer, primary_key=True, index=True)
    indicator_name = Column(String)
    indicator_code = Column(String)
    location = Column(String)        # country
    location_code = Column(String)
    year = Column(Integer)
    disaggregation = Column(String)
    numeric_value = Column(Float)
    display_value = Column(String)
    comments = Column(String)

Base.metadata.create_all(engine)

def get_db():
    db = sessionmaker(bind=engine)()
    try:
        yield db
    finally:
        db.close()
