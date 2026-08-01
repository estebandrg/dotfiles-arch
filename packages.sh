#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  DOTFILES INSTALLER — Setup your environment on any Arch-based system     ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# Usage:
#   ./install.sh              Install everything
#   ./install.sh --packages   Only install packages
#   ./install.sh --dotfiles   Only sync dotfiles
#   ./install.sh --dry-run    Show what would be done

set -euo pipefail

# ─── Colors & Styling ────────────────────────────────────────────────────────

RESET='\033[0m'
BOLD='\033[1m'
DIM='\033[2m'

RED='\033[1;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
MAGENTA='\033[1;35m'
CYAN='\033[1;36m'
WHITE='\033[1;37m'

BG_BLUE='\033[44m'
BG_CYAN='\033[46m'
BG_GREEN='\033[42m'
BG_MAGENTA='\033[45m'

# ─── Configuration ────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGES_DIR="${SCRIPT_DIR}/packages"
DRY_RUN=false
FORCE=false
INSTALL_PACKAGES=true
INSTALL_DOTFILES=true

# ─── Helpers ──────────────────────────────────────────────────────────────────

warn()  { echo -e "${YELLOW}⚠${RESET} $*"; }
error() { echo -e "${RED}✗${RESET} $*"; }
info()  { echo -e "${BLUE}→${RESET} $*"; }

hr() {
    echo -e "${DIM}$(printf '─%.0s' {1..70})${RESET}"
}

# ─── Logo ─────────────────────────────────────────────────────────────────────

show_logo() {
    clear
    echo ""
    echo -e "  ${CYAN}${BOLD}  ██████╗ ███████╗██████╗ ███████╗${RESET}"
    echo -e "  ${CYAN}${BOLD}  ██╔══██╗██╔════╝██╔══██╗██╔════╝${RESET}"
    echo -e "  ${CYAN}${BOLD}  ██║  ██║█████╗  ██████╔╝███████╗${RESET}"
    echo -e "  ${CYAN}${BOLD}  ██║  ██║██╔══╝  ██╔═══╝ ╚════██║${RESET}"
    echo -e "  ${CYAN}${BOLD}  ██████╔╝███████╗██║     ███████║${RESET}"
    echo -e "  ${CYAN}${BOLD}  ╚═════╝ ╚══════╝╚═╝     ╚══════╝${RESET}"
    echo -e "${RESET}"
    echo -e "  ${DIM}Installing required packages...${RESET}"
    echo ""
    hr
    echo ""
}

# ─── Progress Bar ─────────────────────────────────────────────────────────────

progress_bar() {
    local current=$1
    local total=$2
    local width=40
    local label="${3:-}"

    if (( total == 0 )); then
        return
    fi

    local percent=$((current * 100 / total))
    local filled=$((current * width / total))
    local empty=$((width - filled))

    local color="${RED}"
    if (( percent >= 100 )); then
        color="${GREEN}"
    elif (( percent >= 50 )); then
        color="${YELLOW}"
    fi

    printf "\r  ${DIM}[${RESET}${color}"
    printf '█%.0s' $(seq 1 "$filled" 2>/dev/null) || true
    printf "${RESET}${DIM}"
    printf '░%.0s' $(seq 1 "$empty" 2>/dev/null) || true
    printf "${RESET}${DIM}]${RESET} ${color}%3d%%${RESET}" "$percent"

    if [[ -n "$label" ]]; then
        printf " ${DIM}— %s${RESET}" "$label"
    fi

    if (( current == total )); then
        echo ""
    fi
}

# ─── Package Lists ────────────────────────────────────────────────────────────

get_package_list() {
    local file="$1"
    if [[ ! -f "$file" ]]; then
        echo ""
        return
    fi
    grep -vE '^\s*(#|$)' "$file" 2>/dev/null || echo ""
}

count_packages() {
    local file="$1"
    get_package_list "$file" | grep -c . 2>/dev/null || true
}

# ─── Install Packages ─────────────────────────────────────────────────────────

install_pacman_packages() {
    local file="${PACKAGES_DIR}/pacman.txt"
    if [[ ! -f "$file" ]]; then
        warn "No pacman.txt found"
        return
    fi

    local total
    total=$(count_packages "$file")

    if (( total == 0 )); then
        warn "No packages in pacman.txt"
        return
    fi

    echo ""
    echo -e "  ${BG_BLUE}${WHITE}${BOLD} PACMAN PACKAGES ${RESET}"
    echo ""

    local count=0
    local skipped=0
    local failed=0

    while IFS= read -r pkg; do
        ((count++)) || true
        progress_bar "$count" "$total" "$pkg"

        if $DRY_RUN; then
            continue
        fi

        if pacman -Qi "$pkg" &>/dev/null; then
            ((skipped++)) || true
            continue
        fi

        if ! sudo pacman -S --noconfirm --needed "$pkg" &>/dev/null; then
            ((failed++)) || true
        fi
    done <<< "$(get_package_list "$file")"

    echo ""
    if (( failed > 0 )); then
        warn "Failed: $failed packages"
    fi
}

