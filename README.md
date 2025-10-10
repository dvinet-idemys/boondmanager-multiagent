# BoondManager Invoice Workflow Automation

**Stateless MVP for automated invoice generation from client emails**

## Overview

This system automates the invoice workflow by:
1. Parsing client emails to extract consultant activity data
2. Reconciling declared days against BoondManager CRA data
3. Validating data and business rules
4. Generating invoices in BoondManager
5. Sending email notifications

## Architecture

- **Stateless execution**: In-memory only, no database
- **LangGraph workflow**: 5 nodes with conditional routing
- **BoondManager integration**: API client with retry logic
- **Email processing**: IMAP receiving, SMTP sending

See [docs/MVP_ARCHITECTURE.md](docs/MVP_ARCHITECTURE.md) for detailed architecture.

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (fast Python package manager)
- BoondManager API credentials
- Email server access (IMAP/SMTP)

### Installation

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone <repository-url>
cd boondmanager-multiagent

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install project dependencies
uv pip install -e .

# Install development dependencies
uv pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### Configuration

Edit `.env` file with your credentials:

```bash
# BoondManager API - JWT Authentication
BOOND_USER_TOKEN=your_user_token
BOOND_CLIENT_TOKEN=your_client_token
BOOND_CLIENT_KEY=your_signing_key
BOOND_BASE_URL=https://api.boondmanager.com/api/v3

# Email servers
SMTP_HOST=smtp.gmail.com
SMTP_USER=your_email@company.com
SMTP_PASSWORD=your_password

IMAP_HOST=imap.gmail.com
IMAP_USER=your_email@company.com
IMAP_PASSWORD=your_password
```

### Running the Application

```bash
python main.py
```

## Project Structure

```
boondmanager-multiagent/
├── src/
│   ├── models/          # Pydantic state schemas
│   ├── nodes/           # LangGraph workflow nodes
│   ├── integrations/    # BoondManager API & Email clients
│   ├── templates/       # Jinja2 email templates
│   └── workflow.py      # Main LangGraph workflow
├── tests/
│   ├── unit/            # Unit tests per node
│   ├── integration/     # BoondManager integration tests
│   └── e2e/             # End-to-end workflow tests
├── docs/
│   ├── MVP_ARCHITECTURE.md
│   └── IMPLEMENTATION_PLAN.md
├── config/
│   └── .env.example
├── pyproject.toml       # Project configuration (uv)
└── main.py
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

### Adding Dependencies

```bash
# Add runtime dependency
uv pip install <package>
# Then add to pyproject.toml dependencies

# Add dev dependency
uv pip install <package>
# Then add to pyproject.toml [project.optional-dependencies.dev]
```

## Workflow

1. **Email arrives** → Parsed to extract consultant data
2. **Reconciliation** → Compare against BoondManager CRA
3. **Validation** → Check data integrity and business rules
4. **Invoice generation** → Create invoice in BoondManager
5. **Notification** → Send success/discrepancy emails

See [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) for implementation details.

## Troubleshooting

### Common Issues

**Authentication Error**
- Verify `BOOND_API_KEY` is correct
- Check API key has required permissions

**Email Connection Failed**
- Verify SMTP/IMAP credentials
- Check firewall/network settings
- Enable "Less secure app access" for Gmail (if using)

**Import Errors**
- Ensure virtual environment is activated
- Run `uv pip install -e .`

## License

[Your License]

## Contributing

[Contributing guidelines]
