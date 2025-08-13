.PHONY: clean build

build:
	uv build

clean:
	rm -rf dist/ build/ *.egg-info
