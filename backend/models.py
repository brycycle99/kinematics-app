from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Bike(Base):
    __tablename__ = "bikes"
    id = Column(Integer, primary_key=True, index=True)
    make = Column(String)
    model = Column(String)
    year = Column(Integer)
    suspension_design = Column(String)
    
    # Metadata for the specific gears used in the simulation
    gear_low = Column(String)   # e.g., "32x51" (Climbing/Pedaling gear)
    gear_high = Column(String)  # e.g., "32x10" (Descending gear)
    
    # Aggregated Metrics
    avg_antisquat_pedaling = Column(Float) # 20-40% travel (using low gear)
    progressivity_percent = Column(Float)  # (Start - End) / Start
    avg_antirise_squish = Column(Float)    # 40-100% travel (using high gear)
    
    kinematics = relationship("KinematicCurve", back_populates="bike", cascade="all, delete-orphan")

class KinematicCurve(Base):
    __tablename__ = "kinematic_curves"
    id = Column(Integer, primary_key=True, index=True)
    bike_id = Column(Integer, ForeignKey("bikes.id"))
    
    # Standard metrics
    travel_mm = Column(Float)
    travel_percent = Column(Float)
    leverage_ratio = Column(Float)
    
    # Semantic Gear Metrics
    anti_squat_low = Column(Float)
    anti_squat_high = Column(Float)
    anti_rise_low = Column(Float)
    anti_rise_high = Column(Float)
    pedal_kickback_low = Column(Float)
    pedal_kickback_high = Column(Float)
    chain_growth_low = Column(Float)
    chain_growth_high = Column(Float)
    
    forces_data = Column(JSON)
    shock_compression = Column(Float)

    axle_path_x = Column(Float)
    axle_path_radius = Column(Float)
    axle_path_steepness = Column(Float)
    
    # Store the 30+ geometry coordinates as a JSON dictionary
    geometry_data = Column(JSON) 

    bike = relationship("Bike", back_populates="kinematics")