# If you come from bash you might have to change your $PATH.
# export PATH=$HOME/bin:/usr/local/bin:$PATH

export ZSH="$HOME/.oh-my-zsh"

ZSH_THEME="agnosterzak"

plugins=(
    git
    archlinux
    zsh-autosuggestions
    zsh-syntax-highlighting
)

source $ZSH/oh-my-zsh.sh

# oh-my-zsh exporta LS_COLORS, que tiene precedencia sobre el theme de eza.
# Lo desactivamos para que eza use su theme.yml (config/eza/theme.yml).
unset LS_COLORS LSCOLORS

# Check archlinux plugin commands here
# https://github.com/ohmyzsh/ohmyzsh/tree/master/plugins/archlinux

# Display Pokemon-colorscripts
# Project page: https://gitlab.com/phoneybadger/pokemon-colorscripts#on-other-distros-and-macos
#pokemon-colorscripts --no-title -s -r #without fastfetch
#pokemon-colorscripts --no-title -s -r | fastfetch -c $HOME/.config/fastfetch/config-pokemon.jsonc --logo-type file-raw --logo-height 10 --logo-width 5 --logo -

# fastfetch. Will be disabled if above colorscript was chosen to install
fastfetch -c $HOME/.config/fastfetch/config-compact.jsonc

# Set-up eza (ls replacement) with icons and the catppuccin theme
alias ls='eza --icons'
alias l='eza -l --icons'
alias la='eza -la --icons'
alias lla='eza -la --icons'
alias lt='eza --tree --icons'
alias ll='eza -l --icons --header'

# Set-up FZF key bindings (CTRL R for fuzzy history finder)
source <(fzf --zsh)
export PATH="$HOME/.local/bin:$HOME/go/bin:$PATH"
eval "$(zoxide init zsh)"

HISTFILE=~/.zsh_history
HISTSIZE=10000
SAVEHIST=10000
setopt appendhistory

# Ensure new interactive shells do not start inside the Hyprland-Dots repo.
if [[ -o interactive && "${SHLVL:-1}" -eq 1 && "$PWD" == "$HOME/Arch-Hyprland/Hyprland-Dots" ]]; then
  cd "$HOME"
fi

# mise (dev environment manager)
if command -v mise &>/dev/null; then
  eval "$(mise activate zsh)"
fi

# dotfiles sync (usa el venv del repo, que trae python-rich)
alias dotfiles="$HOME/dotfiles/.venv/bin/python $HOME/dotfiles/dotfiles.py"
