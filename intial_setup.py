import os
import sys

# Add ORPHEUS root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.security import enroll_user, log_event
from agents.harness import AgentHarness
from voice.module import VoiceModule
import logging

# Configure logging for the CLI
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger("orpheus_cli")

text_fallback_active = True

def main_cli():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║  ORPHEUS - Omni-Responsive Processing Matrix              ║
    ║  Initial Setup & CLI                                      ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Check for master password (simulated environment variable for setupexample)
    # In a real scenario, the user would provide this via secure input.
    master_password = "local_master_key_for_orpheus"
    
    # 1. Enrollment
    print("\n>> STEP 1: INITIAL SECURITY SETUP")
    print("Checking for existing user profile...")
    
    # (In a real app, we'd check the DB. Here we simulate the enrollment.)
    # For this bootstrap, we just run the enrollment function once.
    
    print("\n>> VOICE BIOMETRIC ENROLLMENT")
    print("You will be prompted to speak for 5 seconds.")
    input("Press ENTER when ready to record...")
    
    try:
        voice_hash = enroll_user(username="Commander", master_password=master_password)
        print(f"\n[SUCCESS] User 'Commander' enrolled successfully!")
        print(f"[INFO] Voice Profile Hash: {voice_hash}")
    except Exception as e:
        logger.error(f"Enrollment failed: {e}")
        return

    # 2. Initialize Agent Harness
    print("\n>> STEP 2: INITIALIZING AGENT NETWORK")
    try:
        harness = AgentHarness()
        logger.info("Agent Harness initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize agents: {e}")
        return

    # 3. Main Loop - Voice Triggered / Text Fallback
    print("\n>> STEP 3: ORPHEUS ACTIVE - LISTENING MODE")
    print("(Voice recognition requires Faster-Whisper to be fully installed)")
    
    global text_fallback_active
    text_fallback_active = True
    
    text_cli(harness)


def handle_command(harness, command):
    """Prints the result of an agent command to the console."""
    try:
        result = harness.execute_command(command)
        print(f"\n[ORPHEUS]: {result}\n")
    except Exception as e:
        print(f"[ORPHEUS ERROR]: {e}")


def text_cli(harness):
    """Runs a simple text-based CLI if voice is unavailable."""
    print("\nText Command Interface Active. Type 'exit' to quit.")
    while True:
        try:
            user_input = input("\n> ORPHEUS: ")
            if user_input.lower() in ['exit', 'quit']:
                break
            result = harness.execute_command(user_input)
            print(f"[ORPHEUS]: {result}")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break
        except Exception as e:
            print(f"[ERROR]: {e}")

if __name__ == "__main__":
    import time
    main_cli()