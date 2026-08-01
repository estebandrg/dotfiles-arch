#!/usr/bin/env bash
# name: Discord + BetterDiscord
# desc: Inyecta/actualiza BetterDiscord en Discord nativo vía bdcli
# tags: discord, betterdiscord
#
# Contexto:
# - Discord nativo (AUR: discord-latest-bin) se auto-instala en
#   ~/.config/discord/<version>/ y es ahí donde bdcli lo detecta (sin sudo).
# - En el primer arranque el bootstrap descarga Discord a ~/.config/discord/;
#   este script lo lanza en background y espera a que se inicialice.
# - Requiere bdcli (AUR: bdcli-bin) para la inyección.
# - BetterDiscord guarda sus datos en ~/.config/BetterDiscord (runtime, no va al repo).
# - El tema catppuccin macchiato vive como dotfile en config/BetterDiscord/themes/.
# - Idempotente: si ya hay inyección, no vuelve a correr.

set -euo pipefail

DISCORD_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/discord"

log() { printf "  \033[1m[%s]\033[0m %s\n" "$1" "$2"; }
info() { log "·" "$1"; }
ok()   { log "OK" "$1"; }
warn() { log "!" "$1"; }

if ! command -v bdcli &>/dev/null; then
    warn "bdcli no está instalado (AUR: bdcli-bin) — no se puede inyectar"
    exit 0
fi

if [ ! -d "$DISCORD_DIR" ] || ! find "$DISCORD_DIR" -maxdepth 6 -name core.asar 2>/dev/null | grep -q .; then
    if ! command -v discord &>/dev/null; then
        warn "discord-latest-bin no está instalado — instalalo primero"
        exit 0
    fi
    info "Discord no inicializado — lanzándolo en background para que se descargue..."
    discord &>/dev/null &
    for _ in $(seq 1 30); do
        if find "$DISCORD_DIR" -maxdepth 6 -name core.asar 2>/dev/null | grep -q .; then
            break
        fi
        sleep 5
    done
    if find "$DISCORD_DIR" -maxdepth 6 -name core.asar 2>/dev/null | grep -q .; then
        ok "Discord inicializado"
    else
        warn "No se pudo inicializar Discord (¿red/display?) — abrí la app una vez y re-corré el script"
        exit 0
    fi
fi

injected=$(find "$DISCORD_DIR" -maxdepth 6 -path "*discord_desktop_core*" -name index.js \
    2>/dev/null -exec grep -il betterdiscord {} + | head -1)
if [ -n "$injected" ]; then
    ok "BetterDiscord ya inyectado ($injected)"
else
    info "Inyectando BetterDiscord"
    bdcli install
fi
