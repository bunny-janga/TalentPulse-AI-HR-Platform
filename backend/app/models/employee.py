from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.session import Base

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    employee_code = Column(String(50), unique=True, index=True, nullable=False)
    job_title = Column(String(100), nullable=False)
    hire_date = Column(Date, nullable=False)
    salary = Column(Float, nullable=False)
    salary_band = Column(String(20), nullable=False)  # Low, Medium, High
    overtime_status = Column(Boolean, default=False, nullable=False)
    performance_rating = Column(Float, default=3.0, nullable=False)
    last_promotion_date = Column(Date, nullable=True)
    total_experience_years = Column(Float, default=0.0, nullable=False)
    years_at_company = Column(Float, default=0.0, nullable=False)
    location = Column(String(100), default="Visakhapatnam", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="employee_profile")
    leave_requests = relationship("LeaveRequest", back_populates="employee", cascade="all, delete-orphan")
    reviews = relationship("PerformanceReview", back_populates="employee", cascade="all, delete-orphan")
    survey_responses = relationship("SurveyResponse", back_populates="employee", cascade="all, delete-orphan")
    onboarding_tasks = relationship("OnboardingTask", back_populates="employee", cascade="all, delete-orphan")
    attrition_score = relationship("AttritionScore", back_populates="employee", uselist=False, cascade="all, delete-orphan")
