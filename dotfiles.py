#!/usr/bin/env python3
"""
Dotfiles Sync — symlink your personal config over existing ones.

Manages two source trees:
  config/  → ~/.config/
  home/    → ~/

If a target file already exists, it gets backed up before being replaced.
Dry-run by default.

Requires: python-rich (install with: sudo pacman -S python-rich)
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import shutil
import sys
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

SOURCES: dict[str, dict[str, Path]] = {
    "config": {
        "src": DOTFILES_DIR / "config",
        "dst": Path.home() / ".config",
    },
    "home": {
        "src": DOTFILES_DIR / "home",
        "dst": Path.home(),
    },
}

BACKUP_ROOT = DOTFILES_DIR / ".backup"

console = Console()

# ─── Ignore Patterns ──────────────────────────────────────────────────────────


def load_ignore_patterns() -> list[str]:
    patterns = [".git", "README.md", ".gitkeep", ".syncignore"]
    ignore_file = DOTFILES_DIR / ".syncignore"
    if ignore_file.exists():
        for line in ignore_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    return patterns


IGNORE_PATTERNS = load_ignore_patterns()


def should_ignore(path: Path, src_root: Path) -> bool:
    rel = path.relative_to(src_root)
    for pattern in IGNORE_PATTERNS:
        for part in rel.parts:
            if fnmatch.fnmatch(part, pattern):
                return True
    return False


# ─── Helpers ──────────────────────────────────────────────────────────────────


def scan_source(src_root: Path) -> list[Path]:
    """Recursively scan a source directory, returning all non-ignored files."""
    if not src_root.exists():
        return []
    return sorted(
        p for p in src_root.rglob("*") if p.is_file() and not should_ignore(p, src_root)
    )


def backup_file(target: Path, category: str) -> Path:
    """Create a timestamped backup of target. Returns backup path.
    
    Does NOT remove the original — caller is responsible for cleanup.
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    rel = target.relative_to(SOURCES[category]["dst"])
    backup_path = BACKUP_ROOT / category / ts / rel
    backup_path.parent.mkdir(parents=True, exist_ok=True)

    if target.is_symlink():
        # Save where the symlink pointed so we can restore it later
        meta_path = backup_path.with_suffix(backup_path.suffix + ".symlink")
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        meta_path.write_text(os.readlink(target))
        return meta_path

    shutil.copy2(target, backup_path)
    return backup_path


def manage_file(
    src_file: Path,
    src_root: Path,
    dst_root: Path,
    category: str,
    dry: bool,
    force: bool,
) -> dict:
    """
    Process a single dotfile.
    Returns a result dict: {rel, action, detail}
    """
    rel = src_file.relative_to(src_root)
    target = dst_root / rel

    result: dict[str, str] = {"rel": str(rel), "action": "skip", "detail": ""}

    # Target doesn't exist → create symlink
    if not target.exists():
        result["action"] = "create"
        if not dry:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.symlink_to(src_file)
        return result

    # Target is already the correct symlink
    if target.is_symlink() and os.readlink(target) == str(src_file) and not force:
        result["action"] = "ok"
        result["detail"] = "already linked"
        return result

    # Target is a directory → skip
    if target.is_dir():
        result["action"] = "skip"
        result["detail"] = "target is a directory"
        return result

    # Target exists and is different (or wrong symlink, or --force)
    result["action"] = "replace"
    if not dry:
        backup_file(target, category)
        target.unlink()
        target.symlink_to(src_file)
    return result


# ─── Display ──────────────────────────────────────────────────────────────────


def display_result(result: dict, dry: bool) -> None:
    """Pretty-print a single file operation using rich."""
    action = result["action"]
    rel = result["rel"]
    detail = result.get("detail", "")

    style_map = {
        "create": "green",
        "replace": "yellow",
        "ok": "dim",
        "skip": "red",
    }

    style = style_map.get(action, "white")
    label = action.upper()

    if dry:
        label = f"[dim]DRY[/dim] {label}"

    detail_str = f" [dim]({detail})[/dim]" if detail else ""
    console.print(f"  [{style}]{label:20}[/{style}] {rel}{detail_str}")


