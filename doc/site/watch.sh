#!/bin/bash

fswatch -o -e build/ . | xargs -n1 -I{} ./run-antora.sh
