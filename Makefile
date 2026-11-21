.PHONY: install lint format test run stop clean docker-clean docker-clean-all

UV_CACHE_DIR ?= .uv-cache
UV_PYTHON_INSTALL_DIR ?= .uv-python
export UV_CACHE_DIR UV_PYTHON_INSTALL_DIR

install:
	uv sync --locked

lint:
	uv run ruff check backend tests swagger
	uv run ruff format --check backend tests swagger
	cd backend/auth-service && uv run --project ../.. mypy app models services
	cd backend/recommendation-service && uv run --project ../.. mypy app main.py

format:
	uv run ruff check --fix backend tests swagger
	uv run ruff format backend tests swagger

test:
	cd backend/recommendation-service && uv run --project ../.. python -m pytest tests
	uv run python tests/run_tests.py

run:
	docker compose up --build

stop:
	docker compose down

docker-clean:
	docker compose down --volumes --remove-orphans

docker-clean-all:
	-docker stop $$(docker ps -a -q)
	-docker rm $$(docker ps -a -q)
	-docker rmi $$(docker images -q)
	docker system prune -a --volumes -f
