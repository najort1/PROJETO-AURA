import { NextRequest, NextResponse } from 'next/server';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { execSync } from 'node:child_process';

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

export async function GET() {
  try {
    const projectRoot = getProjectRoot();
    const tmpIn = path.join(os.tmpdir(), `aura_status_in_${Date.now()}_${Math.random().toString(36).substring(7)}.json`);
    const tmpOut = path.join(os.tmpdir(), `aura_status_out_${Date.now()}_${Math.random().toString(36).substring(7)}.json`);

    fs.writeFileSync(tmpIn, JSON.stringify({ action: 'status' }), 'utf-8');

    try {
      const envArg = fs.existsSync(path.resolve(projectRoot, '.env')) ? '--env-file .env ' : '';
      execSync(`uv run ${envArg}python -m agent.autonomous_bridge --input-file "${tmpIn}" --output-file "${tmpOut}"`, {
        cwd: projectRoot,
        timeout: 20000,
        windowsHide: true,
        stdio: 'inherit',
      });

      if (fs.existsSync(tmpOut)) {
        const data = JSON.parse(fs.readFileSync(tmpOut, 'utf-8'));
        return NextResponse.json(data);
      }
    } finally {
      try { fs.unlinkSync(tmpIn); } catch {}
      try { fs.unlinkSync(tmpOut); } catch {}
    }

    return NextResponse.json({
      success: true,
      status: 'online',
      model: 'principal-combo',
      base_url: 'http://localhost:20128/v1',
    });
  } catch (err: any) {
    return NextResponse.json(
      { success: false, error: err.message, status: 'offline' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  const tmpIn = path.join(os.tmpdir(), `aura_chat_in_${Date.now()}_${Math.random().toString(36).substring(7)}.json`);
  const tmpOut = path.join(os.tmpdir(), `aura_chat_out_${Date.now()}_${Math.random().toString(36).substring(7)}.json`);

  try {
    const body = await request.json();
    const projectRoot = getProjectRoot();

    fs.writeFileSync(tmpIn, JSON.stringify(body), 'utf-8');

    // Executa a bridge com timeout de 2 minutos para permitir múltiplos turnos ReAct e chamadas de tools
    const envArg = fs.existsSync(path.resolve(projectRoot, '.env')) ? '--env-file .env ' : '';
    execSync(`uv run ${envArg}python -m agent.autonomous_bridge --input-file "${tmpIn}" --output-file "${tmpOut}"`, {
      cwd: projectRoot,
      timeout: 180000,
      windowsHide: true,
      stdio: 'inherit',
    });

    if (!fs.existsSync(tmpOut)) {
      throw new Error('O motor autônomo não produziu o arquivo de resposta.');
    }

    const result = JSON.parse(fs.readFileSync(tmpOut, 'utf-8'));
    return NextResponse.json(result);
  } catch (err: any) {
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
    try { fs.unlinkSync(tmpIn); } catch {}
    try { fs.unlinkSync(tmpOut); } catch {}
  }
}
