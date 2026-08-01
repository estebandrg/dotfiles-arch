return {
  {
    "nvim-neo-tree/neo-tree.nvim",
    branch = "v3.x",
    dependencies = {
      "nvim-lua/plenary.nvim",
      "nvim-tree/nvim-web-devicons",
      "MunifTanjim/nui.nvim",
    },
    keys = {
      { "<leader>e", "<cmd>Neotree toggle<CR>", desc = "Toggle file explorer" },
      { "<leader>E", "<cmd>Neotree focus<CR>", desc = "Focus file explorer" },
    },
    opts = {
      close_if_last_window = true,
      sources = { "filesystem", "buffers", "git_status" },
      window = {
        width = 32,
        mappings = {
          ["<space>"] = "none",
        },
      },
      filesystem = {
        follow_current_file = { enabled = true },
        use_libuv_file_watcher = true,
        filtered_items = {
          visible = false,
          hide_dotfiles = false,
          hide_gitignored = true,
        },
      },
      default_component_configs = {
        indent = { with_expanders = true },
        git_status = { symbols = { added = "", modified = "", deleted = "" } },
      },
    },
  },
}
