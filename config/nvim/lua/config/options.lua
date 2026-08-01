local opt = vim.opt

opt.number = true
opt.relativenumber = true
opt.numberwidth = 2
opt.signcolumn = "yes"
opt.tabstop = 2
opt.shiftwidth = 2
opt.expandtab = true
opt.smartindent = true
opt.wrap = false
opt.linebreak = true
opt.termguicolors = true
opt.clipboard = "unnamedplus"
opt.mouse = "a"
opt.splitright = true
opt.splitbelow = true
opt.ignorecase = true
opt.smartcase = true
opt.hlsearch = true
opt.incsearch = true
opt.swapfile = false
opt.backup = false
opt.undofile = true
opt.scrolloff = 8
opt.sidescrolloff = 8
opt.updatetime = 250
opt.timeoutlen = 400
opt.background = "dark"
opt.fillchars = { eob = " " }
opt.completeopt = { "menu", "menuone", "noselect" }

vim.g.netrw_banner = 0
vim.g.netrw_liststyle = 3
