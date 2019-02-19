This directory contains scripts for creating a virtual machine image for running the TSX workflow.

Virtual machines are created using packer (https://www.packer.io)

There are 3 packer scripts which progressively build a TSX workflow environment. Each VM builds on the previous.

 ubuntu1804:                A fresh, minimal Ubuntu 18.04 installation

 ubuntu1804-tsx:            ubuntu1804, plus:
                                - All TSX workflow dependencies installed
                                - Latest TSX repository cloned from git master into ~tsx/tsx
                                - A Python virtualenv with all dependencies installed
                                - TSX sample data downloaded

 ubuntu1804-tsx-desktop:    ubntu1804-tsx, plus:
                                - A minimal desktop environment (LXDE)
                                - Auto login and auto starting terminal

