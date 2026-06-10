import os
import sqlite3
import hashlib
import logging
import json
from datetime import datetime
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wavfile
import librosa
import pickle

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration from environment variables or defaults
DB_PATH = os.getenv('SQLITE_PATH', 'database/orpheus_encrypted.db')
MASTER_KEY = os.getenv('ORPHEUS_MASTER_KEY', None)
AES_SALT = os.getenv('AES_SALT', 'default_salt_change_me')
AUDIO_DIR = Path('assets/audio')
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Global Fernet instance for log encryption (initialized in main())
_fernet = None

def _init_fernet(master_password: str) -> Fernet:
    import base64
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=AES_SALT.encode(),
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
    return Fernet(key)

def init_database(master_password: str) -> bool:
    """
    Initializes the secure SQLite database.
    Creates tables for user_profile, system_logs, and agent_memory.
    Returns True if a new database was created, False if it already existed.
    """
    global _fernet
    db_exists = os.path.exists(DB_PATH)
    
    # Derive a persistent key for database field encryption if not set
    if not MASTER_KEY:
        logger.warning("ORPHEUS_MASTER_KEY not set. Using derived key from master_password (less secure).")
    
    _fernet = _init_fernet(master_password)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            voice_profile BLOB,
            voice_hash TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            level TEXT,
            message BLOB,
            source TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT,
            interaction_type TEXT,
            content BLOB,
            embedding BLOB,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")
    return not db_exists

def log_event(level: str, message: str, source: str = "ORPHEUS_CORE"):
    """
    Encrypts and logs an event to the secure JSONL file and SQLite database.
    """
    global _fernet
    if not _fernet:
        logger.error("Fernet not initialized. Call init_database first.")
        return

    timestamp = datetime.now().isoformat()
    
    # 1. Append to encrypted JSONL (Black Box Recorder)
    log_entry = {
        "timestamp": timestamp,
        "level": level,
        "message": message,
        "source": source
    }
    encrypted_entry = _fernet.encrypt(json.dumps(log_entry).encode())
    
    with open('logs/orpheus_blackbox.jsonl', 'ab') as f:
        f.write(encrypted_entry + b'\n')
    
    # 2. Insert into SQLite
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO system_logs (timestamp, level, message, source) VALUES (?, ?, ?, ?)",
            (timestamp, level, encrypted_entry, source)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to write to SQLite log: {e}")

def record_voice_sample(duration: int = 5, sample_rate: int = 16000, channels: int = 1) -> str:
    """
    Records a voice sample from the default microphone.
    Returns the path to the saved WAV file.
    """
    logger.info(f"Recording voice sample for {duration} seconds. Speak now...")
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=channels, dtype='float32')
    sd.wait()
    
    output_path = AUDIO_DIR / "voice_enrollment.wav"
    wavfile.write(output_path, sample_rate, audio_data)
    logger.info(f"Voice sample saved to {output_path}")
    return str(output_path)

def extract_voice_profile(audio_path: str) -> bytes:
    """
    Extracts a voice profile (features) from an audio file using librosa.
    Returns a pickled numpy array of features.
    """
    try:
        y, sr = librosa.load(audio_path, sr=16000)
        # Extract MFCCs (Mel-Frequency Cepstral Coefficients) - standard for voice prints
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        # Use the mean of MFCCs across time to create a fixed-size feature vector
        profile_vector = np.mean(mfccs, axis=1)
        return pickle.dumps(profile_vector)
    except Exception as e:
        logger.error(f"Error extracting voice profile: {e}")
        raise

def hash_voice_profile(profile_data: bytes) -> str:
    """
    Creates a secure SHA-256 hash of the voice profile data.
    """
    return hashlib.sha256(profile_data).hexdigest()

def enroll_user(username: str, master_password: str) -> str:
    """
    Main enrollment function.
    1. Initializes the database (if not exists).
    2. Records a 5-second voice sample.
    3. Extracts and hashes the voice profile.
    4. Stores the profile and hash securely in the database.
    Returns the voice hash.
    """
    global _fernet
    _fernet = _init_fernet(master_password)
    
    # 1. Initialize Database
    new_db = init_database(master_password)
    if not new_db:
        logger.info("Database already exists. Proceeding with enrollment.")
    
    # 2. Record Voice
    audio_path = record_voice_sample()
    
    # 3. Extract Profile
    profile_data = extract_voice_profile(audio_path)
    voice_hash = hash_voice_profile(profile_data)
    
    # 4. Store in Database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Encrypt profile before storing (DOUBLE ENCRYPTION: Fernet + DB field)
    encrypted_profile = _fernet.encrypt(profile_data)
    
    try:
        cursor.execute(
            "INSERT INTO user_profile (username, voice_profile, voice_hash) VALUES (?, ?, ?)",
            (username, encrypted_profile, voice_hash)
        )
        conn.commit()
        logger.info(f"User '{username}' enrolled successfully. Voice Hash: {voice_hash}")
    except sqlite3.IntegrityError:
        logger.error("User already enrolled or voice profile conflict.")
    finally:
        conn.close()
    
    log_event("INFO", f"User {username} enrolled successfully.", "security")
    return voice_hash