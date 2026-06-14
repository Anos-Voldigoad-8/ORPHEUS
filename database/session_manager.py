import sqlite3
import os
import uuid
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("orpheus_session_manager")

DB_PATH = os.path.join(os.path.dirname(__file__), "user_activity.db")

def get_connection():
    """Return a configured SQLite connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database tables if they do not exist."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table (mirroring basic info from users.json, but mostly for tracking creation/login)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    email TEXT PRIMARY KEY,
                    created_at TIMESTAMP,
                    last_login TIMESTAMP
                )
            """)
            
            # Sessions table (persistent re-login)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    email TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP,
                    last_seen TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
            
            # Activity logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT,
                    action TEXT,
                    details TEXT,
                    timestamp TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing DB: {e}")

def create_session(email: str, ip_address: str, user_agent: str = "") -> str:
    """Create a new session and return the session token."""
    token = str(uuid.uuid4())
    now = datetime.utcnow()
    expires_at = now + timedelta(days=30)  # 30 day expiration
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Ensure user profile exists
            cursor.execute("INSERT OR IGNORE INTO user_profiles (email, created_at, last_login) VALUES (?, ?, ?)", 
                           (email, now, now))
            
            # Update last_login
            cursor.execute("UPDATE user_profiles SET last_login = ? WHERE email = ?", (now, email))
            
            # Insert session
            cursor.execute("""
                INSERT INTO sessions (token, email, ip_address, user_agent, created_at, last_seen, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (token, email, ip_address, user_agent, now, now, expires_at))
            
            conn.commit()
            return token
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return None

def validate_session(token: str) -> dict:
    """Validate a session token, update last_seen, and return session data if valid."""
    now = datetime.utcnow()
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE token = ?", (token,))
            session = cursor.fetchone()
            
            if not session:
                return None
                
            expires_at = datetime.fromisoformat(session["expires_at"])
            if now > expires_at:
                # Session expired, delete it
                cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
                conn.commit()
                return None
                
            # Update last_seen
            cursor.execute("UPDATE sessions SET last_seen = ? WHERE token = ?", (now, token))
            conn.commit()
            
            return dict(session)
    except Exception as e:
        logger.error(f"Error validating session: {e}")
        return None

def revoke_session(token: str):
    """Delete a session token."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
    except Exception as e:
        logger.error(f"Error revoking session: {e}")

def log_activity(email: str, action: str, details: str = ""):
    """Log user activity."""
    now = datetime.utcnow()
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO activity_logs (email, action, details, timestamp)
                VALUES (?, ?, ?, ?)
            """, (email, action, details, now))
            conn.commit()
    except Exception as e:
        logger.error(f"Error logging activity: {e}")

def get_stats() -> dict:
    """Get system stats: total users, total logins, currently active users."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Total users
            cursor.execute("SELECT COUNT(*) FROM user_profiles")
            total_users = cursor.fetchone()[0]
            
            # Total logins (count of login actions in activity_logs)
            cursor.execute("SELECT COUNT(*) FROM activity_logs WHERE action = 'login' OR action = 'signup'")
            total_logins = cursor.fetchone()[0]
            
            # Active users (sessions active in the last 15 minutes)
            fifteen_mins_ago = datetime.utcnow() - timedelta(minutes=15)
            cursor.execute("SELECT COUNT(DISTINCT email) FROM sessions WHERE last_seen >= ?", (fifteen_mins_ago,))
            active_users = cursor.fetchone()[0]
            
            return {
                "total_users": total_users,
                "total_logins": total_logins,
                "active_users": active_users
            }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {"total_users": 0, "total_logins": 0, "active_users": 0}
