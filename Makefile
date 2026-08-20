.PHONY: install install-scripts pre-install clean

install:
	@echo "Installing AI-CLI..."
	@mkdir -p ~/.qwen/bin
	@chmod +x ~/.qwen/bin/chat-launcher.sh
	@chmod +x ~/.qwen/bin/ai-pre-launch.sh
	@chmod +x ~/.qwen/bin/chat-history.sh
	@echo "AI-CLI installed successfully!"
	@echo "Use: /home/termihoe/llama.cpp/build/bin/llama-server <modelo>"

install-scripts:
	@echo "Installing AI-CLI scripts..."
	@chmod +x bin/ai-pre-launch.sh
	@chmod +x bin/chat-launcher.sh
	@chmod +x bin/llama-wrapper.sh
	@chmod +x bin/chat-history.sh
	@echo "Scripts installed!"

pre-install:
	@mkdir -p ~/.qwen/bin
	@echo "Pre-installation complete"

clean:
	@rm -rf ~/.qwen/history.json ~/.qwen/history.json.bak
	@rm -rf ~/.ai_cli_savings ~/.ai_cli_history
	@rm -rf ~/.qwen/bin/chat-launcher.sh ~/.qwen/bin/ai-pre-launch.sh ~/.qwen/bin/chat-history.sh
	@echo "Cleaned up temporary files"
