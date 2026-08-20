.PHONY: install install-scripts pre-install clean help

install:
	@echo "Installing AI-CLI to ~/.local/bin..."
	@mkdir -p ~/.local/bin
	@chmod +x bin/* lib/* presets/* 2>/dev/null || chmod +x bin/* lib/*
	@for f in bin/*; do \
		if [ -f "$$f" ]; then \
			ln -sf "$$(pwd)/$$f" "$$HOME/.local/bin/$$(basename "$$f")"; \
		fi \
	done
	@echo "AI-CLI binaries installed and linked successfully in ~/.local/bin!"
	@echo "Run 'ai' or 'ai-menu' to launch the TUI interface."

install-scripts:
	@echo "Configuring executable permissions..."
	@chmod +x bin/* lib/*
	@echo "Scripts configured!"

pre-install:
	@mkdir -p ~/.local/bin presets .ai_backups
	@echo "Pre-installation complete"

clean:
	@rm -rf ~/.ai_cli_savings ~/.ai_cli_history
	@echo "Cleaned up temporary and history files"

help:
	@echo "AI-CLI Makefile Targets:"
	@echo "  make install         - Link all AI-CLI tools to ~/.local/bin"
	@echo "  make install-scripts - Make all bin and lib scripts executable"
	@echo "  make clean           - Remove local cache and history"