# ─── Restore ──────────────────────────────────────────────────────────────────


def list_backups() -> None:
    """List available backups grouped by category and timestamp."""
    if not BACKUP_ROOT.exists():
        console.print("  [yellow]No backups found.[/yellow]")
        return

    for category in sorted(p.name for p in BACKUP_ROOT.iterdir() if p.is_dir()):
        snapshots = sorted(
            (p for p in (BACKUP_ROOT / category).iterdir() if p.is_dir()),
            reverse=True,
        )
        if not snapshots:
            continue
        console.print(f"\n[bold magenta]{category}/[/bold magenta]")
        for snap in snapshots:
            file_count = sum(1 for _ in snap.rglob("*") if _.is_file())
            console.print(f"  [cyan]{snap.name}[/cyan] [dim]({file_count} files)[/dim]")


def restore_backup(timestamp: str | None, dry: bool) -> None:
    """Restore files from a specific backup timestamp (or latest)."""
    if not BACKUP_ROOT.exists():
        console.print("  [yellow]No backups found.[/yellow]")
        return

    any_restored = False

    for category, paths in SOURCES.items():
        backup_dir = BACKUP_ROOT / category
        if not backup_dir.exists():
            continue

        if timestamp:
            snapshots = [backup_dir / timestamp]
        else:
            snapshots = sorted(
                [p for p in backup_dir.iterdir() if p.is_dir()],
                reverse=True,
            )[:1]

        for snap in snapshots:
            if not snap.exists():
                if timestamp:
                    console.print(f"  [red]Backup not found: {snap}[/red]")
                continue

            dst_root = paths["dst"]
            console.print(
                f"\n[bold magenta]Restoring[/bold magenta] [cyan]{category}/[/cyan] "
                f"[dim]{snap.name}[/dim] → [dim]{dst_root}[/dim]"
            )

            for backup_path in sorted(snap.rglob("*")):
                if not backup_path.is_file():
                    continue

                # .symlink files store the target path for symlinks
                if backup_path.suffix == ".symlink":
                    rel = backup_path.relative_to(snap).with_suffix("")
                    target_path = dst_root / rel
                    symlink_target = backup_path.read_text().strip()

                    if dry:
                        console.print(f"  [dim]DRY RESTORE (symlink):[/dim] {rel} → {symlink_target}")
                    else:
                        any_restored = True
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        if target_path.exists():
                            target_path.unlink()
                        target_path.symlink_to(symlink_target)
                        console.print(f"  [green]✓[/green] Restored symlink: {rel}")
                else:
                    rel = backup_path.relative_to(snap)
                    target_path = dst_root / rel

                    if dry:
                        console.print(f"  [dim]DRY RESTORE:[/dim] {rel}")
                    else:
                        any_restored = True
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(backup_path, target_path)
                        console.print(f"  [green]✓[/green] Restored: {rel}")

    if not any_restored and not dry:
        console.print("  [yellow]Nothing to restore.[/yellow]")


# ─── Clean ────────────────────────────────────────────────────────────────────


def clean_managed(dry: bool) -> None:
    """Remove managed symlinks from target dirs."""
    console.print("\n[bold magenta]Cleaning managed symlinks[/bold magenta]")

    for category, paths in SOURCES.items():
        src_root = paths["src"]
        dst_root = paths["dst"]

        if not src_root.exists():
            continue

        for src_file in scan_source(src_root):
            rel = src_file.relative_to(src_root)
            target = dst_root / rel

            if target.is_symlink() and os.readlink(target) == str(src_file):
                if dry:
                    console.print(f"  [dim]→ [DRY] Would remove:[/dim] {rel}")
                else:
                    target.unlink()
                    console.print(f"  [green]✓[/green] Removed: {rel}")


# ─── CLI ──────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="sync",
        description="Sync dotfiles — symlink your config over existing ones.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python3 sync.py                        dry-run (safe, default)
  python3 sync.py --apply                apply changes for real
  python3 sync.py --apply --force        force re-link everything
  python3 sync.py --clean                remove managed symlinks
  python3 sync.py --list-backups         show available backups
  python3 sync.py --restore              restore from latest backup
  python3 sync.py --restore 20250728_120000  restore specific backup
  python3 sync.py --home                 only sync home/ dotfiles
  python3 sync.py --config               only sync config/ dotfiles
