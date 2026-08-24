#!/usr/bin/env node
/**
 * Start all services (Backend + Frontend)
 */
import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '../..');

const startScript = path.join(projectRoot, 'start-all.sh');

console.log('🚀 Launching AI-CLI Services from project root...');

const child = spawn('bash', [startScript], {
  cwd: projectRoot,
  stdio: 'inherit'
});

child.on('error', (err) => {
  console.error('Failed to run start-all.sh:', err);
  process.exit(1);
});
