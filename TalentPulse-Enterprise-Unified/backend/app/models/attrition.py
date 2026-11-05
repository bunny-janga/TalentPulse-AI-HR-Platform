from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.session import Base

class AttritionScore(Base):
    __tablename__ = "attrition_scores"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    risk_score = Column(Float, nullable=False)  # 0.0 to 1.0 (or percentage)
    risk_band = Column(String(20), nullable=False, index=True)  # LOW, MEDIUM, HIGH
    top_factors = Column(Text, nullable=False)  # JSON list of strings/factor objects
    computed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    employee = relationship("Employee", back_populates="attrition_score")
