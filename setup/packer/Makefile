.PHONY: all
all: build/tsx-desktop/tsx-desktop.ova

build/ubuntu2004/ubuntu2004.ova: ubuntu2004.pkr.hcl
	packer build -force ubuntu2004.pkr.hcl

build/tsx-deps/tsx-deps.ova: tsx-deps.pkr.hcl build/ubuntu2004/ubuntu2004.ova ../ubuntu-setup-tsx-deps.sh
	packer build -force tsx-deps.pkr.hcl

build/tsx/tsx.ova: tsx.pkr.hcl build/tsx-deps/tsx-deps.ova ../ubuntu-setup-tsx.sh
	packer build -force tsx.pkr.hcl

build/tsx-desktop/tsx-desktop.ova: tsx-desktop.pkr.hcl build/tsx/tsx.ova scripts/*.sh ../ubuntu-setup-desktop.sh
	packer build -force tsx-desktop.pkr.hcl

build/tsx-desktop/tsx-web.ova: tsx-web.pkr.hcl build/tsx/tsx.ova scripts/*.sh ../ubuntu-setup-web.sh
	packer build -force tsx-web.pkr.hcl

.PHONY: clean

clean:
	rm -rf build/*
