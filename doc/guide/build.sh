#!/bin/bash

mkdir -p build
cp -r images build
asciidoctor -D build tsx-user-guide.adoc
