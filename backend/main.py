from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SQLALCHEMY_DATABASE_URL = "sqlite:///./kinematics.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/bikes")
def get_bikes(db: Session = Depends(get_db)):
    # Fetch all bikes. SQLAlchemy will automatically include the new columns 
    # like make, model, year, and the aggregated stats.
    bikes = db.query(models.Bike).all()
    return bikes

@app.get("/kinematics/{bike_id}")
def get_kinematics(bike_id: int, db: Session = Depends(get_db)):
    bike = db.query(models.Bike).filter(models.Bike.id == bike_id).first()
    if not bike:
        raise HTTPException(status_code=404, detail="Bike not found")
    
    points = [
        {
            "travel": p.travel_mm,
            "travel_percent": p.travel_percent,
            "leverage_ratio": p.leverage_ratio,
            "anti_squat_low": p.anti_squat_low,
            "anti_squat_high": p.anti_squat_high,
            "anti_rise_low": p.anti_rise_low,
            "anti_rise_high": p.anti_rise_high,
            "pedal_kickback_low": p.pedal_kickback_low,
            "pedal_kickback_high": p.pedal_kickback_high,
            "chain_growth_low": p.chain_growth_low,
            "chain_growth_high": p.chain_growth_high,
            "forces_data": p.forces_data,
            "shock_compression": p.shock_compression,
            "axle_path_x": p.axle_path_x,
            "axle_path_radius": p.axle_path_radius,
            "axle_path_steepness": p.axle_path_steepness,
        } 
        for p in bike.kinematics
    ]
    
    return {
        "metadata": {
            "id": bike.id,
            "make": bike.make,
            "model": bike.model,
            "year": bike.year,
            "design": bike.suspension_design,
            "gear_low": bike.gear_low,
            "gear_high": bike.gear_high,
            "progressivity": bike.progressivity_percent,
            "avg_antisquat": bike.avg_antisquat_pedaling,
            "avg_antirise": bike.avg_antirise_squish
        },
        "points": points
    }