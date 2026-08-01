return {
  {
    "nvim-treesitter/nvim-treesitter",
    lazy = false,
    build = ":TSUpdate",
    config = function()
      require("nvim-treesitter").setup({})

      require("nvim-treesitter").install({
        "lua",
        "vim",
        "vimdoc",
        "bash",
        "python",
        "markdown",
        "markdown_inline",
        "json",
        "yaml",
        "toml",
        "html",
        "css",
        "javascript",
        "typescript",
        "tsx",
        "sql",
        "gitcommit",
        "gitignore",
        "diff",
      })

      vim.api.nvim_create_autocmd("FileType", {
        callback = function(ev)
          local lang = vim.treesitter.language.get_lang(vim.bo[ev.buf].filetype)
          if lang and vim.treesitter.language.add(lang) then
            vim.treesitter.start(ev.buf, lang)
          end
        end,
      })
    end,
  },
}
