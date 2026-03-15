import pandas as pd
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Bike, KinematicPoint

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./kinematics.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def ingest_csv(file_path):
    # 1. Basic Validation: Does file exist?
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return

    # 2. Extract metadata from filename (e.g., specialized_stumpjumper_2024.csv)
    filename = os.path.basename(file_path).replace(".csv", "")
    try:
        brand, model, year = filename.split("_")
    except ValueError:
        print("Error: Filename must be in 'brand_model_year.csv' format.")
        return

    # 3. Process Data with Pandas
    df = pd.read_csv(file_path)
    
    # Ensure columns match your standard
    if not {'travel', 'ratio'}.issubset(df.columns):
        print("Error: CSV must have 'travel' and 'ratio' columns.")
        return

    db = SessionLocal()
    try:
        # 4. Create Bike Entry
        new_bike = Bike(brand=brand.capitalize(), model=model.replace("-", " ").title(), year=int(year))
        db.add(new_bike)
        db.flush() # Gets the ID for the foreign key

        # 5. Add Points
        for _, row in df.iterrows():
            point = KinematicPoint(
                bike_id=new_bike.id,
                travel=round(float(row['travel']), 2),
                leverage_ratio=round(float(row['ratio']), 3)
            )
            db.add(point)
        
        db.commit()
        print(f"Successfully ingested {brand} {model} ({len(df)} points).")
    except Exception as e:
        db.rollback()
        print(f"Failed to ingest: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    if len(sys.argv) > 1:
        ingest_csv(sys.argv[1])
    else:
        print("Usage: python ingest.py path/to/your_bike.csv")