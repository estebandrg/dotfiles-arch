return {
  {
    "williamboman/mason.nvim",
    cmd = "Mason",
    opts = {},
  },
  {
    "williamboman/mason-lspconfig.nvim",
    dependencies = { "williamboman/mason.nvim" },
    opts = {
      ensure_installed = {
        "lua_ls",
        "pyright",
        "ts_ls",
        "bashls",
        "html",
        "cssls",
        "jsonls",
      },
    },
  },
  {
    "neovim/nvim-lspconfig",
    dependencies = {
      "williamboman/mason.nvim",
      "williamboman/mason-lspconfig.nvim",
      "hrsh7th/cmp-nvim-lsp",
    },
    config = function()
      local capabilities = require("cmp_nvim_lsp").default_capabilities()

      vim.lsp.config("*", { capabilities = capabilities })

      vim.diagnostic.config({
        virtual_text = true,
        signs = true,
        update_in_insert = false,
      })

      local map = function(keys, fn, desc)
        vim.keymap.set("n", keys, fn, { buffer = true, desc = "LSP: " .. desc })
      end

      vim.api.nvim_create_autocmd("LspAttach", {
        callback = function(args)
          local client = vim.lsp.get_client_by_id(args.data.client_id)
          if client and client.server_capabilities.documentHighlightProvider then
            vim.api.nvim_create_autocmd({ "CursorHold", "CursorHoldI" }, {
              buffer = args.buf,
              callback = vim.lsp.buf.document_highlight,
            })
            vim.api.nvim_create_autocmd({ "CursorMoved", "CursorMovedI" }, {
              buffer = args.buf,
              callback = vim.lsp.buf.clear_references,
            })
          end

          map("gd", vim.lsp.buf.definition, "Goto definition")
          map("K", vim.lsp.buf.hover, "Hover")
          map("gi", vim.lsp.buf.implementation, "Goto implementation")
          map("gr", vim.lsp.buf.references, "References")
          map("<leader>rn", vim.lsp.buf.rename, "Rename")
          map("<leader>ca", vim.lsp.buf.code_action, "Code action")
          map("<leader>f", function()
            vim.lsp.buf.format({ async = true })
          end, "Format")
        end,
      })
    end,
  },
}
