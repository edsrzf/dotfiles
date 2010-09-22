set nocompatible

set autochdir                 "set pwd to directory of current file"
set hidden

"*** Don't allow bad habits ***"
map <up> <nop>
map <down> <nop>
map <left> <nop>
map <right> <nop>

"*** Console UI & Text display ***"
set visualbell
set number
set mouse=a                   "use a mouse in the console"
set ruler
set lazyredraw
set list
set listchars=tab:»\ ,trail:·
syntax on

"*** GUI options ***"
if has('gui_running')
    set lines=50              "windows are 100x50"
    set columns=100
    set guioptions-=m         "hide menu bar"
    set guioptions-=T         "hide tool bar"
endif

"*** Search ***"
"search with sane regular expressions"
nnoremap / /\v
vnoremap / /\v
set showcmd                   "shows what's being typed as a command"
set hlsearch                  "highlight searches"
set incsearch                 "highlight while typing in a search"
set showmatch                 "show matching ')' and '}'"
set ignorecase                "ignore case"
set smartcase                 "except when search includes caps"

"*** Line wrapping ***"
set wrap                      "wrap lines"
set textwidth=79              "wrap at column 79"
set formatoptions=qrn1
set colorcolumn=85            "color lines that are too long"

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
let mapleader=","
nore ; :

"move by screen lines, not file lines"
nnoremap j gj
nnoremap k gk

"tabs"
map <C-t> :tabnew<CR>
map <C-w> :tabclose<CR>
map <C-Tab> :tabn<CR>
