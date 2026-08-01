return {
  {
    "folke/flash.nvim",
    event = "VeryLazy",
    keys = {
      { "s", mode = { "n", "x", "o" }, function() require("flash").jump() end, desc = "Flash" },
      { "S", mode = { "n", "x", "o" }, function() require("flash").treesitter_search() end, desc = "Flash Treesitter" },
      { "r", mode = "o", function() require("flash").remote() end, desc = "Remote Flash" },
      { "R", mode = { "o", "x" }, function() require("flash").treesitter() end, desc = "Treesitter Search" },
      { "<c-s>", mode = { "c" }, function() require("flash").toggle() end, desc = "Toggle Flash Search" },
    },
    opts = {},
  },
  {
    "RRethy/vim-illuminate",
    event = "BufReadPost",
    config = function()
      require("illuminate").configure({
        providers = { "lsp", "treesitter", "regex" },
        delay = 200,
      })
    end,
  },
  {
    "RRethy/nvim-treesitter-endwise",
    event = "InsertEnter",
  },
  {
    "NMAC427/guess-indent.nvim",
    event = { "BufReadPost", "BufNewFile" },
    config = function()
      require("guess-indent").setup({})
    end,
  },
  {
    "nvimdev/dashboard-nvim",
    event = "VimEnter",
    opts = {
      theme = "hyper",
      config = {
        header = {
          "                                                 ",
          "   __      ___  _  _    ___   ___   ___   _     ",
          "   \\ \\    / (_)| || |  / _ \\ / _ \\ | \\ \\ / /    ",
          "    \\ \\/\\/ /| || || |_| (_) | (_) | | \\ V /     ",
          "     \\_/\\_/ |_||_||___|\\___/ \\___/  |_| |_|     ",
          "                                                 ",
        },
        center = {
          { desc = "Find Files", action = "Telescope find_files", key = "f" },
          { desc = "Recent Files", action = "Telescope oldfiles", key = "r" },
          { desc = "Live Grep", action = "Telescope live_grep", key = "g" },
          { desc = "File Explorer", action = "Neotree toggle", key = "e" },
          { desc = "Quit", action = "qa", key = "q" },
        },
        footer = {},
      },
    },
  },
  {
    "rcarriga/nvim-notify",
    opts = {},
  },
  {
    "folke/noice.nvim",
    dependencies = {
      "MunifTanjim/nui.nvim",
      "rcarriga/nvim-notify",
    },
    event = "VeryLazy",
    opts = {
      lsp = {
        override = {
          ["vim.lsp.util.convert_input_to_markdown_lines"] = true,
          ["vim.lsp.util.stylize_markdown"] = true,
          ["cmp.entry.get_documentation"] = true,
        },
      },
      presets = {
        bottom_search = true,
        command_palette = true,
        long_message_to_split = true,
        inc_rename = false,
        lsp_doc_border = true,
      },
    },
  },
  {
    "Bekaboo/dropbar.nvim",
    event = "VeryLazy",
    config = function()
      require("dropbar").setup({})
      local api = require("dropbar.api")
      vim.keymap.set("n", "<leader>;", api.pick, { desc = "Pick symbols in winbar" })
      vim.keymap.set("n", "[;", api.goto_context_start, { desc = "Go to start of context" })
      vim.keymap.set("n", "];", api.select_next_context, { desc = "Select next context" })
    end,
  },
}
