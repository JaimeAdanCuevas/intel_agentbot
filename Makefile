.PHONY: all test analyze clean

all: test analyze

test:
	@pytest -v tests/

analyze:
	@python -m src.core.coverage.analyzer

clean:
	@find . -name '*.pyc' -delete
	@rm -rf __pycache__/
