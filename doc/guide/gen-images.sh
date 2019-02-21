#!/bin/bash

for svg_file in svg/*.svg
do
	for id in $(inkscape --query-all "$(pwd)/$svg_file" | cut -d "," -f 1 | grep "^ex")
	do
		output_file="images/$(basename "$svg_file" .svg)${id:2}.png"
		inkscape -f "$(pwd)/$svg_file" --export-png "$(pwd)/$output_file" --export-dpi 180 --export-id "$id" --export-id-only
	done
done
