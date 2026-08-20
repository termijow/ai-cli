---
name: ai-cli-services-startup
description: Create centralized startup script and Makefile to manage multiple backend services
source: auto-skill
extracted_at: '2026-08-20T19:45:00.000Z'
---

## Problem
User requested a command to start all services for the AI-CLI project, acknowledging there would be services for the future.

## Approach

### Step 1: Create `start-all.sh` startup script
- Made the script executable (`chmod +x`)
- Set default port to 3094 (user's preference, different from common 8080)
- Implemented colored output using ANSI escape codes for better terminal experience
- Added port availability checks using `port_in_use()` function
  - Tries `ss`, `netstat`, and `lsof` in order (platform detection)
  - Supports graceful port sharing with `wait_for_port()` loop
- Implemented service health checks using `is_service_running()` with curl
- Used `nohup` to background the uvicorn server
- Redirected logs to `/home/termihoe/Documents/ai-cli/backend/server.log`
- Added cleanup trap for graceful shutdown with `pkill -f "uvicorn server:app"`

### Step 2: Update `Makefile` with service targets
- Added targets: `all`, `backend`, `start-all`, `stop-all`, `clean`, `help`
- `make all` defaults to `start-all`
- `make backend` starts individual backend server directly
- `make stop-all` kills running uvicorn processes

### Step 3: Configuration pattern
- Uses environment variables for port (`BACKEND_PORT`) and host (`BACKEND_HOST`)
- Allows overriding defaults via command line
- Default port is 3094 (not 8080)

## Key Technical Details
- Port check uses multiple tools with fallbacks (ss > netstat > lsof)
- Uses `set -e` for exit on error in bash script
- Trap handler ensures cleanup on INT/TERM signals
- Services logged to file for debugging

## Multi-Service Startup (v2)

### Frontend Auto-Start Integration
- Added frontend server startup to start-all.sh
- FRONTEND_PORT environment variable (default 5173)
- Frontend starts with `node scripts/start.js &`
- Both backend and frontend processes tracked in services list

### Python Orchestration (`master.py`)
- Python script to start backend via start-all.sh
- Colored output for service status
- Graceful Ctrl+C handling with cleanup

### Node.js Orchestration (`frontend/scripts/all.js`)
- Uses child_process.spawn to run start-all.sh for backend
- Spawns frontend dev server with custom PORT
- Shows colored output for service status
- Ctrl+C handling for graceful shutdown

### NPM Integration
- Added "all" script to frontend/package.json
- `npm run all` starts both backend and frontend

## Future Extensions
- Add more service targets (e.g., `make frontend`, `make db`)
- Add health check endpoints for each service
- Add dependency installation targets
- Add database migration targets
- Add UI for service management in frontend
