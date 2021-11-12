This directory contains scripts for creating a virtual machine image for running the TSX workflow.

Virtual machines are created using packer (https://www.packer.io)

There are 4 packer scripts which progressively build a TSX workflow environment. Each VM builds on the previous.

 ubuntu2004:                A fresh, minimal Ubuntu 20.04 installation

 tsx-deps:                  ubuntu1804, plus:
                                - All TSX workflow dependencies installed

 tsx:                       tsx-deps, plus:
                                - Latest TSX repository cloned from git master into ~tsx/tsx
                                - A Python virtualenv with all dependencies installed
                                - TSX sample data downloaded

 tsx-desktop:               tsx, plus:
                                - A minimal desktop environment (LXDE)
                                - Auto login and auto starting terminal

