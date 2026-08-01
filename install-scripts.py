#!/usr/bin/env python3
"""
Post-Install Orchestrator — recorre y ejecuta tus scripts de post-instalación.

Busca scripts en postinstall/ (uno por tarea: habilitar servicios, chsh,
oh-my-zsh, git config, lo que sea) y los corre en orden alfabético/numérico.
Recuerda cuáles ya se ejecutaron con éxito (por hash de contenido, no solo
por nombre) para no repetirlos en la próxima corrida, a menos que el script
haya cambiado o pidas --force.

El output de cada script se muestra en vivo (para que sudo, prompts, etc.
funcionen con normalidad) y también se guarda en .postinstall/logs/.

Requires: python-rich (install with: sudo pacman -S python-rich)
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
except ImportError:
    print(
        "\n  [!] python-rich is required but not installed.\n"
        "      Install it with:  sudo pacman -S python-rich\n"
    )
    sys.exit(1)

# ─── Configuration ────────────────────────────────────────────────────────────

DOTFILES_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = DOTFILES_DIR / "postinstall"
STATE_DIR = DOTFILES_DIR / ".postinstall"
STATE_FILE = STATE_DIR / "state.json"
LOG_DIR = STATE_DIR / "logs"

RUNNERS = {
    ".sh": ["bash"],
    ".bash": ["bash"],
    ".py": [sys.executable],
    ".zsh": ["zsh"],
}

console = Console()

# ─── State ────────────────────────────────────────────────────────────────────


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True))


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


# ─── Script discovery ─────────────────────────────────────────────────────────


class Script:
    def __init__(self, path: Path):
        self.path = path
        self.rel = path.relative_to(SCRIPTS_DIR)
        self.hash = file_hash(path)
        meta = self._parse_metadata()
        self.name = meta.get("name") or self._default_name()
        self.desc = meta.get("desc", "")
        self.tags = meta.get("tags", [])

    def _default_name(self) -> str:
        # "05-shell-setup.sh" -> "shell setup"
        stem = self.path.stem
        parts = stem.split("-")
        if parts and parts[0].isdigit():
            parts = parts[1:]
        return " ".join(parts) or stem

    def _parse_metadata(self) -> dict:
        """Reads simple '# key: value' header comments from the first lines."""
        meta: dict = {}
        try:
            lines = self.path.read_text(errors="ignore").splitlines()[:20]
        except OSError:
            return meta
        for line in lines:
            line = line.strip()
            if not line.startswith("#"):
                continue
            line = line.lstrip("#").strip()
            if ":" not in line:
                continue
            key, _, value = line.partition(":")
            key = key.strip().lower()
            value = value.strip()
            if key == "name":
                meta["name"] = value
            elif key == "desc":
                meta["desc"] = value
            elif key == "tags":
                meta["tags"] = [t.strip() for t in value.split(",") if t.strip()]
        return meta

    def command(self) -> list[str]:
        runner = RUNNERS.get(self.path.suffix)
        if runner:
            return runner + [str(self.path)]
        if os.access(self.path, os.X_OK):
            return [str(self.path)]
        raise ValueError(
            f"no sé cómo ejecutar '{self.rel}' "
            f"(extensión desconocida y no tiene +x)"
        )


def discover_scripts() -> list[Script]:
    if not SCRIPTS_DIR.exists():
        return []
    files = sorted(
        p for p in SCRIPTS_DIR.rglob("*")
        if p.is_file() and not p.name.startswith(".") and p.suffix != ".log"
    )
    return [Script(p) for p in files]


def matches_filters(script: Script, only: list[str], tags: list[str]) -> bool:
    if only:
        hay = any(
            fnmatch.fnmatch(str(script.rel), pat) or fnmatch.fnmatch(script.name, pat)
            for pat in only
        )
        if not hay:
            return False
    if tags:
        if not set(t.lower() for t in tags) & set(t.lower() for t in script.tags):
            return False
    return True


# ─── Execution ────────────────────────────────────────────────────────────────


def run_script(script: Script, state: dict, dry: bool) -> str:
    """Runs one script, streaming output live and logging it. Returns status."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"{script.path.stem}_{ts}.log"

    if dry:
        console.print(f"  [dim]→ [DRY] Would run:[/dim] {' '.join(script.command())}")
        return "dry"

    try:
        cmd = script.command()
    except ValueError as exc:
        console.print(f"  [red]✗ {exc}[/red]")
        return "failed"

    start = time.monotonic()
    with open(log_path, "w") as log_f:
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=DOTFILES_DIR,
                env={**os.environ, "DOTFILES_DIR": str(DOTFILES_DIR)},
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except OSError as exc:
            console.print(f"  [red]✗ No se pudo ejecutar: {exc}[/red]")
            return "failed"

        assert proc.stdout is not None
        for line in proc.stdout:
            console.print(f"  [dim]│[/dim] {line.rstrip()}")
            log_f.write(line)
        proc.wait()

    elapsed = time.monotonic() - start
    ok = proc.returncode == 0

    state[str(script.rel)] = {
        "hash": script.hash,
        "status": "done" if ok else "failed",
        "returncode": proc.returncode,
        "ran_at": ts,
        "elapsed_s": round(elapsed, 1),
        "log": str(log_path.relative_to(DOTFILES_DIR)),
    }
    save_state(state)

    if ok:
        console.print(f"  [green]✓ OK[/green] [dim]({elapsed:.1f}s)[/dim]")
        return "ok"
    else:
        console.print(
            f"  [red]✗ FAILED[/red] [dim](exit {proc.returncode}, log: {log_path.name})[/dim]"
        )
        return "failed"


