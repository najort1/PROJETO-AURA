import { NextRequest, NextResponse } from 'next/server';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { spawn } from 'node:child_process';

function getProjectRoot(): string {
  if (fs.existsSync(path.resolve(process.cwd(), 'agent'))) {
    return process.cwd();
  }
  const parent = path.resolve(process.cwd(), '..');
  if (fs.existsSync(path.resolve(parent, 'agent'))) {
    return parent;
  }
  return process.cwd();
}

function killProcessTree(pid: number | undefined): Promise<void> {
  return new Promise((resolve) => {
    if (!pid) return resolve();
    if (process.platform === 'win32') {
      const killer = spawn('taskkill', ['/PID', pid.toString(), '/T', '/F'], {
        windowsHide: true,
        stdio: 'ignore',
      });
      killer.on('close', () => resolve());
      killer.on('error', () => {
        try {
          process.kill(pid);
        } catch {}
        resolve();
      });
    } else {
      try {
        process.kill(-pid, 'SIGKILL');
      } catch {
        try {
          process.kill(pid, 'SIGKILL');
        } catch {}
      }
      resolve();
    }
  });
}

interface RunBridgeOptions {
  command: string;
  args: string[];
  cwd: string;
  timeoutMs?: number;
  signal?: AbortSignal;
}

function runBridgeProcess({ command, args, cwd, timeoutMs = 180000, signal }: RunBridgeOptions): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      const abortErr = new Error('Operação cancelada pelo cliente.');
      abortErr.name = 'AbortError';
      return reject(abortErr);
    }

    const child = spawn(command, args, {
      cwd,
      windowsHide: true,
      stdio: ['ignore', 'pipe', 'pipe'],
    });

    let stdoutTail = '';
    let stderrTail = '';
    const MAX_TAIL_CHARS = 4096;

    let isSettled = false;
    let timer: NodeJS.Timeout | null = null;

    const cleanup = () => {
      if (timer) {
        clearTimeout(timer);
        timer = null;
      }
      if (signal && onAbort) {
        signal.removeEventListener('abort', onAbort);
      }
    };

    const settleReject = (err: Error) => {
      if (isSettled) return;
      isSettled = true;
      cleanup();
      reject(err);
    };

    const settleResolve = () => {
      if (isSettled) return;
      isSettled = true;
      cleanup();
      resolve();
    };

    const onAbort = () => {
      if (isSettled) return;
      const abortErr = new Error('Operação cancelada pelo cliente.');
      abortErr.name = 'AbortError';
      settleReject(abortErr);
      killProcessTree(child.pid).catch(() => {});
    };

    if (signal) {
      signal.addEventListener('abort', onAbort, { once: true });
    }

    if (timeoutMs > 0) {
      timer = setTimeout(() => {
        if (isSettled) return;
        const timeoutErr = new Error(
          `O motor autônomo excedeu o tempo limite de ${Math.round(timeoutMs / 1000)}s.`
        );
        timeoutErr.name = 'TimeoutError';
        settleReject(timeoutErr);
        killProcessTree(child.pid).catch(() => {});
      }, timeoutMs);
    }

    child.stdout?.on('data', (chunk: Buffer) => {
      process.stdout.write(chunk);
      stdoutTail += chunk.toString('utf-8');
      if (stdoutTail.length > MAX_TAIL_CHARS) {
        stdoutTail = stdoutTail.slice(-MAX_TAIL_CHARS);
      }
    });

    child.stderr?.on('data', (chunk: Buffer) => {
      process.stderr.write(chunk);
      stderrTail += chunk.toString('utf-8');
      if (stderrTail.length > MAX_TAIL_CHARS) {
        stderrTail = stderrTail.slice(-MAX_TAIL_CHARS);
      }
    });

    child.on('error', (err: Error) => {
      settleReject(err);
    });

    child.on('close', (code: number | null, closeSignal: NodeJS.Signals | null) => {
      if (isSettled) return;

      if (code === 0) {
        settleResolve();
      } else {
        const errorDetail =
          stderrTail.trim() ||
          stdoutTail.trim() ||
          (closeSignal ? `Finalizado por sinal ${closeSignal}` : `Código de saída ${code}`);
        const procErr = new Error(
          `Falha na execução do motor autônomo (código ${code}): ${errorDetail}`
        );
        settleReject(procErr);
      }
    });
  });
}

