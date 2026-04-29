from pydantic import BaseModel
from database import Health, get_db

app = FastAPI(title="WHO Health")

class HealthMetric(BaseModel):
    country: str
    year: int
    life_expectancy: float
    mortality_rate: float
    health_expenditure: float

# Get life expectancy for a country
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
