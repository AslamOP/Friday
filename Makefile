.PHONY: run daemon test install clean welcome

run:
	. .venv/bin/activate && python3 friday/main.py

daemon:
	. .venv/bin/activate && python3 friday/main.py --daemon

welcome:
	. .venv/bin/activate && python3 friday/main.py --welcome

test:
	. .venv/bin/activate && python3 -m pytest tests/ -v --tb=short

install:
	bash install/setup.sh

clean:
	rm -rf data/*.json data/*.db __pycache__ .pytest_cache
