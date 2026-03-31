.PHONY: setup run

setup:
	chmod +x install.sh && ./install.sh

run:
	record &
