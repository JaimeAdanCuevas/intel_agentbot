.PHONY: all test analyze stress-ng clean

all: test analyze stress-ng

test:
	. .venv/bin/activate && PYTHONPATH=$(PWD) pytest -v tests/

analyze:
	. .venv/bin/activate && PYTHONPATH=$(PWD) python -m src.core.coverage.analyzer --sde-file tests/integration/data/cg.A.AVX2-mix-out.txt --xed-path ./bin/xed

stress-ng:
	./scripts/deployment/run_stress_ng_sde.sh
	. .venv/bin/activate && PYTHONPATH=$(PWD) python -m src.core.coverage.analyzer --sde-file tests/integration/data/stress-ng-cpu-mix-out.txt --xed-path ./bin/xed

clean:
	find . -name '*.pyc' -delete
	rm -rf __pycache__/

.PHONY: all test analyze stress-ng clean
