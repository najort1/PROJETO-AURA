import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { execSync } from 'node:child_process';

const projectRoot = fs.existsSync(path.resolve(process.cwd(), 'agent'))
  ? process.cwd()
  : path.resolve(process.cwd(), '..');

const tmpIn = path.join(os.tmpdir(), `test_bridge_in_${Date.now()}.json`);
const tmpOut = path.join(os.tmpdir(), `test_bridge_out_${Date.now()}.json`);

fs.writeFileSync(tmpIn, JSON.stringify({ action: 'status' }), 'utf-8');

try {
  execSync(`uv run python -m agent.autonomous_bridge --input-file "${tmpIn}" --output-file "${tmpOut}"`, {
    cwd: projectRoot,
    timeout: 30000,
    windowsHide: true,
    stdio: 'inherit',
  });

  const res = JSON.parse(fs.readFileSync(tmpOut, 'utf-8'));
  console.log('Bridge Status Test Result:', res.status, res.model, res.tools_available?.length);
} finally {
  try { fs.unlinkSync(tmpIn); } catch {}
  try { fs.unlinkSync(tmpOut); } catch {}
}
