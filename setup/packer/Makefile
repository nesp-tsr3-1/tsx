.PHONY: all
all: build/tsx-desktop/tsx-desktop.ova

build/ubuntu1804/ubuntu1804.ova: ubuntu1804.json
	packer build -force ubuntu1804.json

build/tsx-deps/tsx-deps.ova: ubuntu1804-tsx-deps.json build/ubuntu1804/ubuntu1804.ova ../ubuntu-setup-tsx-deps.sh
	packer build -force ubuntu1804-tsx-deps.json

build/tsx/tsx.ova: ubuntu1804-tsx.json build/tsx-deps/tsx-deps.ova ../ubuntu-setup-tsx.sh
	packer build -force ubuntu1804-tsx.json

build/tsx-desktop/tsx-desktop.ova: ubuntu1804-tsx-desktop.json build/tsx/tsx.ova scripts/*.sh ../ubuntu-setup-desktop.sh
	packer build -force ubuntu1804-tsx-desktop.json

build/tsx-desktop/tsx-web.ova: ubuntu1804-tsx-web.json build/tsx/tsx.ova scripts/*.sh ../ubuntu-setup-web.sh
	packer build -force ubuntu1804-tsx-web.json

.PHONY: clean

clean:
	rm -rf build/*
