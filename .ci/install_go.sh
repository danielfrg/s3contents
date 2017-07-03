#!/usr/bin/env bash

mkdir -p ~/go
mkdir -p ~/bin

curl -sL -o ~/bin/gimme https://raw.githubusercontent.com/travis-ci/gimme/master/gimme
chmod +x ~/bin/gimme
export PATH=~/bin/:$PATH

gimme 1.7.1
export GOROOT=~/.gimme/versions/go1.7.1.linux.amd64
export PATH=~/.gimme/versions/go1.7.1.linux.amd64/bin:$PATH
export GIMME_ENV=~/.gimme/envs/go1.7.1.env

export GOPATH=~/go
export PATH=$GOPATH/bin:$PATH

go version >&2
