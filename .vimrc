set nocompatible

set autochdir                 "set pwd to directory of current file"
set hidden

"*** Console UI & Text display ***"
set visualbell
set number
set mouse=a                   "use a mouse in the console"
set ruler
set lazyredraw
set list
set listchars=tab:»\ ,trail:·
set showcmd                   "shows what's being typed as a command"
set hlsearch                  "highlight searches"
set incsearch                 "highlight while typing in a search"
set showmatch                 "show matching ')' and '}'"
syntax on

"*** Indents and tabs ***"
set autoindent            "set the cursor at the same indent as line above"
set smartindent           "be smart about indenting"
set expandtab             "expand tabs to spaces"
set shiftwidth=4          "spaces for each step of indent"
set shiftround            "always round indents to multiples of shiftwidth"
set softtabstop=4         "set virtual tab stop"
set tabstop=4             "proper display of files with tabs"
set copyindent            "use existing indent characters for new indents"
filetype plugin indent on "load filetype plugins and indent settings"

"*** Filetypes ***"
autocmd FileType go setlocal noexpandtab
autocmd FileType html,xhthml,xml setlocal shiftwidth=2 tabstop=2
autocmd FileType ruby setlocal shiftwidth=2 tabstop=2

"*** Mappings ***"
inoremap jj <Esc>
nore ; :

"Tabs"
map <C-t> :tabnew<CR>
map <C-w> :tabclose<CR>
map <C-Tab> :tabn<CR>
