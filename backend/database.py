import os
from sqlalchemy import create_engine, Column, Integer, Float, String, Text, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# In production (Railway) set DATA_DIR=/data to store DB on a persistent volume
_data_dir = os.getenv("DATA_DIR", os.path.dirname(os.path.abspath(__file__)))
os.makedirs(_data_dir, exist_ok=True)   # create /data if missing
DATABASE_URL = f"sqlite:///{_data_dir}/newsforge.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Report(Base):
    __tablename__ = "reports"
    id            = Column(Integer, primary_key=True, index=True)
    geo           = Column(String(10), index=True)
    created_at    = Column(DateTime, default=datetime.utcnow)
    status        = Column(String(20), default="pending")   # pending/running/done/error
    team_lead     = Column(String(200), default="")
    prev_report_id = Column(Integer, nullable=True)
    total_news    = Column(Integer, default=0)
    total_angles  = Column(Integer, default=0)
    total_headlines = Column(Integer, default=0)
    recommendations = Column(Text)   # JSON array — top-5 с обоснованием
    title           = Column(String(500), default="")   # user-defined report name
    gdocs_url       = Column(String(500), default="")   # Google Docs export URL
    is_favorite     = Column(Boolean, default=False)    # ⭐ starred by user
    data            = Column(Text)                      # full JSON blob
    vertical        = Column(String(200), default="")   # выбранная вертикаль (финансы / крипто / ...)
    keywords        = Column(Text, default="")          # свои ключевые слова под вертикаль
    output_language = Column(String(50), default="")    # язык генерации (русский / español / ...)


class NewsItem(Base):
    __tablename__ = "news_items"
    id               = Column(Integer, primary_key=True, index=True)
    report_id        = Column(Integer, index=True)
    title            = Column(String(500))
    source           = Column(String(200))
    source_type      = Column(String(50))   # top_media, local_tabloid, google_news, twitter_trend
    category         = Column(String(50))
    description      = Column(Text)
    emotional_trigger = Column(String(50))
    urgency          = Column(String(20))
    geo              = Column(String(10))
    original_url     = Column(String(500))
    published_at     = Column(DateTime, nullable=True)   # дата самой новости из источника
    created_at       = Column(DateTime, default=datetime.utcnow)


class Angle(Base):
    __tablename__ = "angles"
    id              = Column(Integer, primary_key=True, index=True)
    report_id       = Column(Integer, index=True)
    news_item_id    = Column(Integer, default=0)   # FK → news_items.id
    angle_title     = Column(String(500))
    offer_connection = Column(Text)
    target_pain     = Column(Text)
    creative_type   = Column(String(50))
    priority        = Column(String(5))
    feedback        = Column(Integer, default=0)   # -1 / 0 / 1
    created_at      = Column(DateTime, default=datetime.utcnow)


class Headline(Base):
    __tablename__ = "headlines"
    id              = Column(Integer, primary_key=True, index=True)
    report_id       = Column(Integer, index=True)
    angle_id        = Column(Integer, index=True)
    text            = Column(String(500))
    format          = Column(String(50))
    character_count = Column(Integer)
    created_at      = Column(DateTime, default=datetime.utcnow)


class RiskItem(Base):
    __tablename__ = "risks"
    id                       = Column(Integer, primary_key=True, index=True)
    report_id                = Column(Integer, index=True)
    news_title               = Column(String(500), default="")
    legal_risks              = Column(Text, default="[]")   # JSON list of strings
    platform_ban_risk        = Column(String(20), default="low")
    audience_negativity_risk = Column(String(20), default="low")
    reputation_risk          = Column(String(20), default="low")
    expiry_date              = Column(String(100), default="")
    created_at               = Column(DateTime, default=datetime.utcnow)


class Schedule(Base):
    __tablename__ = "schedules"
    id             = Column(Integer, primary_key=True, index=True)
    geo            = Column(String(10), unique=True)
    interval_hours = Column(Float, default=72.0)
    enabled        = Column(Boolean, default=False)
    last_run       = Column(DateTime, nullable=True)
    next_run       = Column(DateTime, nullable=True)
    created_at     = Column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _migrate():
    """Add new columns to existing tables without dropping data."""
    from sqlalchemy import text
    migrations = [
        "ALTER TABLE reports ADD COLUMN team_lead VARCHAR(200) DEFAULT ''",
        "ALTER TABLE reports ADD COLUMN prev_report_id INTEGER",
        "ALTER TABLE reports ADD COLUMN recommendations TEXT",
        "ALTER TABLE angles ADD COLUMN news_item_id INTEGER DEFAULT 0",
        "ALTER TABLE reports ADD COLUMN gdocs_url VARCHAR(500) DEFAULT ''",
        "ALTER TABLE reports ADD COLUMN is_favorite BOOLEAN DEFAULT 0",
        "ALTER TABLE reports ADD COLUMN title VARCHAR(500) DEFAULT ''",
        "ALTER TABLE news_items ADD COLUMN published_at DATETIME",
        "ALTER TABLE reports ADD COLUMN vertical VARCHAR(200) DEFAULT ''",
        "ALTER TABLE reports ADD COLUMN keywords TEXT DEFAULT ''",
        "ALTER TABLE reports ADD COLUMN output_language VARCHAR(50) DEFAULT ''",
    ]
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                pass  # column already exists


def init_db():
    Base.metadata.create_all(bind=engine)
    _migrate()
    # Create risks table if missing (for existing DBs)
    with engine.connect() as conn:
        try:
            conn.execute(text(
                "CREATE TABLE IF NOT EXISTS risks ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "report_id INTEGER, "
                "news_title VARCHAR(500) DEFAULT '', "
                "legal_risks TEXT DEFAULT '[]', "
                "platform_ban_risk VARCHAR(20) DEFAULT 'low', "
                "audience_negativity_risk VARCHAR(20) DEFAULT 'low', "
                "reputation_risk VARCHAR(20) DEFAULT 'low', "
                "expiry_date VARCHAR(100) DEFAULT '', "
                "created_at DATETIME)"
            ))
            conn.commit()
        except Exception:
            pass
