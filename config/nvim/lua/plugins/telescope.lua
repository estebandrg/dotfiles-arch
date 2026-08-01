return {
  {
    "nvim-telescope/telescope.nvim",
    cmd = "Telescope",
    dependencies = {
      "nvim-lua/plenary.nvim",
      { "nvim-telescope/telescope-fzf-native.nvim", build = "make" },
      {
        "ahmedkhalf/project.nvim",
        event = "BufReadPre",
        config = function()
          require("project_nvim").setup({})
        end,
      },
    },
    keys = {
      { "<leader>ff", "<cmd>Telescope find_files<CR>", desc = "Find files" },
      { "<leader>fg", "<cmd>Telescope live_grep<CR>", desc = "Live grep" },
      { "<leader>fb", "<cmd>Telescope buffers<CR>", desc = "Find buffers" },
      { "<leader>fh", "<cmd>Telescope help_tags<CR>", desc = "Find help" },
      { "<leader>fr", "<cmd>Telescope oldfiles<CR>", desc = "Recent files" },
      { "<leader>fp", "<cmd>Telescope projects<CR>", desc = "Projects" },
      { "<leader>gc", "<cmd>Telescope git_commits<CR>", desc = "Git commits" },
    },
    config = function()
      local telescope = require("telescope")
      telescope.setup({
        defaults = {
          sorting_strategy = "ascending",
          layout_config = { prompt_position = "top" },
          file_ignore_patterns = { "node_modules", ".git", ".venv", "vendor" },
          prompt_prefix = "  ",
          selection_caret = "  ",
        },
        pickers = {
          find_files = {
            hidden = true,
            file_ignore_patterns = { "node_modules", ".git", ".venv", "vendor" },
          },
        },
      })
      telescope.load_extension("fzf")
      pcall(telescope.load_extension, "projects")
    end,
  },
}
