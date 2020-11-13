#!/bin/bash

set -e

cd "$(dirname "$0")" && cd ..

mkdir -p jupter/log
jupyter-lab --config=jupyter/jupyter_notebook_config.py 2> jupyter/log/jupyter-lab-$(date +%Y%m%d_%H%M%S).log &

echo
echo Open Jupyter Lab by visiting this URL in your web browser:
echo
echo http://$(hostname -I | cut -f 2 -d ' '):8888
echo
