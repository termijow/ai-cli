.PHONY: start-backend start-all stop-all clean help

# Default target
all: start-all

# Start backend server
backend:
	cd backend && uvicorn server:app --host 0.0.0.0 --port 3094

# Start all services (currently only backend)
start-all:
	@chmod +x start-all.sh 2>/dev/null || true
	bash start-all.sh

# Stop all services
stop-all:
	pkill -f "uvicorn server:app" 2>/dev/null || true
	echo "Stopped all services"

# Clean up
clean:
	rm -f backend/server.log
	rm -f ~/.ai_cli_savings ~/.ai_cli_history
	echo "Cleaned up"

# Help
help:
	@echo "AI-CLI Services Commands:"
	@echo "  make all              - Start all services (default)"
	@echo "  make backend          - Start backend server only"
	@echo "  make start-all        - Start all services using startup script"
	@echo "  make stop-all         - Stop all running services"
	@echo "  make clean            - Clean up logs and cache"
	@echo "  make help             - Show this help message"
