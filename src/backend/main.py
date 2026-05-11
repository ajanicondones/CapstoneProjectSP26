from pydantic import BaseModel
from database import Health, get_db, engine
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import pandas as pd

app = FastAPI(title="WHO Health")


class HealthMetric(BaseModel):
    country: str
    year: int
    life_expectancy: float
    mortality_rate: float
    health_expenditure: float


def load_csv_to_db():
    from sqlalchemy.orm import sessionmaker
    db = sessionmaker(bind=engine)()
    if db.query(Health).count() == 0:
        df = pd.read_csv("WHO_Data.csv")
        df = df[["IndicatorName", "IndicatorCode", "Location", "LocationCode",
                 "Year", "Disaggregation", "NumericValue", "DisplayValue", "Comments"]].dropna(subset=["NumericValue"])
        for _, row in df.iterrows():
            db.add(Health(
                indicator_name = row["IndicatorName"],
                indicator_code = row["IndicatorCode"],
                location = row["Location"],
                location_code  = row["LocationCode"],
                year = str(row["Year"]),
                disaggregation = str(row["Disaggregation"]),
                numeric_value  = float(row["NumericValue"]),
                display_value  = str(row["DisplayValue"]),
                comments = str(row["Comments"]) if pd.notna(row["Comments"]) else None
            ))
        db.commit()
        print("Database loaded")
    db.close()

load_csv_to_db()

@app.get("/data")
def get_data(db: Session = Depends(get_db)):

    data = db.query(Health).all()

    return [
        {
            "IndicatorName": row.indicator_name,
            "Location": row.location,
            "Year": row.year,
            "NumericValue": row.numeric_value
        }
        for row in data
    ]

@app.get("/life-expectancy/{country}")
def get_life_expectancy(country: str, db: Session = Depends(get_db)):

    data = db.query(Health).filter(
        Health.location == country,
        Health.indicator_name == "Life expectancy"
    ).all()

    return [
        {"year": row.year, "value": row.numeric_value}
        for row in data
    ]




# get all indicators
@app.get("/indicators")
def get_indicators(db: Session = Depends(get_db)):

    indicators = db.query(Health.indicator_name).distinct().all()

    return {
        "indicators": sorted([indicator[0] for indicator in indicators])
    }

# get average value of indicator
@app.get("/average/{indicator}")
def get_average_indicator(indicator: str,
                          db: Session = Depends(get_db)):

    data = db.query(Health).filter(
        Health.indicator_name == indicator
    ).all()

    if not data:
        return {"message": "No data found"}

    average = sum(row.numeric_value for row in data) / len(data)

    return {
        "indicator": indicator,
        "average": round(average, 2)
    }



# top countries for a specific indicator
@app.get("/top/{indicator}")
def get_top_countries(indicator: str,
                      limit: int = 10,
                      db: Session = Depends(get_db)):

    data = db.query(Health).filter(
        Health.indicator_name == indicator
    ).order_by(Health.numeric_value.desc()).limit(limit).all()

    return [
        {
            "country": row.location,
            "year": row.year,
            "value": row.numeric_value
        }
        for row in data
    ]