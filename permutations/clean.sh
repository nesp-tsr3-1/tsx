#!/bin/bash

DIR="$1"
set -e
shopt -s extglob

cd "$DIR"
rm -rf !(*infile_Results.txt)
