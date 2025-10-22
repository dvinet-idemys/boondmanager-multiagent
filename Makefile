.PHONY: all lms-start lms-stop lint format typecheck test help

all: lms-start

LMS=${HOME}/.lmstudio/bin/lms

lms-start:
	${LMS} server start

	# support cold start by waiting for service to start
	@sleep 3

	${LMS} load openai/gpt-oss-20b \
		--gpu=max \
		--context-length=10000

	${LMS} load qwen/qwen3-4b-thinking-2507 \
		--gpu=max \
		--context-length=4096

	${LMS} load text-embedding-nomic-embed-text-v1.5 \
		--gpu=max \

lms-stop:
	${LMS} server stop

	${LMS} unload --all

# Linting and Code Quality
help:
	@echo "Available targets:"
	@echo "  lint        - Run all linters (ruff format check, ruff check, mypy)"
	@echo "  format      - Auto-format code with ruff"
	@echo "  typecheck   - Run mypy type checking"
	@echo "  test        - Run pytest with coverage"
	@echo "  lms-start   - Start LMStudio and load models"
	@echo "  lms-stop    - Stop LMStudio and unload models"

lint: format-check typecheck ruff
	@echo "✅ All linting checks passed!"

format:
	@echo "🎨 Formatting code with ruff..."
	uv run ruff format src/ tests/

format-check:
	@echo "🔍 Checking code formatting..."
	uv run ruff format --check src/ tests/

ruff:
	@echo "🔍 Running ruff linter..."
	uv run ruff check src/ tests/

ruff-fix:
	@echo "🔧 Auto-fixing ruff issues..."
	uv run ruff check --fix src/ tests/

typecheck:
	@echo "🔍 Running mypy type checking..."
	uv run mypy src/

test:
	@echo "🧪 Running tests with coverage..."
	uv run pytest

test-fast:
	@echo "⚡ Running tests without coverage..."
	uv run pytest --no-cov -x

clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage 2>/dev/null || true
