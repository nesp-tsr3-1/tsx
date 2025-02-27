#!/bin/bash

#docker run -u $(id -u) -e HOME=/antora -v $PWD:/antora:Z --rm -t antora/antora antora-playbook.yml
docker run -u $(id -u) -e HOME=/antora/doc/site -v $PWD/../..:/antora:Z -w /antora/doc/site --rm -t antora/antora antora-playbook.yml

