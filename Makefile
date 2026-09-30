.PHONY: install test run docker-build docker-run

install:
	pip install -r requirements.txt

test:
	python -m pytest -q

run:
	GIT_SHA=$$(git rev-parse --short=7 HEAD 2>/dev/null || echo dev) python app.py

docker-build:
	docker build --build-arg GIT_SHA=$$(git rev-parse --short=7 HEAD) -t loan-api:local .

docker-run:
	docker run --rm -p 8080:8080 loan-api:local
