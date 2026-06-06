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


# ── Google Search Console ──────────────────────────────────────────────────────

class GSCCredential(Base):
    """OAuth tokens per user — one row per connected account."""
    __tablename__ = "gsc_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    access_token = Column(Text)
    refresh_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime, nullable=True)
    connected_at = Column(DateTime, default=datetime.utcnow)


class GSCReport(Base):
    """One row per GSC audit job — stores all fetched data + analysis."""
    __tablename__ = "gsc_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    property_url = Column(String)
    status = Column(String, default="running")     # running | completed | failed
    progress = Column(Integer, default=0)
    progress_message = Column(String, default="")

    # Raw GSC data
    overview = Column(JSON, nullable=True)          # {clicks, impressions, ctr, position, date_range}
    top_queries = Column(JSON, nullable=True)       # [{query, clicks, impressions, ctr, position}]
    top_pages = Column(JSON, nullable=True)         # [{page, clicks, impressions, ctr, position}]
    date_trend = Column(JSON, nullable=True)        # [{date, clicks, impressions, ctr, position}]
    device_breakdown = Column(JSON, nullable=True)  # [{device, clicks, impressions, ctr, position}]
    period_comparison = Column(JSON, nullable=True) # {current: {...}, previous: {...}}

    # Detected issues
    opportunities = Column(JSON, nullable=True)     # page-2 keyword opportunities
    declining_pages = Column(JSON, nullable=True)   # pages losing clicks
    ctr_opportunities = Column(JSON, nullable=True) # high impressions, low CTR

    # AI analysis
    ai_insights = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


# ── Tools ─────────────────────────────────────────────────────────────────────

class TrackedKeyword(Base):
    """Keywords the user wants to monitor position for via GSC."""
    __tablename__ = "tracked_keywords"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    keyword = Column(String)
    site_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
