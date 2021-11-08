#!/bin/bash

./build.sh
rsync -avz build/ tsx:guide/
