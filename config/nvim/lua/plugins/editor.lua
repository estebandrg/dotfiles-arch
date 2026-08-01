return {
  {
    "windwp/nvim-autopairs",
    event = "InsertEnter",
    opts = {
      check_ts = true,
      enable_check_bracket_line = false,
    },
  },
  {
    "numToStr/Comment.nvim",
    keys = {
      { "gcc", desc = "Toggle comment line" },
      { "gbc", desc = "Toggle comment block" },
      { "gc", mode = "v", desc = "Toggle comment selection" },
    },
    opts = {},
  },
  {
    "lukas-reineke/indent-blankline.nvim",
    event = { "BufReadPre", "BufNewFile" },
    main = "ibl",
    opts = {
      indent = { char = "│" },
      scope = {
        enabled = true,
        show_start = false,
        show_end = false,
      },
    },
  },
}
