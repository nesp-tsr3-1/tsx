#!/bin/bash

set -e

./run-antora.sh
rsync -avz build/site/ tsx:tech-doc
