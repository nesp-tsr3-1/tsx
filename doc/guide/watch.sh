#!/bin/bash

# Watches for changes and automatically runs build

echo 'Watching for changes'

fswatch -o -e build . | xargs -n1 -I{} sh -c 'echo "$(date) Running build" && ./build.sh'
