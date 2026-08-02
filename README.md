# 🌟 Dotfiles — mi configuración de Arch Linux

Bienvenido a mi casa de configuración 🏠. Acá vive todo lo que hace que mi sistema
**se sienta mío**: mis dotfiles, mis listas de paquetes y mis scripts de post-instalación,
todo versionado y listo para sincronizar en cualquier máquina Arch 🐧.

## 🗂️ ¿Qué hay dentro?

```
📁 dotfiles/
├── 📄 dotfiles.py              → 🪄 Sincroniza tus dotfiles (symlinks + backups)
├── 📄 packages.sh              → 📦 Instalador de paquetes (pacman + AUR + flatpak)
├── 📄 install-scripts.py       → 🚀 Orquestador de scripts de post-instalación
├── 📁 config/                  → 🔗 Va a ~/.config/
├── 📁 home/                    → 🏠 Va a tu $HOME
├── 📁 packages/                → 📝 Listas de paquetes (pacman.txt, aur.txt, flatpak.txt)
├── 📁 postinstall/             → 📜 Scripts que corren una sola vez (con memoria)
├── 📁 skills/                  → 🧠 Skills de OpenCode para este repo
└── 📁 .backup/                 → 💾 Backups de lo que reemplaza el sync (auto)
```

---

## 🪄 `dotfiles.py` — Sincronización de dotfiles

El corazón del repo. Toma tus archivos y los convierte en **symlinks** hacia tu sistema.

| Origen | Destino |
|---|---|
| `config/` | `~/.config/` |
| `home/` | `~/` |

**Modo seguro por defecto:** sin banderas, solo hace un *dry-run* (te muestra qué
pasaría sin tocar nada). Para aplicar de verdad tenés que pasar `--apply`
explícitamente. 🙅♂️

### 🚀 Uso

```bash
python3 dotfiles.py                            # 👀 Dry-run (seguro, por defecto)
python3 dotfiles.py --apply                    # ✅ Aplica los cambios de verdad
python3 dotfiles.py --apply --force            # 🔁 Re-enlaza todo aunque ya esté
python3 dotfiles.py --clean                    # 🧹 Quita los symlinks manejados
python3 dotfiles.py --home                     # 🏠 Solo sincroniza home/
python3 dotfiles.py --config                   # 🎛️ Solo sincroniza config/
python3 dotfiles.py --list-backups             # 💾 Muestra los backups disponibles
python3 dotfiles.py --restore                  # ⏪ Restaura desde el último backup
python3 dotfiles.py --restore 20250728_120000  # ⏪ Restaura un backup específico
```

### 💾 Backups automáticos

Si un archivo ya existe en el destino, el sync lo **respalda en `.backup/`** con
timestamp antes de reemplazarlo. Los symlinks se guardan como `.symlink` para poder
restaurar exactamente a dónde apuntaban. Nada se pierde. 🛟

---

## 📦 `packages.sh` — Instalador de paquetes

Instala todo tu software en una sola pasada, leyendo las listas de `packages/`:

| Lista | Gestor | Archivo |
|---|---|---|
| 🔵 Oficiales | `pacman` | `packages/pacman.txt` |
| 🟣 AUR | `yay` | `packages/aur.txt` |
| 🟢 Flatpak | `flatpak` | `packages/flatpak.txt` |

Incluye barra de progreso 📊, salta los paquetes ya instalados, y termina con un
resumen lindo. Solo para Arch (requiere `pacman`). 🐧

### 🚀 Uso

```bash
./packages.sh                       # 📦 Todo: paquetes + dotfiles
./packages.sh --packages            # 📦 Solo paquetes
./packages.sh --dotfiles            # 🪄 Solo sincronizar dotfiles
./packages.sh --dry-run             # 👀 Solo muestra lo que haría
./packages.sh --force               # 🔁 Fuerza re-enlace de dotfiles
./packages.sh --help                # ❓ Ayuda
```

---

## 🚀 `install-scripts.py` — Post-instalación con memoria

Recorre los scripts de `postinstall/` en orden numérico (ej: `10-…`, `20-…`) y los
ejecuta **una sola vez**. Recuerda lo que ya se hizo comparando el **hash del
contenido** del script (no solo su nombre): si no cambió, no lo vuelve a correr. 🧠

- ✅ Se salta lo que ya corrió con éxito
- 🔄 Lo re-corre si el script cambió (o con `--force`)
- 📝 El output en vivo se guarda en `.postinstall/logs/`
- 🎯 Filtros por nombre (`--only "*zsh*"`) o por tag (`--tag shell`)

### 🚀 Uso

```bash
python3 install-scripts.py              # 🏃 Corre todo lo pendiente
python3 install-scripts.py --list       # 📋 Solo muestra el plan
python3 install-scripts.py --dry-run    # 👀 Muestra qué ejecutaría
python3 install-scripts.py --force      # 🔁 Re-corre todo, incluso lo hecho
python3 install-scripts.py --only "*zsh*"   # 🎯 Filtra por nombre/ruta
python3 install-scripts.py --tag shell      # 🏷️ Filtra por tag
python3 install-scripts.py --reset          # 🗑️ Olvida todo el historial
python3 install-scripts.py -y --keep-going  # 🤖 Sin preguntar y sin frenar en errores
```

---

## 📁 `postinstall/` — ¿Qué son estos scripts?

Cada archivo es una tarea que se ejecuta una vez por máquina (activar un servicio,
inyectar BetterDiscord, configurar `chsh`…). Ejemplos existentes:

- `10-discord-betterdiscord.sh` → inyecta/actualiza BetterDiscord en Discord nativo vía `bdcli` 🎨

Pueden llevar metadatos en comentarios (nombre, descripción, tags) que el orquestador
usa para el plan y los filtros.

---

## 🧠 Skills de OpenCode

Este repo trae skills para que los agentes de OpenCode trabajen con las reglas del proyecto:

- `repo-rules` → reglas de oro del repo (todo cambio dentro del repo, `--apply` solo con confirmación)
- `skill-creator` → crear, editar y medir skills

---

## 🚦 Flujo típico en una máquina nueva

```bash
git clone git@github.com:estebandrg/dotfiles-arch.git
cd dotfiles-arch
./packages.sh               # 📦 paquetes
python3 install-scripts.py  # 🚀 post-instalación
python3 dotfiles.py --apply # 🪄 symlinks (ya revisaste el dry-run, ¿verdad? 😉)
```

## 📝 Licencia

Hacé lo que quieras con esto 🎁 — si te sirve, mejor.
