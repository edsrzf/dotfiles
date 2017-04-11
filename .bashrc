# if not running interactively, don't do anything
[ -z "$PS1" ] && return

# don't put duplicate lines in the history
export HISTCONTROL=ignoredups

# check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS.
shopt -s checkwinsize

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "$debian_chroot" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

# if this is an xterm set the title to user@host:dir
case "$TERM" in
xterm*|rxvt*)
    PROMPT_COMMAND='echo -ne "\033]0;${USER}@${HOSTNAME}: ${PWD/$HOME/~}\007"'
    ;;
*)
    ;;
esac

# enable color support of ls and also add handy aliases
if [ "$TERM" != "dumb" ]; then
    if hash dircolors &> /dev/null; then
        eval "`dircolors -b`"
        alias ls='ls --color=auto'
    else
        export CLICOLOR=1
    fi
fi

# for Git shell prompt
if [ -f /usr/share/git/completion/git-prompt.sh ]; then
    . /usr/share/git/completion/git-prompt.sh
fi

if hash brew; then
    if [ -f "$(brew --prefix git)/etc/bash_completion.d/git-prompt.sh" ]; then
        . "$(brew --prefix git)/etc/bash_completion.d/git-prompt.sh"
    fi
    if [ $? -a -f "$(brew --prefix)/etc/bash_completion" ]; then
        . "$(brew --prefix)/etc/bash_completion"
    fi
fi
if [ -f ~/.bash_local ]; then
    . ~/.bash_local
fi

alias dc=docker-compose
alias g=git

export PATH="$HOME/bin:$PATH"

export EDITOR=vim
export PAGER="less -FirS"

PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]$(__git_ps1 " (%s)")$ '
