.PHONY: install test lint clean

install:
	python -m pip install -e .

test:
	python -m unittest discover -s tests -v

lint:
	python -m py_compile src/handy/*.py tests/*.py

clean:
	rm -rf build dist *.egg-info .pytest_cache __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} +
