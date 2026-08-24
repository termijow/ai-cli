#!/usr/bin/env node
/**
 * Start AI-CLI Frontend Server using Vite
 */
import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontendDir = path.resolve(__dirname, '..');

const port = process.env.PORT || '5173';
console.log(`Starting AI-CLI Frontend on http://localhost:${port}...`);

const vite = spawn('npx', ['vite', '--port', port, '--host'], {
  cwd: frontendDir,
  stdio: 'inherit',
  shell: true
});

vite.on('error', (err) => {
  console.error('Failed to start frontend:', err);
  process.exit(1);
});

process.on('SIGINT', () => {
  vite.kill('SIGINT');
  process.exit(0);
});

process.on('SIGTERM', () => {
  vite.kill('SIGTERM');
  process.exit(0);
});
