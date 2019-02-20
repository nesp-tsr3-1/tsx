#!/bin/bash

./build.sh
rsync -avz build/ nesp2:guide/
