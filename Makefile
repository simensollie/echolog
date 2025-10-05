# Echolog - Audio Recording Application Makefile

.PHONY: help install test clean dev-setup start stop status files devices

# Default target
help:
	@echo "Echolog - Audio Recording Application"
	@echo "====================================="
	@echo ""
	@echo "Available targets:"
	@echo "  install     - Install dependencies in virtual environment"
	@echo "  dev-setup   - Set up development environment"
	@echo "  test        - Run test recording (1-minute segments)"
	@echo "  clean       - Clean up temporary files and recordings"
	@echo "  start       - Start recording (requires SESSION_ID)"
	@echo "               Variables: TIME_LIMIT=30m LIMIT_BOUNDARY=end-segment TEST=true"
	@echo "  stop        - Stop current recording"
	@echo "  status      - Show recording status and files"
	@echo "  files       - List all recording files"
	@echo "  devices     - List available audio devices"
	@echo "  help        - Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make install"
	@echo "  make test"
	@echo "  make start my_meeting"
	@echo "  make start test_session TEST=true"

# Install dependencies
install:
	@echo "Installing dependencies..."
	python -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt
	@echo "✅ Dependencies installed successfully!"
	@echo "To activate: source .venv/bin/activate"

# Development setup
dev-setup: install
	@echo "Setting up development environment..."
	@echo "✅ Development environment ready!"
	@echo "To activate: source .venv/bin/activate"

# Test recording (1-minute segments)
test:
	@echo "Starting test recording with 1-minute segments..."
	@echo "Press Ctrl+C to stop"
	.venv/bin/python echolog.py start --session-id "test_$(shell date +%Y%m%d_%H%M%S)" --test

# Start recording (supports both SESSION_ID=name and make start name)
start:
	@ARGS="$(filter-out start,$(MAKECMDGOALS))"; \
	if [ -z "$$ARGS" ]; then \
		echo "❌ Error: Session name required"; \
		echo "Usage: make start my_session_name [TIME_LIMIT]"; \
		echo "For test mode: make start my_session_name TEST=true"; \
		exit 1; \
	fi
	@SESSION_NAME=$$(set -- $$ARGS; echo $$1); \
	SHORT_TL=$$(set -- $$ARGS; echo $$2); \
	echo "Starting recording: $$SESSION_NAME"; \
	CMD=".venv/bin/python echolog.py start --session-id \"$$SESSION_NAME\""; \
	if [ -n "$$SHORT_TL" ]; then CMD="$$CMD --time-limit $$SHORT_TL"; fi; \
	if [ -n "$(TIME_LIMIT)" ]; then CMD="$$CMD --time-limit $(TIME_LIMIT)"; fi; \
	if [ -n "$(LIMIT_BOUNDARY)" ]; then CMD="$$CMD --limit-boundary $(LIMIT_BOUNDARY)"; fi; \
	if [ "$(TEST)" = "true" ]; then CMD="$$CMD --test"; fi; \
	echo "Command: $$CMD"; \
	sh -c "$$CMD"

# Allow targets to be passed as arguments
%:
	@:

# Stop recording
stop:
	@echo "Stopping recording..."
	.venv/bin/python echolog.py stop

# Show status
status:
	.venv/bin/python echolog.py status

# List files
files:
	.venv/bin/python echolog.py files

# List devices
devices:
	.venv/bin/python echolog.py devices

# Clean up
clean:
	@echo "Cleaning up..."
	rm -rf .venv
	rm -rf test_recordings
	rm -rf __pycache__
	rm -f *.pyc
	rm -f .coverage
	@echo "✅ Cleanup complete!"

# Quick test (short duration)
quick-test:
	@echo "Starting quick test (30 seconds, 10-second segments)..."
	@echo "This will create test_recordings/ directory"
	.venv/bin/python test_ffmpeg.py

# Debug ffmpeg
debug:
	@echo "Running ffmpeg debug script..."
	./debug_ffmpeg.sh

# Show configuration
config:
	@echo "Current configuration:"
	@cat echolog.conf

# Update dependencies
update-deps:
	@echo "Updating dependencies..."
	.venv/bin/pip install --upgrade -r requirements.txt
	@echo "✅ Dependencies updated!"

# Run all tests
test-all: devices test
	@echo "Running comprehensive test..."
	@echo "1. Testing device detection..."
	.venv/bin/python echolog.py devices
	@echo "2. Testing file listing..."
	.venv/bin/python echolog.py files
	@echo "✅ All tests completed!"

# Show help for specific target
help-install:
	@echo "Install dependencies in a virtual environment"
	@echo "Usage: make install"

help-test:
	@echo "Run a test recording with 1-minute segments"
	@echo "Usage: make test"

help-start:
	@echo "Start recording with a session name"
	@echo "Usage: make start my_session_name"
	@echo "Test mode: make start my_session_name TEST=true"

# Check if virtual environment exists
check-env:
	@if [ ! -d ".venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi

# Ensure virtual environment is activated
ensure-env: check-env
	@echo "✅ Virtual environment found"

# Default session ID for testing
DEFAULT_SESSION ?= test_$(shell date +%Y%m%d_%H%M%S)

# Show current status
info:
	@echo "Echolog Status:"
	@echo "==============="
	@echo "Virtual environment: $(if $(wildcard .venv),✅ Found,❌ Not found)"
	@echo "ffmpeg: $(shell which ffmpeg > /dev/null && echo "✅ Found" || echo "❌ Not found")"
	@echo "Python: $(shell python --version 2>/dev/null || echo "❌ Not found")"
	@echo "Recordings directory: $(shell echo ~/recordings)"
	@echo ""
	@if [ -d ".venv" ]; then \
		echo "To activate virtual environment: source .venv/bin/activate"; \
	fi