""",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes (default is dry-run)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-link even if already linked",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove managed symlinks from target dirs",
    )
    parser.add_argument(
        "--home",
        action="store_true",
        help="Only sync home/ dotfiles",
    )
    parser.add_argument(
        "--config",
        action="store_true",
        help="Only sync config/ dotfiles",
    )
    parser.add_argument(
        "--list-backups",
        action="store_true",
        help="List available backups",
    )
    parser.add_argument(
        "--restore",
        nargs="?",
        const=None,
        default=False,
        metavar="TIMESTAMP",
        help="Restore from a backup (latest if no timestamp given)",
    )

    return parser.parse_args()


# ─── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    args = parse_args()
    dry = not args.apply

    console.print()
    console.print(
        Panel(
            "[bold white]DOTFILES SYNC[/bold white]",
            subtitle="[dim]backup & symlink[/dim]",
            border_style="cyan",
            expand=False,
        )
    )

    if dry:
        console.print(
            "  [dim]Mode: [bold]DRY-RUN[/bold] (use [cyan]--apply[/cyan] to commit)[/dim]\n"
        )
    else:
        console.print(
            "  [yellow]Mode: [bold]APPLY[/bold] (changes will be written)[/yellow]\n"
        )

    if args.list_backups:
        list_backups()
        return

    if args.restore is not False:
        restore_backup(args.restore, dry)
        if dry:
            console.print("\n  [dim]Dry-run complete. Use --apply to commit.[/dim]")
        else:
            console.print("\n  [green bold]Restore complete.[/green bold]")
        return

    if args.clean:
        clean_managed(dry)
        if dry:
            console.print("\n  [dim]Dry-run complete. Use --apply to commit.[/dim]")
        else:
            console.print("\n  [green bold]Clean complete.[/green bold]")
        return

    categories: list[str] = []
    if args.home:
        categories = ["home"]
    elif args.config:
        categories = ["config"]
    else:
        categories = list(SOURCES.keys())

    counters = {"create": 0, "replace": 0, "ok": 0, "skip": 0}

    for category in categories:
        paths = SOURCES[category]
        src_root = paths["src"]
        dst_root = paths["dst"]

        console.print(
            f"\n[bold magenta]Syncing[/bold magenta] [cyan]{category}/[/cyan] → [dim]{dst_root}[/dim]"
        )

        if not src_root.exists():
            console.print(f"  [yellow]⚠ Source not found: {src_root}[/yellow]")
            console.print(f"  [dim]→ Creating it — add dotfiles here[/dim]")
            if not dry:
                src_root.mkdir(parents=True, exist_ok=True)
            continue

        files = scan_source(src_root)
        if not files:
            console.print("  [yellow]⚠ No files found[/yellow]")
            continue

        for src_file in files:
            result = manage_file(
                src_file=src_file,
                src_root=src_root,
                dst_root=dst_root,
                category=category,
                dry=dry,
                force=args.force,
            )
            display_result(result, dry)

            action = result["action"]
            if action == "create":
                counters["create"] += 1
            elif action == "replace":
                counters["replace"] += 1
            elif action == "ok":
                counters["ok"] += 1
            elif action == "skip":
                counters["skip"] += 1

    summary = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    summary.add_column(style="bold")
    summary.add_column(justify="right")
    summary.add_row("[green]Created[/green]", str(counters["create"]))
    summary.add_row("[yellow]Replaced[/yellow]", str(counters["replace"]))
    summary.add_row("[dim]Already OK[/dim]", str(counters["ok"]))
    summary.add_row("[red]Skipped[/red]", str(counters["skip"]))

    console.print()
    console.print(
        Panel(summary, title="[bold]Summary[/bold]", border_style="white", expand=False)
    )

    if dry:
        console.print(
            "\n  [dim]Dry-run complete. Use [cyan]--apply[/cyan] to commit.[/dim]"
        )
    else:
        console.print("\n  [green bold]Sync complete.[/green bold]")

    console.print()


if __name__ == "__main__":
    main()
