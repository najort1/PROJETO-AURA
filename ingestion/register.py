"""Registro e manifesto versionado de dados brutos com integridade SHA-256.

Gera data/manifests/anac.json (ou outro manifesto via --manual) mapeando
cada arquivo a seu hash, tamanho, data de modificação e licença de proveniência.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from datetime import UTC
from pathlib import Path

from aura_core.log import get_logger
from aura_core.paths import ROOT, ensure_dir, path

logger = get_logger("ingestion.register")

CHUNK_SIZE = 1024 * 1024  # 1 MiB


def compute_sha256(file_path: Path, chunk_size: int = CHUNK_SIZE) -> str:
    """Calcula o hash SHA-256 de um arquivo lendo em blocos de memória delimitados."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def _format_iso(timestamp: float) -> str:
    """Formata timestamp POSIX em ISO 8601 UTC."""
    return dt.datetime.fromtimestamp(timestamp, tz=UTC).isoformat()


def load_existing_manifest(manifest_path: Path) -> dict[str, dict]:
    """Carrega manifesto pré-existente indexado por caminho relativo, se houver."""
    if not manifest_path.exists():
        return {}
    try:
        with open(manifest_path, encoding="utf-8") as f:
            data = json.load(f)
        files = data.get("files", [])
        if isinstance(files, list):
            return {item["path"]: item for item in files if "path" in item}
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning(f"Não foi possível ler manifesto anterior {manifest_path}: {exc}")
    return {}


def register_tree(
    source_dir: Path,
    manifest_path: Path,
    source_name: str = "Portal de Dados Abertos ANAC",
    license_name: str = "CC BY-ND 3.0 / Política de Dados Abertos (Decreto nº 8.777/2016)",
    method: str = "manual",
) -> dict:
    """Varre diretório, calcula SHA-256 em stream e persiste manifesto JSON."""
    if not source_dir.exists():
        raise FileNotFoundError(f"Diretório fonte não encontrado: {source_dir}")

    ensure_dir(manifest_path.parent)
    existing_entries = load_existing_manifest(manifest_path)

    all_files = sorted(p for p in source_dir.rglob("*") if p.is_file())
    total_files = len(all_files)
    logger.info(
        f"Iniciando registro de {total_files} arquivos em '{source_dir.relative_to(ROOT)}'..."
    )

    manifest_entries: list[dict] = []
    total_bytes = 0
    now_iso = dt.datetime.now(tz=UTC).isoformat()

    for idx, file_path in enumerate(all_files, start=1):
        rel_path = file_path.relative_to(ROOT).as_posix()
        stat = file_path.stat()
        size_bytes = stat.st_size
        mtime_iso = _format_iso(stat.st_mtime)
        total_bytes += size_bytes

        sha256_hash = compute_sha256(file_path)

        prev = existing_entries.get(rel_path)
        # Preserva data de registro original caso o conteúdo não tenha mudado
        if prev and prev.get("sha256") == sha256_hash:
            registered_at = prev.get("registered_at", now_iso)
        else:
            registered_at = now_iso

        entry = {
            "path": rel_path,
            "sha256": sha256_hash,
            "size_bytes": size_bytes,
            "mtime": mtime_iso,
            "method": method,
            "source": source_name,
            "license": license_name,
            "registered_at": registered_at,
        }
        manifest_entries.append(entry)

        if idx % 100 == 0 or idx == total_files:
            logger.info(
                f"Progresso: {idx}/{total_files} arquivos processados ({total_bytes / (1024**2):.1f} MB)..."
            )

    # Manter metadados de execução com deterministic timestamp se arquivos não mudaram
    all_same = len(existing_entries) == len(manifest_entries) and all(
        existing_entries.get(e["path"], {}).get("sha256") == e["sha256"] for e in manifest_entries
    )
    if all_same and manifest_path.exists():
        try:
            with open(manifest_path, encoding="utf-8") as f:
                old_meta = json.load(f).get("_meta", {})
            generated_at = old_meta.get("generated_at", now_iso)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning(
                f"Meta do manifesto anterior ilegível ({manifest_path}): {exc}; "
                "usando timestamp novo."
            )
            generated_at = now_iso
    else:
        generated_at = now_iso

    manifest_data = {
        "_meta": {
            "source": source_name,
            "license": license_name,
            "total_files": total_files,
            "total_bytes": total_bytes,
            "generated_at": generated_at,
            "method": method,
        },
        "files": manifest_entries,
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)

    logger.info(
        f"Manifesto salvo com sucesso em '{manifest_path.relative_to(ROOT)}' "
        f"({total_files} arquivos, {total_bytes / (1024**3):.2f} GB)."
    )
    return manifest_data


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Registra arquivos brutos no manifesto de integridade e proveniência."
    )
    parser.add_argument(
        "--manual",
        nargs="?",
        const="data/raw/_manual",
        default=None,
        help="Caminho para snapshot manual alternativo (default: data/raw/_manual)",
    )
    parser.add_argument(
        "--source-dir",
        default="data/raw/anac",
        help="Diretório fonte para os dados ANAC (default: data/raw/anac)",
    )
    parser.add_argument(
        "--output",
        default="data/manifests/anac.json",
        help="Arquivo JSON do manifesto a ser gerado (default: data/manifests/anac.json)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.manual:
        source_target = path(args.manual)
        out_target = (
            path(args.output)
            if args.output != "data/manifests/anac.json"
            else path("data/manifests/manual.json")
        )
        source_name = "Snapshot manual complementar"
        license_name = "Conforme documentação da fonte específica"
        register_tree(
            source_dir=source_target,
            manifest_path=out_target,
            source_name=source_name,
            license_name=license_name,
            method="manual",
        )
    else:
        source_target = path(args.source_dir)
        out_target = path(args.output)
        register_tree(
            source_dir=source_target,
            manifest_path=out_target,
            source_name="Portal de Dados Abertos ANAC",
            license_name="CC BY-ND 3.0 / Política de Dados Abertos (Decreto nº 8.777/2016)",
            method="manual",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
