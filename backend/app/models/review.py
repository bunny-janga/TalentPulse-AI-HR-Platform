from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.session import Base

class PerformanceReview(Base):
    __tablename__ = "performance_reviews"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    review_cycle = Column(String(50), nullable=False, index=True)  # e.g., "2024-H1", "2024-H2", "2025-H1"
    rating = Column(Integer, nullable=False)  # 1 to 5
    feedback = Column(Text, nullable=True)
    strengths = Column(Text, nullable=True)
    growth_areas = Column(Text, nullable=True)
    goals = Column(Text, nullable=True)
    status = Column(String(20), default="COMPLETED", nullable=False)  # DRAFT, COMPLETED
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    employee = relationship("Employee", back_populates="reviews")
    reviewer = relationship("User")
