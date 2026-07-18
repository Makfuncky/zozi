const { exec, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const webAppDir = path.join(__dirname, '..', 'web_app');

// Clear the dev build cache once at startup. With the webpack filesystem
// cache re-enabled in next.config.ts, a stale/corrupted `.next`
// (from a previous parallel-compile run) is what caused the original
// "Cannot find module" / missing route-manifest errors. A clean
// clear before a single dev server starts avoids that without the
// per-request recompile penalty of config.cache=false.
function clearNextCache() {
  const nextDir = path.join(webAppDir, '.next');
  try {
    if (fs.existsSync(nextDir)) {
      fs.rmSync(nextDir, { recursive: true, force: true });
      console.log('Cleared stale .next cache for a clean dev start.');
    }
  } catch (e) {
    console.warn('Could not clear .next cache:', e.message);
  }
}

function killProcessesOnPort(port) {
  const killCmd = `for /f "tokens=5" %p in ('netstat -ano ^| findstr :${port}') do taskkill /F /PID %p 2>nul`;
  exec(killCmd, { shell: true });
}

// Kill processes on ports before starting
killProcessesOnPort(3000);
killProcessesOnPort(3001);

// Clear stale dev cache (corruption guard for the re-enabled
// webpack filesystem cache).
clearNextCache();

// Ensure dev mode: a stray NODE_ENV=production in the environment makes
// `next dev` apply the production webpack config (which drops the dev CSS
// loader and breaks global CSS compilation). Force dev for the dev server.
delete process.env.NODE_ENV;

setTimeout(() => {
  console.log('Starting Next.js dev server...');
  
  const cmd = `cd /d "${webAppDir}" && npx next dev --port 3000`;
  exec(cmd, { shell: true, stdio: 'inherit' });
}, 2000);

setTimeout(() => {
  console.log('Server should be starting...');
}, 100);