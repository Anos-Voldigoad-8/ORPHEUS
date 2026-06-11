# ═══════════════════════════════════════════════════════════════
# ORPHEUS — Omni-Responsive Processing Matrix
# Main Server Orchestrator (FastAPI + WebSocket)
# ═══════════════════════════════════════════════════════════════

# pyrefly: ignore [missing-import]
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
# pyrefly: ignore [missing-import]
from fastapi.staticfiles import StaticFiles
# pyrefly: ignore [missing-import]
import uvicorn
import os
import logging
import asyncio
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path

# System metrics
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import ORPHEUS Core Components
try:
    from agents.harness import AgentHarness, WORKSPACE_DIR
    CORE_AVAILABLE = True
except ImportError as e:
    CORE_AVAILABLE = False
    WORKSPACE_DIR = Path("workspace")
    logging.error(f"Failed to import ORPHEUS core components: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("orpheus_main")

# ═══════════════════════════════════════════════════════════════
# Global State
# ═══════════════════════════════════════════════════════════════
agent_harness: Optional[AgentHarness] = None
start_time = time.time()

# ═══════════════════════════════════════════════════════════════
# WebSocket Connection Manager
# ═══════════════════════════════════════════════════════════════
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast a JSON message to all connected clients."""
        dead = []
        for conn in self.active_connections:
            try:
                await conn.send_json(message)
            except Exception:
                dead.append(conn)
        for d in dead:
            self.disconnect(d)

    async def send_to(self, websocket: WebSocket, message: dict):
        """Send a JSON message to a specific client."""
        try:
            await websocket.send_json(message)
        except Exception:
            pass

ws_manager = ConnectionManager()

# ═══════════════════════════════════════════════════════════════
# System Metrics
# ═══════════════════════════════════════════════════════════════
def get_system_metrics() -> dict:
    """Collect real system metrics using psutil."""
    if not PSUTIL_AVAILABLE:
        return {
            "cpu": round(5.0 + (time.time() % 10), 1),
            "ram": 45.0,
            "disk": 30.0,
            "uptime": format_uptime(time.time() - start_time),
            "cpu_count": "N/A",
            "ram_used": "N/A",
            "ram_total": "N/A",
        }

    try:
        cpu_percent = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        uptime_seconds = time.time() - start_time

        return {
            "cpu": round(cpu_percent, 1),
            "ram": round(mem.percent, 1),
            "disk": round(disk.percent, 1),
            "uptime": format_uptime(uptime_seconds),
            "cpu_count": psutil.cpu_count(),
            "ram_used": f"{mem.used // (1024**3):.1f}GB",
            "ram_total": f"{mem.total // (1024**3):.1f}GB",
        }
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        return {"cpu": 0, "ram": 0, "disk": 0, "uptime": "error"}


def format_uptime(seconds: float) -> str:
    """Format seconds into human-readable uptime."""
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    elif s < 3600:
        return f"{s // 60}m {s % 60}s"
    else:
        h = s // 3600
        m = (s % 3600) // 60
        return f"{h}h {m}m"


def get_agent_status() -> dict:
    """Get status of all agents."""
    if agent_harness:
        return {
            "commander": {"status": "active", "tasks": 0},
            "fileos": {"status": "active", "tasks": 0},
            "webresearch": {"status": "active", "tasks": 0},
            "creator": {"status": "active", "tasks": 0},
            "llm": {"status": "active", "tasks": 0},
        }
    return {
        "commander": {"status": "idle", "tasks": 0},
        "fileos": {"status": "idle", "tasks": 0},
        "webresearch": {"status": "idle", "tasks": 0},
        "creator": {"status": "idle", "tasks": 0},
        "llm": {"status": "idle", "tasks": 0},
    }


def list_workspace_files() -> list:
    """List files in the workspace directory."""
    try:
        WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
        files = []
        for item in sorted(WORKSPACE_DIR.iterdir()):
            info = {"name": item.name, "is_dir": item.is_dir()}
            if item.is_file():
                size = item.stat().st_size
                if size < 1024:
                    info["size"] = f"{size}B"
                elif size < 1024 * 1024:
                    info["size"] = f"{size / 1024:.1f}KB"
                else:
                    info["size"] = f"{size / (1024*1024):.1f}MB"
            files.append(info)
        return files
    except Exception as e:
        logger.error(f"Error listing workspace: {e}")
        return []


# ═══════════════════════════════════════════════════════════════
# Background Metrics Broadcaster
# ═══════════════════════════════════════════════════════════════
async def metrics_broadcaster():
    """Periodically broadcast system metrics to all connected clients."""
    # Give psutil a moment to initialize CPU tracking
    if PSUTIL_AVAILABLE:
        psutil.cpu_percent(interval=None)

    while True:
        await asyncio.sleep(2)
        if ws_manager.active_connections:
            metrics = get_system_metrics()
            await ws_manager.broadcast({
                "type": "metrics",
                "payload": metrics
            })


# ═══════════════════════════════════════════════════════════════
# Lifespan
# ═══════════════════════════════════════════════════════════════
@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent_harness

    logger.info("╔═══════════════════════════════════════════╗")
    logger.info("║  ORPHEUS — Omni-Responsive Processing     ║")
    logger.info("║  Matrix v2.0 Initializing...               ║")
    logger.info("╚═══════════════════════════════════════════╝")

    if CORE_AVAILABLE:
        agent_harness = AgentHarness()
        logger.info("✅ Agent Harness initialized.")
    else:
        logger.warning("⚠️ Core components not available. Running in degraded mode.")

    # Start metrics broadcaster
    metrics_task = asyncio.create_task(metrics_broadcaster())

    logger.info("🌐 ORPHEUS is online at http://localhost:8000")

    yield

    logger.info("Shutting down ORPHEUS...")
    metrics_task.cancel()
    try:
        await metrics_task
    except asyncio.CancelledError:
        pass


# ═══════════════════════════════════════════════════════════════
# FastAPI App
# ═══════════════════════════════════════════════════════════════
app = FastAPI(
    title="ORPHEUS — Omni-Responsive Processing Matrix",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# UI path
ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui")

# ═══════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def serve_root():
    """Serve the landing page."""
    landing_file = os.path.join(ui_path, "landing.html")
    if os.path.exists(landing_file):
        return FileResponse(landing_file)
    return HTMLResponse(
        "<h1>Landing page not found</h1><p>Place landing.html in the ui/ directory.</p>",
        status_code=404
    )


@app.get("/app", response_class=HTMLResponse)
async def serve_app():
    """Serve the main ORPHEUS dashboard."""
    index_file = os.path.join(ui_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return HTMLResponse(
        "<h1>ORPHEUS UI not found</h1><p>Place index.html in the ui/ directory.</p>",
        status_code=404
    )


@app.get("/health")
async def health_check():
    """System health endpoint."""
    return {
        "status": "online",
        "service": "ORPHEUS",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "core_available": CORE_AVAILABLE,
        "psutil_available": PSUTIL_AVAILABLE,
        "connected_clients": len(ws_manager.active_connections),
    }


@app.get("/api/metrics")
async def api_metrics():
    """Get current system metrics."""
    return get_system_metrics()


@app.get("/api/agents")
async def api_agents():
    """Get agent status."""
    return get_agent_status()


@app.get("/api/files")
async def api_files():
    """List workspace files."""
    return list_workspace_files()


@app.post("/api/command")
async def api_command(request: Request):
    """Execute a command via REST API."""
    try:
        body = await request.json()
        command = body.get("command", "")
    except Exception:
        command = request.query_params.get("command", "")

    if not command:
        return JSONResponse(
            {"status": "error", "message": "No command provided."},
            status_code=400
        )

    if not agent_harness:
        return JSONResponse(
            {"status": "error", "message": "Agent Harness not initialized."},
            status_code=503
        )

    try:
        result = agent_harness.execute_command(command)
        await ws_manager.broadcast({
            "type": "activity",
            "payload": {
                "icon": "⚡",
                "iconClass": "cmd",
                "text": f"REST: {command[:60]}..."
            }
        })
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Command error: {e}")
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500
        )


# ═══════════════════════════════════════════════════════════════
# WebSocket Endpoint
# ═══════════════════════════════════════════════════════════════

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)

    # Send initial status
    await ws_manager.send_to(websocket, {
        "type": "status",
        "payload": {
            "metrics": get_system_metrics(),
            "agents": get_agent_status(),
        }
    })

    # Send connection activity
    await ws_manager.broadcast({
        "type": "activity",
        "payload": {
            "icon": "🔗",
            "text": "Client connected to neural link"
        }
    })

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                # Treat plain text as a command
                data = {"type": "command", "command": raw}

            msg_type = data.get("type", "")

            if msg_type == "command":
                command = data.get("command", "").strip()
                if not command:
                    continue

                logger.info(f"WS Command: '{command}'")

                # Notify client that processing started
                await ws_manager.send_to(websocket, {
                    "type": "command_start",
                    "command": command
                })

                # Activity broadcast
                await ws_manager.broadcast({
                    "type": "activity",
                    "payload": {
                        "icon": "⚡",
                        "iconClass": "cmd",
                        "text": f"Cmd: {command[:80]}"
                    }
                })

                # Execute command
                if agent_harness:
                    try:
                        # Run in thread to avoid blocking
                        result = await asyncio.get_event_loop().run_in_executor(
                            None, agent_harness.execute_command, command
                        )
                    except Exception as e:
                        result = f"Error: {str(e)}"
                        logger.error(f"Command execution error: {e}")
                else:
                    result = (
                        "ORPHEUS Agent Harness is not initialized. "
                        "This may be due to missing dependencies. "
                        "Check the server logs for details."
                    )

                # Send result
                await ws_manager.send_to(websocket, {
                    "type": "command_response",
                    "payload": result
                })

                await ws_manager.send_to(websocket, {
                    "type": "command_complete",
                    "command": command
                })

                # Log it
                await ws_manager.broadcast({
                    "type": "log",
                    "level": "info",
                    "message": f"Executed: {command[:60]}"
                })

            elif msg_type == "get_status":
                await ws_manager.send_to(websocket, {
                    "type": "status",
                    "payload": {
                        "metrics": get_system_metrics(),
                        "agents": get_agent_status(),
                    }
                })

            elif msg_type == "list_files":
                files = list_workspace_files()
                await ws_manager.send_to(websocket, {
                    "type": "file_list",
                    "payload": files
                })

            elif msg_type == "ping":
                await ws_manager.send_to(websocket, {"type": "pong"})

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


# ═══════════════════════════════════════════════════════════════
# Static Files (mounted AFTER routes for priority)
# ═══════════════════════════════════════════════════════════════
if os.path.exists(ui_path):
    app.mount("/ui", StaticFiles(directory=ui_path), name="ui_static")
else:
    logger.warning("UI directory not found. GUI will be unavailable.")


# ═══════════════════════════════════════════════════════════════
# Entry Point
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        lifespan="on",
        log_level="info"
    )