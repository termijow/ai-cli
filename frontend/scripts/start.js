#!/usr/bin/env node

console.log('Starting AI-CLI Frontend...');
console.log('Press Ctrl+C to stop');

import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const viteDev = spawn(
  process.argv[1],
  ['--mode', 'development', '--port', process.env.PORT || '5173'],
  {
    cwd: path.dirname(path.dirname(__dirname)),
    stdio: 'inherit'
  }
);

viteDev.on('error', (err) => {
  console.error('Failed to start frontend:', err);
  process.exit(1);
});