const DEFAULT_TOOLS = [
  'consultar_cliente_360',
  'consultar_historico_atritos_voos',
  'consultar_regras_regulamento',
  'conceder_milhas_cortesia',
  'emitir_voucher_servico',
  'propor_acao_retencao_kanban',
  'escalar_atendimento_vip',
  'listar_clientes_em_risco_ou_atrito',
];

export async function GET() {
  const rawBaseUrl = process.env.AURA_LLM_BASE_URL || 'http://localhost:20128/v1';
  const baseUrl = rawBaseUrl.replace(/\/+$/, '');
  const model = process.env.AURA_LLM_MODEL || 'principal-combo';

  let status: 'online' | 'offline' = 'offline';

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

    const probeUrl = `${baseUrl}/models`;
    const response = await fetch(probeUrl, {
      method: 'GET',
      signal: controller.signal,
      headers: process.env.AURA_LLM_API_KEY
        ? { Authorization: `Bearer ${process.env.AURA_LLM_API_KEY}` }
        : {},
    });

    clearTimeout(timeoutId);

    if (response.ok) {
      status = 'online';
    } else if (![401, 403].includes(response.status)) {
      // Alguns gateways OpenAI-compat (ex.: Cloudflare Workers AI, Gemini)
      // respondem 404/405 em GET /models. Qualquer resposta HTTP autenticada
      // prova que o serviço está alcançável e credenciado -> online.
      // 401/403 = credencial rejeitada -> permanece offline.
      status = 'online';
    }
  } catch {
    status = 'offline';
  }

  return NextResponse.json({
    success: true,
    status,
    model,
    base_url: rawBaseUrl,
    tools_available: DEFAULT_TOOLS,
  });
}

export async function POST(request: NextRequest) {
  const tmpIn = path.join(os.tmpdir(), `aura_chat_in_${Date.now()}_${Math.random().toString(36).substring(7)}.json`);
  const tmpOut = path.join(os.tmpdir(), `aura_chat_out_${Date.now()}_${Math.random().toString(36).substring(7)}.json`);

  try {
    const body = await request.json();
    const projectRoot = getProjectRoot();

    await fs.promises.writeFile(tmpIn, JSON.stringify(body), 'utf-8');

    // Executa a bridge de forma assíncrona com timeout de 3 minutos e cancelamento via AbortSignal
    // Resolve o interpretador Python do Concierge:
    // 1) Python do venv do projeto (.venv) — criado pelo `uv sync` no dev e
    //    presente na imagem Docker de produção. Evita depender do binário `uv`
    //    em runtime (requisito essencial para deploys cloud, ex.: Render).
    // 2) Fallback: `uv run python` (ambiente de desenvolvimento local).
    const isWindows = process.platform === 'win32';
    const venvPython = path.join(
      projectRoot,
      '.venv',
      isWindows ? 'Scripts' : 'bin',
      isWindows ? 'python.exe' : 'python'
    );
    const useVenv = fs.existsSync(venvPython);

    const command = useVenv ? venvPython : 'uv';
    const prefixArgs = useVenv
      ? []
      : fs.existsSync(path.resolve(projectRoot, '.env'))
        ? ['run', '--env-file', '.env']
        : ['run'];
    const args = [
      ...prefixArgs,
      '-m',
      'agent.autonomous_bridge',
      '--input-file',
      tmpIn,
      '--output-file',
      tmpOut,
    ];

    await runBridgeProcess({
      command,
      args,
      cwd: projectRoot,
      timeoutMs: 180000,
      signal: request.signal,
    });

    if (!fs.existsSync(tmpOut)) {
      throw new Error('O motor autônomo não produziu o arquivo de resposta.');
    }

    const fileContent = await fs.promises.readFile(tmpOut, 'utf-8');
    const result = JSON.parse(fileContent);
    return NextResponse.json(result);
  } catch (err: any) {
    if (request.signal.aborted || err?.name === 'AbortError') {
      return NextResponse.json(
        {
          success: false,
          error: 'Requisição cancelada pelo cliente.',
          reply: 'A geração de resposta foi interrompida pelo operador.',
        },
        { status: 499 }
      );
    }

    console.error('Erro em POST /api/concierge/chat:', err);
    return NextResponse.json(
      {
        success: false,
        error: err.message || 'Erro inesperado na execução do Aura Concierge.',
        reply: 'Desculpe, ocorreu uma instabilidade ao conectar com o motor autônomo do Concierge. Verifique se o serviço local do modelo está ativo em http://localhost:20128/v1.',
      },
      { status: 500 }
    );
  } finally {
    try { await fs.promises.unlink(tmpIn); } catch {}
    try { await fs.promises.unlink(tmpOut); } catch {}
  }
}
