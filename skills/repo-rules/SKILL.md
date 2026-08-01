---
name: repo-rules
description: "Working rules of the dotfiles repository (this project's philosophy). Trigger whenever the user wants to create, modify, remove or sync system configuration in this project: dotfiles, files under ~/.config or $HOME (.zshrc, .gitconfig, themes), packages (pacman/AUR/flatpak), or post-install scripts. Also trigger on mentions of dotfiles.py, sync, --apply, symlinks, or 'syncing the configuration'. Golden rule: EVERY change happens inside the repository (config/, home/, packages/, postinstall/), NEVER directly on the real system; and --apply only runs with explicit confirmation after reviewing the dry-run. Use this skill whenever the user asks to change, add, remove or sync system configuration in this dotfiles project, even when they reference ~/.config or $HOME paths directly."
---

# repo-rules — Dotfiles repository philosophy

This repository is the single source of truth for this system's configuration. Everything you configure here is what persists: the real files in `~/.config/`, `~/`, the installed packages and the post-install scripts are just *results* managed from this repo.

The purpose of this skill is that when the user wants to change something about the system, you ALWAYS do it inside the repository, and the real system stays untouched unless the user explicitly asks and after seeing what will happen.

## Why work only inside the repo

- If you hand-edit `~/.config/kitty/kitty.conf`, that change is lost the next time the system is restored or the repo is re-cloned. The repo is what survives.
- The real files are usually symlinks pointing into the repo. Writing "behind the symlink" breaks consistency and can leave the system in a state the repo does not reflect.
- The repo versions everything with git, so any change can be reviewed and reverted.

## Repo → system mapping

| In the repo | Links to / affects |
|---|---|
| `config/<app>/...` | `~/.config/<app>/...` |
| `home/.zshrc`, `home/.gitconfig`, ... | `~/.zshrc`, `~/.gitconfig`, ... |
| `packages/pacman.txt` | packages installed with pacman |
| `packages/aur.txt` | packages installed with yay (AUR) |
| `packages/flatpak.txt` | apps installed with flatpak |
| `postinstall/` | scripts run by scripts-orchestrator.py |

## How to act on configuration change requests

When the user asks to change, add or remove system configuration:

1. **Figure out which part of the repo** the change maps to (table above).
2. **Edit the file inside the repo**, never the real system file.
3. If the change targets a path the repo does not cover, **do not edit the system**: tell the user that file is not versioned and offer to import it into the repo (copy it into `config/` or `home/` and then sync).
4. If the user mentions a `~/.config` or `$HOME` path, **translate it automatically** to its repo equivalent before editing.

Translation examples:
- "change the kitty theme" → edit `config/kitty/kitty.conf`
- "add an alias to my zsh" → edit `home/.zshrc`
- "install neovim" → add `neovim` to `packages/pacman.txt` (do not run `sudo pacman -S neovim`)
- "set a black background in waybar" → edit `config/waybar/...`

## dotfiles.py and the danger of --apply

`dotfiles.py` syncs the repo to the system:
- `config/` → `~/.config/`
- `home/` → `~/`

Default mode: **dry-run** (`python3 dotfiles.py`), which only shows what it would do without touching anything. Safe.

`--apply` is **dangerous**: it backs up and **replaces** real system files with symlinks into the repo. It can overwrite local configuration that was not in the repo (though it stays backed up in `.backup/`).

Rules for `--apply` (HARD RULES, never bend them):

- **`--apply` and `--clean` are strictly manual.** The agent NEVER runs them on its own initiative, and NEVER as an indirect consequence of another request.
- The dry-run is ONLY the dry-run. Saying "haz el dry-run", "intenta el dry-run", or asking to configure something (a theme, an alias, a file) is NOT authorization to apply. After the dry-run, the agent STOPS and asks.
- The ONLY valid authorizations are: (1) the user writes an explicit command to apply in their own message (e.g. "ejecuta --apply", "aplica", "sincroniza ahora") AFTER seeing the dry-run plan; or (2) the user explicitly picks the "apply" option in response to the agent's "¿aplico?" question — still only after showing the dry-run.
- A `permission.ask` result on the `dotfiles.py` command is a technical gate, NOT user authorization. If the tool asks for permission, the agent still stops and asks the user in plain language; it never treats the permission prompt as consent to run `--apply`.
- If there is any doubt between "apply" and "don't apply", the answer is **don't apply**.
- If the dry-run shows files that will be **replaced** (not already-correct symlinks), clearly point out which ones will be replaced: that is where local config is most easily lost.

## General rules

- When in doubt, prefer touching the repo: it is easier to revert a repo change than to repair an overwritten real file.
- Reading real system files to inspect them is fine. Writing, deleting or moving real system files is not, unless that is exactly what the user asked for.
- If a change requires touching the real system some other way (e.g. restarting a service), say so first and only do it with confirmation.
