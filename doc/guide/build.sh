#!/bin/bash

mkdir -p build
cp -r images build
asciidoctor -D build index.adoc
