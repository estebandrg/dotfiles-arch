# Project Instructions for OpenCode Agents

This repository is a dotfiles & system configuration project containing dotfiles, package lists, post-install scripts, and local OpenCode skills.

## Project Architecture & Scripts

- **Dotfiles Sync (`dotfiles.py`)**:
  - Manages `config/` → `~/.config/` and `home/` → `~/`.
  - Runs in dry-run mode by default (`python3 dotfiles.py`). Use `python3 dotfiles.py --apply` to commit changes.
  - Root repo entries (such as `skills/`, `.opencode/`, `dotfiles.py`) are project files and should not be placed inside `config/` or `home/` unless meant to be symlinked to `$HOME`.

## Regla crítica: `--apply` es ESTRICTAMENTE manual

`python3 dotfiles.py --apply` (y `--clean`) **JAMÁS** se ejecuta por iniciativa del agente, ni como
consecuencia indirecta de otra petición. Aplicar cambios al sistema real es un acto **exclusivamente
manual** del usuario, y requiere UNO de estos dos casos (y solo estos):

1. El usuario escribe explícitamente y por sí mismo un mensaje ordenando aplicar el sync
   (p. ej. "ejecuta `--apply`", "aplica los cambios", "sincroniza ahora"), **después** de haber visto
   el plan del dry-run.
2. En respuesta a la pregunta del agente ("¿aplico?"), el usuario elige la opción de aplicar de forma
   inequívoca — y aun así, solo tras mostrarle el dry-run y sus archivos a reemplazar.

**Prohibido explícitamente:**
- Ejecutar `--apply` porque el usuario pidió algo *parecido* (instalar un tema, crear un archivo,
  "sincroniza mi config") sin una orden literal de aplicar.
- Ejecutar `--apply` porque el usuario dijo "haz el dry-run" o "intenta el dry-run": eso es SOLO el dry-run.
- Encadenar el dry-run con el `--apply` en la misma operación o turno sin una confirmación manual
  separada y explícita.
- Aprovechar que la config tiene `permission.ask` para "colar" el `--apply`: el permiso técnico nunca
  sustituye a la orden explícita del usuario.

Si el usuario no ha dicho literalmente "aplica", el agente se detiene después del dry-run y pregunta.
Cuando haya duda entre "aplicar" y "no aplicar", la respuesta correcta es **no aplicar**.

- **Package Installer (`packages.sh`)**:
  - Manages Arch pacman (`packages/pacman.txt`), AUR (`packages/aur.txt`), and Flatpak (`packages/flatpak.txt`).
  - Supports `--dry-run`, `--packages`, `--dotfiles`, `--force`.

- **Post-Install Orchestrator (`scripts-orchestrator.py`)**:
  - Discovers and runs scripts in `postinstall/` with hash tracking and logging in `.postinstall/`.

## Local Skills & Skill Triggers

Project skills are registered in `opencode.json` under `"skills": { "paths": ["skills", ".opencode/skills"] }`.

### Skill Triggers

- **`repo-rules`**:
  - **Trigger when**: The user wants to change, add, remove or sync system configuration in this project — dotfiles, files under `~/.config` or `$HOME`, packages, post-install scripts — or mentions `dotfiles.py`, `--apply`, symlinks or "syncing configuration". Enforces the golden rule: every change happens inside the repo, never on the real system.
  - **Path**: `skills/repo-rules/SKILL.md`

- **`skill-creator`**:
  - **Trigger when**: The user wants to create, edit, test, evaluate, benchmark, optimize, or package OpenCode skills in this repository (e.g., "crear skill", "modificar skill", "crea una skill para...", "correr evals de skill").
  - **Path**: `skills/skill-creator/SKILL.md`

- **`customize-opencode`**:
  - **Trigger when**: Editing or creating OpenCode configs (`opencode.json`, `.opencode/`, `~/.config/opencode/`), creating or fixing OpenCode agents, subagents, skills, plugins, MCP servers, or permission rules.

- **`find-skills`**:
  - **Trigger when**: Searching for external/installable skills or extending OpenCode capabilities.

## Operational Rules

1. Always use `--dry-run` or dry mode first when testing dotfiles sync or package script execution.
2. `--dry-run` nunca es autorización para `--apply` (ver "Regla crítica" arriba).
3. Ensure project-level skills stay inside `skills/` or `.opencode/skills/` without interfering with `dotfiles.py` symlink targets.
