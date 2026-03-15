from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models # This is your models.py file

app = FastAPI()

# Enable CORS so your React app can talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./kinematics.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/bikes")
def get_bikes(db: Session = Depends(get_db)):
    # Returns the list of all bikes for your sidebar/dropdown
    bikes = db.query(models.Bike).all()
    return bikes

@app.get("/kinematics/{bike_id}")
def get_kinematics(bike_id: int, db: Session = Depends(get_db)):
    # Fetches the specific X/Y points for a bike
    bike = db.query(models.Bike).filter(models.Bike.id == bike_id).first()
    if not bike:
        raise HTTPException(status_code=404, detail="Bike not found")
    
    # Format data for Recharts: [{travel: 0, ratio: 3.1}, ...]
    points = [
        {"travel": p.travel, "ratio": p.leverage_ratio} 
        for p in bike.kinematics
    ]
    return {
        "model": bike.model,
        "points": points
    }