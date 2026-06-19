import uuid
from datetime import datetime, timedelta
import logging

from core.db import SessionLocal, Session, ActivityLog, User
from sqlalchemy import func

logger = logging.getLogger("orpheus_session_manager")

def init_db():
    """Initialize the database tables."""
    try:
        from core.db import Base, engine
        Base.metadata.create_all(bind=engine)
        logger.info("Session database mapped to Cloud ORM successfully.")
    except Exception as e:
        logger.error(f"Error initializing DB: {e}")

def create_session(email: str, ip_address: str, user_agent: str = "") -> str:
    """Create a new session and return the session token."""
    token = str(uuid.uuid4())
    now = datetime.utcnow()
    expires_at = now + timedelta(days=30)
    
    try:
        with SessionLocal() as db:
            session = Session(
                token=token,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                created_at=now,
                last_seen=now,
                expires_at=expires_at
            )
            db.add(session)
            db.commit()
            return token
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return None

def validate_session(token: str) -> dict:
    """Validate a session token, update last_seen, and return session data if valid."""
    now = datetime.utcnow()
    
    try:
        with SessionLocal() as db:
            session = db.query(Session).filter(Session.token == token).first()
            
            if not session:
                return None
                
            expires_at = session.expires_at
            if expires_at and expires_at.tzinfo:
                from datetime import timezone
                now = now.replace(tzinfo=timezone.utc)
                
            if now > expires_at:
                db.delete(session)
                db.commit()
                return None
                
            session.last_seen = func.now()
            db.commit()
            
            return {
                "token": session.token,
                "email": session.email,
                "ip_address": session.ip_address,
                "user_agent": session.user_agent,
                "created_at": session.created_at,
                "last_seen": session.last_seen,
                "expires_at": session.expires_at
            }
    except Exception as e:
        logger.error(f"Error validating session: {e}")
        return None

def revoke_session(token: str):
    """Delete a session token."""
    try:
        with SessionLocal() as db:
            db.query(Session).filter(Session.token == token).delete()
            db.commit()
    except Exception as e:
        logger.error(f"Error revoking session: {e}")

def log_activity(email: str, action: str, details: str = ""):
    """Log user activity."""
    try:
        with SessionLocal() as db:
            log = ActivityLog(email=email, action=action, details=details)
            db.add(log)
            db.commit()
    except Exception as e:
        logger.error(f"Error logging activity: {e}")

def get_stats() -> dict:
    """Get system stats: total users, total logins, currently active users."""
    try:
        with SessionLocal() as db:
            total_users = db.query(User).count()
            total_logins = db.query(ActivityLog).filter(ActivityLog.action.in_(['login', 'signup'])).count()
            
            fifteen_mins_ago = datetime.utcnow() - timedelta(minutes=15)
            active_users = db.query(Session.email).filter(Session.last_seen >= fifteen_mins_ago).distinct().count()
            
            return {
                "total_users": total_users,
                "total_logins": total_logins,
                "active_users": active_users
            }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {"total_users": 0, "total_logins": 0, "active_users": 0}
