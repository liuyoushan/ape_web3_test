# AGENTS.md — ape-demo

## Project Overview

ApeWorX-based Web3 & CEX automated testing framework. Python 3.8+ with Solidity 0.8.20, Pytest + Allure reporting. 93 test cases across 4 domains: smart contracts, DEX, CEX, security.

## Quick Commands

```bash
# Setup
pip install -r requirements.txt
ape plugins install solidity anvil

# Run tests (primary method)
source .venv/bin/activate
python3 run_tests.py -s --project contracts    # Contract layer
python3 run_tests.py -s --project dex          # DEX layer
python3 run_tests.py -s --project cex          # CEX layer
python3 run_tests.py -s --project security     # Security tests
python3 run_tests.py -s --project all          # All domains

# Run by priority
python3 run_tests.py -s --project cex -m "P0"
python3 run_tests.py -s --project contracts -m "P0 and ERC20"

# Run specific test
python3 run_tests.py -s tests/cex/fund/scenarios/test_account.py::test_cex_fund_001_get_balance --no-report

# List available projects
python3 run_tests.py --list-projects

# Lint (non-blocking)
flake8 scripts/ tests/ --max-line-length=120

# Solidity lint
solhint 'contracts/**/*.sol'

# Deploy smoke test
ape run deploy --network ethereum:local
```

## Architecture

```
framework/          # Shared library (NOT a test directory)
  core/             # logger, config, formatters, assertions, retry/polling helpers
  api/              # HTTP client with retry
  cex/              # HMAC-SHA256 CEX client, assertions, mock chain simulator
  web3/             # Ape Framework wrapper (deploy, call, transact, snapshot/rollback)

contracts/          # Solidity contracts (14 files)
tests/
  contracts/        # ERC20 + custom contract tests
  dex/              # DEX swap, liquidation, NFT tests
  cex/              # CEX fund, order, risk tests
  security/         # Security scenario tests
scripts/            # Deploy smoke test
```

## Critical: Fork Node Must Be Running

Most tests require a mainnet fork. Start it before running tests:

```bash
source ./start_fork_node.sh
```

This launches Anvil at `127.0.0.1:8545` with mainnet fork at block 19500000. The `ape-config.yaml` sets `no_start: true`, so Ape will NOT auto-start a node. Tests will fail without this.

## Test Conventions

### Module Structure Pattern
```
tests/{domain}/{module}/
  conftest.py               # Re-exports fixtures
  apis/                     # API wrapper classes
  data/test_{module}.yaml   # YAML test data
  fixtures/                 # pytest fixtures
  scenarios/                # Actual test functions
```

### Naming
- Functions: `test_{domain}_{number}_{description}` (e.g., `test_erc20_001_metadata_verification`)
- Test data files: `test_{module}.yaml`
- Markers: `@pytest.mark.P0`, `@pytest.mark.CEX_Fund`, `@pytest.mark.ERC20`

### Logging
Use `log.step()`, `log.debug()`, `log.success()` — not `print()`. The singleton `log` from `framework.core.logger` handles file persistence automatically.

### Allure Integration
Tests use `@allure.title()`, `@allure.description()`, `@allure.tag()` decorators. Reports auto-generate in `report/allure-report/{timestamp}/` with a `latest` symlink.

## CEX-Specific Notes

- Tests target **Binance testnet** (`https://testnet.binance.vision`)
- Several wallet APIs (`/sapi/v1/*`) return 404 on testnet — tests using these are marked `@pytest.mark.skip`
- `CEX_BASE_URL` in `.env` controls the target
- CEX fixtures use `scope="function"` (fresh client per test), unlike contract fixtures which use `scope="module"`

## Environment

`.env` file (gitignored) must contain:
- `TEST_MNEMONIC` — test wallet mnemonic
- `CEX_API_KEY` / `CEX_API_SECRET` — Binance testnet keys
- `ALCHEMY_MAINNET_API_KEY` — for mainnet fork RPC

Config priority: environment variables > `config/{env}.yaml` > `config/config.example.yaml`

## No Type Checking or Pre-commit

- No mypy/pyright configuration exists
- No pre-commit hooks
- Only lint tool: `flake8` (non-blocking in CI)
- No formatter (black/ruff) configured

## CI Notes

GitHub Actions runs on push to main/dev, PR to main, and daily cron. Path filters exclude README-only changes. CI installs Foundry with retry logic (up to 3 attempts).
