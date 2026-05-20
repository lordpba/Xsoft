import os
import json
import logging
import asyncio
from typing import List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.core.orchestrator import Orchestrator

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("xsoft.main")

app = FastAPI(title="Xsoft Agentic Software House Backend")

# Enable CORS for the local React development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active WebSocket connections
active_connections: List[WebSocket] = []

async def broadcast(event: Dict[str, Any]):
    # Send event to all connected clients
    for connection in active_connections:
        try:
            await connection.send_json(event)
        except Exception:
            if connection in active_connections:
                active_connections.remove(connection)

# Initialize Orchestrator pointing to the parent workspace folder
WORKSPACE_DIR = "/home/mario/Scrivania/Xsoft"
orchestrator = Orchestrator(workspace_dir=WORKSPACE_DIR, broadcast_callback=broadcast)

def get_all_files(directory: str) -> Dict[str, str]:
    files_dict = {}
    if not os.path.exists(directory):
        return files_dict
        
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            # Skip virtual environments or node_modules
            if "venv" in root or "node_modules" in root or ".git" in root:
                continue
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, WORKSPACE_DIR)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    files_dict[rel_path] = f.read()
            except Exception:
                # Skip binary or unreadable files
                pass
    return files_dict

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"Client connesso al WebSocket. Connessioni attive: {len(active_connections)}")
    
    # On initial connection, send current state and all files
    try:
        # Send current state
        await websocket.send_json({
            "type": "state_update",
            "active_agent": orchestrator.active_agent,
            "agent_statuses": orchestrator.agent_statuses,
            "stats": orchestrator.stats,
            "current_project": orchestrator.current_project
        })
        
        # Send all files in workspace (wiki and newly written code)
        files = get_all_files(os.path.join(WORKSPACE_DIR, "wiki"))
        # Add frontend code if they exist
        app_jsx_path = os.path.join(WORKSPACE_DIR, "frontend/src/App.jsx")
        app_css_path = os.path.join(WORKSPACE_DIR, "frontend/src/App.css")
        
        if os.path.exists(app_jsx_path):
            try:
                with open(app_jsx_path, "r") as f:
                    files["frontend/src/App.jsx"] = f.read()
            except Exception:
                pass
        if os.path.exists(app_css_path):
            try:
                with open(app_css_path, "r") as f:
                    files["frontend/src/App.css"] = f.read()
            except Exception:
                pass

        await websocket.send_json({
            "type": "all_files",
            "files": files
        })
        
    except Exception as e:
        logger.error(f"Errore durante l'handshake iniziale del client: {e}")

    try:
        while True:
            # Receive actions from the frontend
            data = await websocket.receive_text()
            event = json.loads(data)
            logger.info(f"Ricevuto evento dal client: {event}")
            
            action = event.get("action")
            
            if action == "start_project":
                project_name = event.get("project_name", "Todo App")
                # Run the project simulation in the background
                asyncio.create_task(orchestrator.run_project_simulation(project_name))
                
            elif action == "submit_ticket":
                ticket_desc = event.get("ticket_desc", "")
                # Run the support hotfix loop in the background
                asyncio.create_task(orchestrator.run_ticket_simulation(ticket_desc))
                
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.info(f"Client disconnesso dal WebSocket. Connessioni attive: {len(active_connections)}")
    except Exception as e:
        logger.error(f"Errore nel ciclo di ascolto WebSocket: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
