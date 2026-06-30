.PHONY: setup run update

setup:
	./install.sh

run:
	record &

update:
	./install.sh --update