install_aur_packages() {
    local file="${PACKAGES_DIR}/aur.txt"
    if [[ ! -f "$file" ]]; then
        return
    fi

    if ! command -v yay &>/dev/null; then
        warn "yay not found — skipping AUR packages"
        return
    fi

    local total
    total=$(count_packages "$file")

    if (( total == 0 )); then
        return
    fi

    echo ""
    echo -e "  ${BG_MAGENTA}${WHITE}${BOLD} AUR PACKAGES ${RESET}"
    echo ""

    local count=0
    local failed=0

    while IFS= read -r pkg; do
        ((count++)) || true
        progress_bar "$count" "$total" "$pkg"

        if $DRY_RUN; then
            continue
        fi

        if yay -Qi "$pkg" &>/dev/null; then
            continue
        fi

        if ! yay -S --noconfirm --needed "$pkg" &>/dev/null; then
            ((failed++)) || true
        fi
    done <<< "$(get_package_list "$file")"

    echo ""
    if (( failed > 0 )); then
        warn "Failed: $failed AUR packages"
    fi
}

install_flatpak_packages() {
    local file="${PACKAGES_DIR}/flatpak.txt"
    if [[ ! -f "$file" ]]; then
        return
    fi

    if ! command -v flatpak &>/dev/null; then
        warn "flatpak not found — skipping flatpak packages"
        return
    fi

    local total
    total=$(count_packages "$file")

    if (( total == 0 )); then
        return
    fi

    echo ""
    echo -e "  ${BG_GREEN}${WHITE}${BOLD} FLATPAK PACKAGES ${RESET}"
    echo ""

    local count=0
    local failed=0

    while IFS= read -r pkg; do
        ((count++)) || true
        progress_bar "$count" "$total" "$pkg"

        if $DRY_RUN; then
            continue
        fi

        if flatpak list --app --columns=application 2>/dev/null | grep -q "^${pkg}$"; then
            continue
        fi

        if ! flatpak install -y "$pkg" &>/dev/null; then
            ((failed++)) || true
        fi
    done <<< "$(get_package_list "$file")"

    echo ""
    if (( failed > 0 )); then
        warn "Failed: $failed flatpak packages"
    fi
}

# ─── Dotfiles ─────────────────────────────────────────────────────────────────

sync_dotfiles() {
    echo ""
    echo -e "  ${BG_CYAN}${WHITE}${BOLD} DOTFILES SYNC ${RESET}"
    echo ""

    local sync_script="${SCRIPT_DIR}/dotfiles.py"

    if [[ ! -f "$sync_script" ]]; then
        error "dotfiles.py not found"
        return
    fi

    local force_flag=""
    $FORCE && force_flag=" --force"

    if $DRY_RUN; then
        info "Would run: python3 ${sync_script} --apply${force_flag}"
    else
        info "Syncing dotfiles..."
        python3 "$sync_script" --apply$force_flag
    fi
}

# ─── Summary ──────────────────────────────────────────────────────────────────

show_summary() {
    echo ""
    hr
    echo ""
    echo -e "  ${WHITE}${BOLD}SUMMARY${RESET}"
    echo ""
    echo -e "  ${CYAN}Dotfiles:${RESET}  ${SCRIPT_DIR}"
    echo -e "  ${CYAN}Packages:${RESET}  ${PACKAGES_DIR}"
    echo ""
    hr
    echo ""

    if $DRY_RUN; then
        echo -e "  ${YELLOW}${BOLD}DRY RUN COMPLETE${RESET} — no changes were made"
    else
        echo -e "  ${GREEN}${BOLD}INSTALL COMPLETE${RESET} — restart your shell or run:"
        echo -e "  ${DIM}source ~/.zshrc${RESET}"
    fi
    echo ""
}

# ─── CLI ──────────────────────────────────────────────────────────────────────

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --packages)
                INSTALL_DOTFILES=false
                shift
                ;;
            --dotfiles)
                INSTALL_PACKAGES=false
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            -h|--help)
                echo "Usage: ./install.sh [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --dry-run      Show what would be done"
                echo "  --packages     Only install packages"
                echo "  --dotfiles     Only sync dotfiles"
                echo "  --force        Force re-link dotfiles"
                echo "  -h, --help     Show this help"
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
}

# ─── Main ─────────────────────────────────────────────────────────────────────

main() {
    parse_args "$@"
    show_logo

    if $DRY_RUN; then
        echo -e "  ${YELLOW}${BOLD}DRY RUN MODE${RESET} — nothing will be installed"
        echo ""
    fi

    if ! command -v pacman &>/dev/null; then
        error "pacman not found — this installer is for Arch Linux"
        exit 1
    fi

    if $INSTALL_PACKAGES; then
        install_pacman_packages
        install_aur_packages
        install_flatpak_packages
    fi

    if $INSTALL_DOTFILES; then
        sync_dotfiles
    fi

    show_summary
}

main "$@"
