#!/usr/bin/env python3
"""
websocket_savings_handler.py - WebSocket endpoint for real-time savings monitoring
This script creates a WebSocket server that listens on port 1234 and provides
savings data to connected clients, including real-time token counts.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Configuration
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

SavingsFile = PROJECT_ROOT / ".ai_cli_savings"
DbFile = PROJECT_ROOT / ".ai_cli_db.db"
PORT = int(os.environ.get("WEBSOCKET_PORT", 1235))

# Token pricing (same as core.sh)
INPUT_PRICE = 0.0000050  # $0.0000050 per input token
OUTPUT_PRICE = 0.0000100  # $0.0000100 per output token


class SavingsClient:
    """A client that has connected to the WebSocket server."""
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        self.input_tokens = 0
        self.output_tokens = 0
        self.input_price = INPUT_PRICE
        self.output_price = OUTPUT_PRICE
        self.total_savings = 0.0
        self.last_message = None
        self.last_timestamp = datetime.now()

    async def handle_input(self, data: bytes):
        """Handle incoming data from a client."""
        try:
            raw_data = data.decode('utf-8').strip()
            if not raw_data:
                return

            # Parse the message
            if raw_data.startswith('{') and raw_data.endswith('}'):
                try:
                    message = json.loads(raw_data)
                    msg_type = message.get('type', '')

                    # Handle token count update
                    if msg_type == 'tokens':
                        input_tokens = message.get('input_tokens', 0)
                        output_tokens = message.get('output_tokens', 0)

                        # Calculate savings for this batch
                        batch_savings = (input_tokens * self.input_price) + (output_tokens * self.output_price)
                        
                        # Update running totals
                        self.input_tokens += input_tokens
                        self.output_tokens += output_tokens
                        self.total_savings += batch_savings

                        # Send current state to all clients
                        await self.broadcast()

                except json.JSONDecodeError:
                    pass

        except Exception:
            pass

    async def broadcast(self):
        """Send a message to all connected clients."""
        try:
            # Get current savings from file
            current_savings = 0.0
            if SavingsFile.exists():
                with open(SavingsFile, 'r') as f:
                    current_savings = float(f.read().strip())

            # Get token stats from database if available
            db_tokens = {}
            if DbFile.exists():
                try:
                    with open(DbFile, 'r') as f:
                        db_tokens = json.load(f)
                except:
                    pass

            message = {
                "type": "savings",
                "data": {
                    "total_savings": round(current_savings, 4),
                    "timestamp": datetime.now().isoformat(),
                    "tokens_in": self.input_tokens,
                    "tokens_out": self.output_tokens,
                    "input_price": self.input_price,
                    "output_price": self.output_price,
                    "db_tokens": db_tokens.get('total_tokens_in', db_tokens.get('input_tokens', 0)),
                    "db_tokens_out": db_tokens.get('total_tokens_out', db_tokens.get('output_tokens', 0)),
                    "running_total": round(self.total_savings, 4),
                    "running_tokens_in": self.input_tokens,
                    "running_tokens_out": self.output_tokens,
                }
            }

            # Send to all clients
            for client in self.clients:
                try:
                    if isinstance(client, asyncio.Task):
                        await client()
                    elif isinstance(client, SavingsClient):
                        await client.writer.write(json.dumps(message).encode('utf-8') + b'\n')
                except:
                    pass

        except Exception:
            pass

    async def send_message(self, message: dict):
        """Send a message to a single client."""
        try:
            message_json = json.dumps(message).encode('utf-8')
            self.writer.write(message_json + b'\n')
            await self.writer.drain()
        except Exception:
            pass

    async def update_tokens(self, input_tokens, output_tokens):
        """Update token counts from a new LLM call."""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        batch_savings = (input_tokens * self.input_price) + (output_tokens * self.output_price)
        self.total_savings += batch_savings
        await self.send_message({
            "type": "tokens_update",
            "data": {
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "savings": round(self.total_savings, 4),
                "delta": batch_savings,
                "timestamp": datetime.now().isoformat(),
            }
        })


class SavingsServer:
    """WebSocket server for real-time savings monitoring."""

    def __init__(self):
        self.clients: list[SavingsClient] = []
        self.running = True

    async def handle_connection(self, reader, writer):
        """Handle a new client connection."""
        client = SavingsClient(reader, writer)
        self.clients.append(client)
        print(f"Client connected: {client}", flush=True)

        try:
            while self.running:
                data = await client.handle_input(await client.reader.read(4096))
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        finally:
            self.clients.remove(client)
            print(f"Client disconnected: {client}", flush=True)
            writer.close()

    async def broadcast(self, message: dict):
        """Send a message to all connected clients."""
        if not self.clients:
            return

        message_json = json.dumps(message).encode('utf-8')
        for client in self.clients:
            try:
                await client.writer.write(message_json + b'\n')
                await client.writer.drain()
            except:
                pass

    async def send_savings_update(self):
        """Periodically send savings updates to all clients."""
        if not self.clients:
            return

        # Get current savings from file
        current_savings = 0.0
        if SavingsFile.exists():
            try:
                with open(SavingsFile, 'r') as f:
                    current_savings = float(f.read().strip())
            except:
                current_savings = 0.0

        message = {
            "type": "savings",
            "data": {
                "total_savings": round(current_savings, 4),
                "timestamp": datetime.now().isoformat(),
                "running_total": round(current_savings, 4),
            }
        }

        await self.broadcast(message)

    async def start(self):
        """Start the WebSocket server."""
        print(f"WebSocket server starting on port {PORT}...")
        print(f"Savings file: {SavingsFile}")
        print(f"Database file: {DbFile}")

        # Start periodic broadcast task
        broadcast_task = asyncio.create_task(self.send_savings_update())

        # Run server
        server = await asyncio.start_server(self.handle_connection, "0.0.0.0", PORT)

        print(f"Server listening on ws://0.0.0.0:{PORT}")
        print("Press Ctrl+C to stop")

        async with server:
            while self.running:
                await asyncio.sleep(1)

        # Cleanup
        broadcast_task.cancel()
        await broadcast_task

        print("Server stopped.")


async def main():
    server = SavingsServer()
    await server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