def already_done(script: Script, state: dict) -> bool:
    entry = state.get(str(script.rel))
    return bool(entry) and entry.get("status") == "done" and entry.get("hash") == script.hash


# ─── Display ──────────────────────────────────────────────────────────────────


def print_plan(scripts: list[Script], state: dict) -> None:
    table = Table(box=box.SIMPLE, show_header=True, padding=(0, 2))
    table.add_column("#", style="dim", justify="right")
    table.add_column("Script", style="bold")
    table.add_column("Tags", style="cyan")
    table.add_column("Estado")

    for i, s in enumerate(scripts, start=1):
        entry = state.get(str(s.rel))
        if already_done(s, state):
            status = "[dim]ya hecho[/dim]"
        elif entry and entry.get("hash") != s.hash:
            status = "[yellow]modificado — se re-corre[/yellow]"
        elif entry and entry.get("status") == "failed":
            status = "[red]falló antes[/red]"
        else:
            status = "[green]pendiente[/green]"
        table.add_row(str(i), f"{s.name}\n[dim]{s.rel}[/dim]", ", ".join(s.tags), status)

    console.print(table)


# ─── CLI ──────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="postinstall",
        description="Ejecuta tus scripts de post-instalación, en orden, con memoria.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
ejemplos:
  python3 postinstall.py                  corre todo lo pendiente
  python3 postinstall.py --list           solo muestra el plan, no corre nada
  python3 postinstall.py --dry-run        muestra qué se ejecutaría
  python3 postinstall.py --force          re-corre todo, incluso lo ya hecho
  python3 postinstall.py --only "*zsh*"   filtra por nombre/ruta (glob)
  python3 postinstall.py --tag shell      filtra por tag
  python3 postinstall.py --reset          olvida todo el historial
