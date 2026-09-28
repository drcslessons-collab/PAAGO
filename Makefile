.PHONY: verify reproduce test clean
verify:
	PYTHONPATH=src python scripts/verify_inputs.py
reproduce:
	PYTHONPATH=src python scripts/reproduce_all.py
test:
	PYTHONPATH=src python -m pytest -q
clean:
	rm -rf outputs/reproduced .pytest_cache
