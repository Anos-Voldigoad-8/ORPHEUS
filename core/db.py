import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, select
from sqlalchemy.orm import declarative_base, sessionmaker
from itsdangerous import URLSafeSerializer
from dotenv import load_dotenv
import bcrypt

load_dotenv()

DATABASE_URL = os.getenv('CLOUD_DATABASE_URL') or os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError('CLOUD_DATABASE_URL or DATABASE_URL not set in .env')

# Use psycopg2 adapter for postgresql URLs
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, default='user')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), onupdate=func.now())

class Session(Base):
    __tablename__ = 'sessions'
    token = Column(String, primary_key=True, index=True)
    email = Column(String, index=True)
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))

class ActivityLog(Base):
    __tablename__ = 'activity_logs'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    action = Column(String)
    details = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

def get_user_by_email(email: str):
    with SessionLocal() as db:
        stmt = select(User).where(User.email == email)
        return db.execute(stmt).scalar_one_or_none()

def create_user(email: str, password: str, role: str = 'user'):
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    user = User(email=email, password_hash=hashed, role=role)
    with SessionLocal() as db:
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def update_last_login(email: str):
    with SessionLocal() as db:
        stmt = select(User).where(User.email == email)
        user = db.execute(stmt).scalar_one_or_none()
        if user:
            user.last_login = func.now()
            db.commit()
