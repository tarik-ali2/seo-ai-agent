from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    audits = relationship("Audit", back_populates="user")


class Audit(Base):
    __tablename__ = "audits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    url = Column(String)
    audit_type = Column(String)
    status = Column(String, default="pending")  # pending, running, completed, failed
    progress = Column(Integer, default=0)
    progress_message = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="audits")
    pages = relationship("PageData", back_populates="audit")
    result = relationship("AuditResult", back_populates="audit", uselist=False)


class AuditResult(Base):
    __tablename__ = "audit_results"

    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(Integer, ForeignKey("audits.id"), unique=True)
    technical_seo = Column(JSON, nullable=True)
    pages_data = Column(JSON, nullable=True)
    suggestions = Column(JSON, nullable=True)
    gtm_guide = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    audit = relationship("Audit", back_populates="result")


class PageData(Base):
    __tablename__ = "page_data"

    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(Integer, ForeignKey("audits.id"))
    url = Column(String)
    title = Column(String, nullable=True)
    meta_description = Column(Text, nullable=True)
    h1 = Column(JSON, nullable=True)
    h2 = Column(JSON, nullable=True)
    h3 = Column(JSON, nullable=True)
    canonical = Column(String, nullable=True)
    images_without_alt = Column(JSON, nullable=True)
    internal_links = Column(JSON, nullable=True)
    schema_markup = Column(JSON, nullable=True)
    slug = Column(String, nullable=True)
    page_type = Column(String, nullable=True)
    word_count = Column(Integer, default=0)
    robots_meta = Column(String, nullable=True)
    og_tags = Column(JSON, nullable=True)
    suggestions = Column(JSON, nullable=True)

    audit = relationship("Audit", back_populates="pages")
