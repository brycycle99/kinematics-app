from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Bike(Base):
    __tablename__ = "bikes"
    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String)
    model = Column(String)
    year = Column(Integer)
    # Relationship to the curve data
    kinematics = relationship("KinematicPoint", back_populates="bike", cascade="all, delete-orphan")

class KinematicPoint(Base):
    __tablename__ = "kinematic_points"
    id = Column(Integer, primary_key=True, index=True)
    bike_id = Column(Integer, ForeignKey("bikes.id"))
    travel = Column(Float)
    leverage_ratio = Column(Float)
    bike = relationship("Bike", back_populates="kinematics")