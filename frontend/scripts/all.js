#!/usr/bin/env node
/**
 * Start all services (backend + frontend)
 */

const { spawn } = require('child_process');
const path = require('path');
const { fileURLToPath } = require('url');

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('\n🚀 Starting AI-CLI Services...\n');

// Start backend server
console.log('📦 Starting Backend Server...');
const backend = spawn(
  'bash',
  ['start-all.sh'],
  {
    cwd: '/home/termihoe/Documents/ai-cli',
    stdio: ['inherit', 'inherit', 'inherit']
  }
);

backend.on('error', (err) => {
  console.error('Failed to start backend:', err);
  process.exit(1);
});

backend.on('close', (code) => {
  if (code !== 0) {
    console.error('Backend server failed to start');
    process.exit(code);
  }
});

// Start frontend server (in background)
console.log('🎨 Starting Frontend Server...');
const frontend = spawn(
  process.argv[1],
  ['--mode', 'development', '--port', process.env.PORT || '5173'],
  {
    cwd: '/home/termihoe/Documents/ai-cli/frontend',
    stdio: ['inherit', 'inherit', 'inherit']
  }
);

frontend.on('error', (err) => {
  console.error('Failed to start frontend:', err);
  process.exit(1);
});

console.log('\n✅ All services started successfully!\n');
console.log('Services:');
console.log('  - Backend Server: http://localhost:3094');
console.log('  - Frontend Server: http://localhost:5173\n');
console.log('Press Ctrl+C to stop all services.');