""",
    )
    parser.add_argument("--list", action="store_true", help="Solo mostrar el plan")
    parser.add_argument("--dry-run", action="store_true", help="No ejecutar, solo mostrar")
    parser.add_argument("--force", action="store_true", help="Re-correr aunque ya esté hecho")
    parser.add_argument("--only", action="append", default=[], help="Filtro glob por nombre/ruta (repetible)")
    parser.add_argument("--tag", action="append", default=[], help="Filtro por tag (repetible)")
    parser.add_argument("-y", "--yes", action="store_true", help="No pedir confirmación")
    parser.add_argument("--keep-going", action="store_true", help="Seguir aunque un script falle")
    parser.add_argument("--reset", action="store_true", help="Borrar el historial de ejecución y salir")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    console.print()
    console.print(
        Panel(
            "[bold white]POST-INSTALL[/bold white]",
            subtitle="[dim]orquestador de scripts[/dim]",
            border_style="cyan",
            expand=False,
        )
    )

    if args.reset:
        if STATE_FILE.exists():
            STATE_FILE.unlink()
            console.print("  [green]✓[/green] Historial borrado.\n")
        else:
            console.print("  [dim]No había historial guardado.[/dim]\n")
        return

    if not SCRIPTS_DIR.exists():
        console.print(f"  [yellow]⚠ No existe {SCRIPTS_DIR}[/yellow]")
        console.print("  [dim]→ Creala y poné ahí tus scripts (ej: 00-shell.sh, 01-git.py)[/dim]\n")
        return

    all_scripts = discover_scripts()
    if not all_scripts:
        console.print(f"  [yellow]⚠ No hay scripts en {SCRIPTS_DIR}[/yellow]\n")
        return

    scripts = [s for s in all_scripts if matches_filters(s, args.only, args.tag)]
    if not scripts:
        console.print("  [yellow]⚠ Ningún script coincide con los filtros[/yellow]\n")
        return

    state = load_state()

    console.print(f"  [dim]{len(scripts)} script(s) encontrados en {SCRIPTS_DIR}[/dim]\n")
    print_plan(scripts, state)
    console.print()

    if args.list:
        return

    to_run = scripts if args.force else [s for s in scripts if not already_done(s, state)]

    if not to_run:
        console.print("  [green]✓ Todo al día — nada que correr.[/green]")
        console.print("  [dim]Usá --force para re-ejecutar de todos modos.[/dim]\n")
        return

    if not args.yes and not args.dry_run:
        console.print(f"  [yellow]Se van a ejecutar {len(to_run)} script(s).[/yellow]")
        answer = console.input("  [bold]¿Continuar? [y/N] [/bold]").strip().lower()
        if answer not in ("y", "yes", "s", "si", "sí"):
            console.print("  [dim]Cancelado.[/dim]\n")
            return

    counters = {"ok": 0, "failed": 0, "dry": 0}

    for i, script in enumerate(to_run, start=1):
        console.print(
            f"\n[bold magenta]▶ [{i}/{len(to_run)}][/bold magenta] "
            f"[bold]{script.name}[/bold] [dim]({script.rel})[/dim]"
        )
        if script.desc:
            console.print(f"  [dim]{script.desc}[/dim]")

        status = run_script(script, state, dry=args.dry_run)
        counters[status] = counters.get(status, 0) + 1

        if status == "failed" and not args.keep_going and not args.dry_run:
            console.print(
                "\n  [red bold]Detenido por un fallo.[/red bold] "
                "[dim](usá --keep-going para seguir pese a errores)[/dim]"
            )
            break

    summary = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    summary.add_column(style="bold")
    summary.add_column(justify="right")
    summary.add_row("[green]OK[/green]", str(counters.get("ok", 0)))
    summary.add_row("[red]Fallidos[/red]", str(counters.get("failed", 0)))
    if args.dry_run:
        summary.add_row("[dim]Dry-run[/dim]", str(counters.get("dry", 0)))

    console.print()
    console.print(Panel(summary, title="[bold]Resumen[/bold]", border_style="white", expand=False))

    if counters.get("failed", 0):
        console.print("\n  [red bold]Terminado con errores.[/red bold] Revisá los logs en .postinstall/logs/\n")
        sys.exit(1)
    else:
        console.print("\n  [green bold]Listo.[/green bold]\n")


if __name__ == "__main__":
    main()
