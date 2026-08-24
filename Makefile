.PHONY: all start-all start-backend stop-all status test clean help

# Default target starts both backend & frontend
all: start-all

# Start all services (Backend + Frontend)
start-all:
	@chmod +x start-all.sh 2>/dev/null || true
	bash start-all.sh

# Start backend server only
backend:
	cd backend && ../venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port 3094

# Start frontend server only
frontend:
	cd frontend && npm run dev

# Check services status
status:
	python3 master.py status

# Run unit tests
test:
	./venv/bin/python test_parser.py

# Stop all running services
stop-all:
	pkill -f "uvicorn server:app" 2>/dev/null || true
	pkill -f "vite" 2>/dev/null || true
	@echo "✓ Servicios detenidos."

# Clean up temporary logs and caches
clean:
	rm -f backend/server.log
	rm -rf backend/__pycache__ __pycache__ bin/__pycache__ scripts/__pycache__
	@echo "✓ Caches y logs limpiados."

# Help
help:
	@echo "Comandos AI-CLI Studio:"
	@echo "  make start-all        - Iniciar Backend (:3094) y Frontend (:5173)"
	@echo "  make status           - Ver estado de los servicios"
	@echo "  make stop-all         - Detener todos los servicios"
	@echo "  make test             - Ejecutar tests unitarios"
	@echo "  make clean            - Limpiar logs y caches temporales"
