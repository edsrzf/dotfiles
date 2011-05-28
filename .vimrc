set nocompatible

set autochdir                 "set pwd to directory of current file"
set hidden

"*** Don't allow bad habits ***"
map <up> <nop>
map <down> <nop>
map <left> <nop>
map <right> <nop>

"*** Console UI & Text display ***"
set title                     "change the terminal's title"
set visualbell
set number
set mouse=a                   "use a mouse in the console"
set ruler
set lazyredraw
set list
set listchars=tab:»\ ,trail:·
syntax on
"allow backspacing over everything"
set backspace=indent,eol,start
"ignore these file extensions when globbing"
set wildignore=*.5,*.6,*.8,*.o,*.swp
set nostartofline             "don't go to start of line when scrolling"

"*** GUI options ***"
if has('gui_running')
    set lines=44              "windows are 100x44"
    set columns=100
    set guioptions-=m         "hide menu bar"
    set guioptions-=T         "hide tool bar"
endif

"*** Backups ***"
"don't create a ~ backup file"
set nobackup
"write directly to the file instead of creating a new file and renaming"
set nowritebackup
"put .swp files in vim directory"
set directory=~/.vim/swap,~/tmp,.

"*** Search ***"
set showcmd                   "shows what's being typed as a command"
set gdefault                  "replace globally by default"
set hlsearch                  "highlight searches"
set incsearch                 "highlight while typing in a search"
set showmatch                 "show matching ')' and '}'"
set ignorecase                "ignore case"
set smartcase                 "except when search includes caps"

"Use UTF-8 for everything"
"set termencoding=utf-8
"set encoding=utf-8

"*** Line wrapping ***"
set wrap                      "wrap lines"
set textwidth=79              "wrap at column 79"
set formatoptions=qrn1
if version >= 703
    set colorcolumn=85            "color lines that are too long"
endif

"*** Indents and tabs ***"
set autoindent            "set the cursor at the same indent as line above"
set smartindent           "be smart about indenting"
set expandtab             "expand tabs to spaces"
set shiftwidth=8          "spaces for each step of indent"
set shiftround            "always round indents to multiples of shiftwidth"
set softtabstop=8         "set virtual tab stop"
set tabstop=8             "proper display of files with tabs"
set copyindent            "use existing indent characters for new indents"
filetype plugin indent on "load filetype plugins and indent settings"

"*** Filetypes ***"
autocmd FileType go setlocal noexpandtab
autocmd FileType html,xhthml,xml setlocal shiftwidth=2 softtabstop=2 tabstop=2
autocmd FileType java setlocal shiftwidth=4 softtabstop=4 tabstop=4
autocmd FileType python setlocal shiftwidth=4 softtabstop=4 tabstop=4
autocmd FileType ruby setlocal shiftwidth=2 tabstop=2

"*** Mappings ***"
let mapleader=","
nore ; :

"move by screen lines, not file lines"
nnoremap j gj
nnoremap k gk

"redraw the screen and remove search highlighting"
nnoremap <silent> <C-l> :noh<CR><C-l>

"tabs"
map <C-t> :tabnew<CR>
map <C-Tab> :tabn<CR>

"NERDTree"
map <C-n> :NERDTree<CR>
