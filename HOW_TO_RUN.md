# How to Run ORPHEUS

## Step 1: Install Dependencies

Navigate to the `ORPHEUS` directory and install the requirements:

```bash
cd ORPHEUS
pip install -r requirements.txt
```

Note: `pyaudio`, `Coqui TTS`, and `Faster-Whisper` may require specific system libraries (like PortAudio for PyAudio, or C++ compilers for some dependencies). Please ensure you have a compatible environment (Python 3.11+).

## Step 2: Configure Environment

Copy the environment template and fill in your values. For a basic local run, the defaults should be fine:

```bash
cp .env.template .env
```

## Step 3: Run ORPHEUS

### Option A: Full System (Main Orchestrator)
This starts the FastAPI server (hosting the UI) and attempts to initialize the voice module:

```bash
python main.py
```
Then open your browser to `http://localhost:8000` to see the dashboard.

### Option B: CLI Setup (First Run / Text-Based)
If you want to perform the first-time enrollment or use the text-based CLI (if voice dependencies are not installed):

```bash
python intial_setup.py
```

## Step 4: Interact with ORPHEUS

### Via Voice (if Voice Module initialized):
Say "Orpheus" followed by a command. Examples:
- "Orpheus search latest news in technology"
- "Orpheus read file my_notes.txt"
- "Orpheus list files"

### Via the Web Interface:
Open `http://localhost:8000` in your browser. The dashboard will display live system metrics and agent statuses. You can also trigger the `/command` API endpoint directly via a tool like `curl` or a REST client.

Example `curl`:
```bash
curl -X POST "http://localhost:8000/command?command=search+latest+technology+news"
```

### Via the Text CLI (if Voice Module fails):
Simply type your requests when prompted. Type `exit` to quit.

## Step 5: Explore the Workspace

All files created by ORPHEUS (e.g., by the File OS Agent or Creator Agent) will be stored in the `workspace/` directory.