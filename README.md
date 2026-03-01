# Pact Protocol

**Bounded authority coordination infrastructure.**

Pact is a protocol for multi-party coordination with explicit boundaries, cryptographic receipts, and fail-closed enforcement. It lets principals (people, agents, services) coordinate actions under shared constraints — where every decision is scoped, every action is auditable, and every receipt is verifiable.

> *Human coordination fails not because people are untrustworthy, but because the tools for establishing shared boundaries have been too expensive, too slow, or too opaque.* — [PHILOSOPHY.md](pact-spec/PHILOSOPHY.md)

---

## What does Pact guarantee?

| Guarantee | How |
|---|---|
| **Authority is explicit** | Every action requires a valid scope with declared types, namespace, and ceiling |
| **Actions are attributable** | Every commit produces a hash-sealed receipt linking intent → authority → result |
| **Boundaries are inspectable** | Scopes form a DAG — parent constraints always contain child constraints |
| **Revocation is real** | Revoking a scope cascades to all descendants; post-revocation actions fail closed |

## What Pact does *not* guarantee

Pact makes no claims about human character, legal enforceability, or economic outcomes. Trust in Pact is trust in structure, not in people.

---

## Installation

### Core library only

Install just the Pact Protocol core library (no server dependencies):

```bash
git clone https://github.com/smazor/pact.git && cd pact
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

This installs the `pact` package with its only dependency (`cryptography`).

### With demo server

To run the interactive demo, install with the `server` extra and build the frontend:

```bash
git clone https://github.com/smazor/pact.git && cd pact
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[server]"

# Build the frontend
cd apps/web && npm install && npm run build && cd ../..
```

### Verify installation

```bash
source .venv/bin/activate
python3 -m unittest discover -s tests -p "test_*.py"    # 425 tests
python3 ci/check_vectors.py                              # 13 vectors
```

---

## Usage

### Creating a runtime

`PactRuntime` is the main entry point. It wires all stores, validators, and evaluators together:

```python
from pact.runtime import PactRuntime
from pact.contract import CoalitionContract
from pact.scopes import Scope
from pact.types import Domain, OperationType

runtime = PactRuntime()
```

### Registering and activating a contract

```python
contract = CoalitionContract(
    contract_id="c0000000-0000-0000-0000-000000000001",
    version="0.2",
    purpose={
        "title": "Project Alpha",
        "description": "Multi-team coordination contract",
    },
    principals=[
        {"principal_id": "principal:alice", "role": "coordinator"},
        {"principal_id": "principal:bob", "role": "member"},
        {"principal_id": "principal:carol", "role": "member"},
    ],
    governance={
        "decision_rule": "threshold",
        "threshold": 2,
        "amendment_rule": "unanimous",
        "amendment_threshold": None,
    },
    budget_policy={
        "allowed": True,
        "dimensions": [
            {"name": "USD", "unit": "currency", "ceiling": "10000"},
        ],
    },
    activation={
        "status": "draft",
        "activated_at": None,
        "expires_at": "2026-12-31T23:59:59Z",
    },
)

# Register (validates structure, computes descriptor_hash)
runtime.register_contract(contract)

# Activate (draft → active)
runtime.activate_contract(
    contract_id=contract.contract_id,
    activated_at="2026-03-01T00:00:00Z",
    signatures=["principal:alice", "principal:bob", "principal:carol"],
)
```

### Creating scopes and delegating authority

```python
# Root scope — full authority for the coordinator
root_scope = Scope(
    id="s0000000-0000-0000-0000-000000000001",
    issued_by_scope_id=None,                    # root scope has no parent
    issued_by=contract.contract_id,
    issued_at="2026-03-01T00:00:00Z",
    expires_at="2026-12-31T23:59:59Z",
    domain=Domain(
        namespace="project",
        types=(OperationType.OBSERVE, OperationType.PROPOSE, OperationType.COMMIT),
    ),
    predicate="TOP",                            # no restrictions
    ceiling="action.params.cost <= 10000",
    delegate=True,                              # can create child scopes
    revoke="principal_only",
)
runtime.scopes.add(root_scope)

# Delegate a child scope to Bob — limited to project.engineering
child_scope = Scope(
    id="s0000000-0000-0000-0000-000000000002",
    issued_by_scope_id=root_scope.id,           # parent pointer
    issued_by="principal:alice",
    issued_at="2026-03-01T00:01:00Z",
    expires_at="2026-12-31T23:59:59Z",
    domain=Domain(
        namespace="project.engineering",        # narrower than parent
        types=(OperationType.OBSERVE, OperationType.PROPOSE, OperationType.COMMIT),
    ),
    predicate="action.params.cost <= 5000",     # must be within ceiling
    ceiling="action.params.cost <= 5000",       # tighter ceiling than parent
    delegate=False,
    revoke="principal_only",
)

receipt = runtime.delegate(
    parent_scope_id=root_scope.id,
    child=child_scope,
    contract_id=contract.contract_id,
    initiated_by="principal:alice",
)
print(receipt.receipt_kind)  # "delegation"
print(receipt.receipt_hash)  # SHA-256 hash
```

### Executing actions through the enforcement pipeline

```python
# Bob commits an action — passes all 7 enforcement steps
receipt = runtime.commit(
    action={
        "type": "COMMIT",
        "namespace": "project.engineering",
        "resource": "server:prod-deploy",
        "params": {"cost": 2000},
    },
    scope_id=child_scope.id,
    contract_id=contract.contract_id,
    initiated_by="principal:bob",
    budget_amounts={"USD": "2000"},
)

print(receipt.receipt_kind)  # "commitment"
print(receipt.outcome)       # "success"
```

### Handling failures

The enforcement pipeline is fail-closed. When any of the 7 steps fails, a failure receipt is emitted:

```python
# Bob tries to exceed the ceiling — fails at step 6
receipt = runtime.commit(
    action={
        "type": "COMMIT",
        "namespace": "project.engineering",
        "resource": "server:premium-cluster",
        "params": {"cost": 8000},      # exceeds ceiling of 5000
    },
    scope_id=child_scope.id,
    contract_id=contract.contract_id,
    initiated_by="principal:bob",
    budget_amounts={"USD": "8000"},
)

print(receipt.receipt_kind)  # "failure"
print(receipt.outcome)       # "denied"
print(receipt.detail["error_code"])  # "SCOPE_EXCEEDED"
```

### Revoking scopes and dissolving contracts

```python
# Revoke Bob's scope (cascades to all descendants)
receipt, result = runtime.revoke(
    scope_id=child_scope.id,
    contract_id=contract.contract_id,
    initiated_by="principal:alice",
)
print(len(result.revoked_ids))  # number of scopes revoked

# Dissolve the entire contract
receipt = runtime.dissolve_contract(
    contract_id=contract.contract_id,
    dissolved_at="2026-06-01T00:00:00Z",
    dissolved_by="principal:alice",
    signatures=["principal:alice", "principal:bob"],  # meets threshold of 2
)
print(receipt.receipt_kind)  # "contract_dissolution"
```

### Querying the audit trail

```python
# All receipts in order
for r in runtime.receipts.timeline():
    print(f"{r.receipt_kind}: {r.outcome} by {r.initiated_by}")

# Receipts for a specific scope
scope_receipts = runtime.receipts.for_scope(child_scope.id)

# Look up a receipt by hash
receipt = runtime.receipts.get(receipt.receipt_hash)
```

---

## Project Structure

```
src/pact/                        Core protocol library (11 modules)
│
├── types.py                     Enums, Domain, ValidationResult — pure data
├── hashing.py                   JCS canonicalization, pact_hash(), normalization
├── identity.py                  Ed25519 sign/verify
├── interfaces.py                5 Protocol definitions (structural typing)
│
├── contract.py                  CoalitionContract, ContractStore, governance
├── scopes.py                    Scope DAG, DelegationValidator, revocation cascade
├── constraints.py               Constraint DSL parser/evaluator
├── receipts.py                  Receipt dataclass, 5 builders, ReceiptLog
├── budget.py                    BudgetLedger — Decimal arithmetic, per-scope ceilings
│
├── validator.py                 7-step enforcement pipeline (imports only interfaces)
└── runtime.py                   PactRuntime — composition root

tests/                           425 unit tests across 8 files
ci/check_vectors.py              13-vector CI gate (hash correctness)

pact-spec/                       Protocol specification
├── PHILOSOPHY.md                Protocol constitution
├── GLOSSARY.md                  Canonical vocabulary
└── spec/                        12 normative spec documents

connectors/                      Stub connectors for demo (flights, hotels)

apps/
├── server/                      FastAPI backend — demo state, routes, WebSocket
│   ├── main.py                  App entry point, static file serving
│   ├── demo_state.py            8-friends-trip scenario fixtures
│   ├── websocket.py             ConnectionManager, real-time broadcast
│   └── routes/                  REST endpoints (contract, actions, votes, demo)
│
└── web/                         React + TypeScript + Tailwind frontend (Vite)
    └── src/
        ├── api/                 Typed API client
        ├── hooks/               WebSocket + status polling hooks
        └── components/          Dashboard UI — 5 flow cards + timeline
```

---

## Architecture

### Two-store model

Pact separates state from audit:

- **ContractStore** — source of truth for contract state (draft → active → dissolved)
- **ReceiptLog** — append-only audit trail (hash-verified, immutable once appended)

Stores are independent. Receipt emission is the runtime's responsibility.

### Dependency firewall

```
validator.py  ──imports──▶  interfaces.py (Protocols only)
runtime.py    ──imports──▶  all concrete classes (sole composition root)
```

The validator never sees concrete implementations. All interfaces use `Protocol` (structural typing), not ABC.

### 7-step enforcement pipeline

Every action passes through these checks in locked order. First failure wins.

```
1. Contract valid          active, not expired, not dissolved
2. Scope exists & valid    not revoked, not expired, ancestors valid
3. Operation type          action type ∈ scope's domain types
4. Namespace containment   action namespace ⊆ scope namespace
5. Predicate evaluation    action satisfies scope predicate
6. Ceiling check           action within scope ceiling
7. Budget check            COMMIT only: consumed + requested ≤ ceiling
```

---

## The Demo

The interactive demo proves four assertions through an **8-friends-trip to Italy** scenario.

### Running the demo

After [installing with server dependencies](#with-demo-server):

```bash
source .venv/bin/activate
PYTHONPATH=. uvicorn apps.server.main:app --port 8000
```

Open http://localhost:8000 in your browser. The demo UI shows stakeholder cards, scope popovers, receipt timeline, and animated agent message flows.

Click through the 5 flows in order — each flow demonstrates a different protocol guarantee:

| # | Flow | What happens | Assertion proved |
|---|---|---|---|
| 1 | **Contract Setup** | 8 principals form a coalition with 3 scoped delegations | Delegation is bounded |
| 2 | **Raanan's Personal Agent Books Flight** | COMMIT on `travel.flights` with valid scope → success | Receipts are verifiable |
| 3 | **Yaki's Personal Agent Tries Hotel Booking** | COMMIT on OBSERVE+PROPOSE scope → `TYPE_ESCALATION` | Scope enforcement works |
| 4 | **Agents Vote to Widen Scope + Rebook** | 5/8 governance vote grants COMMIT → Yaki rebooks | Bounded delegation via governance |
| 5 | **Dissolve Coalition** | Contract dissolved, all scopes revoked, actions fail | Revocation is real |

### Development mode (two terminals)

For frontend hot-reload during development:

```bash
# Terminal 1 — backend
source .venv/bin/activate
PYTHONPATH=. uvicorn apps.server.main:app --reload       # API + WebSocket on :8000

# Terminal 2 — frontend
cd apps/web && npm run dev                               # Vite dev server on :5173
```

### API Endpoints

```
POST /contract/setup          Initialize the 8-friends-trip scenario
POST /contract/dissolve       Dissolve contract + cascade revocation
POST /action                  Execute action through enforcement pipeline
POST /vote/open               Open a governance vote
POST /vote/cast               Cast vote (auto-resolves at threshold)
POST /demo/reset              Reset to clean state
GET  /demo/status             Current state summary
GET  /demo/state              Enriched state (principals, scopes, governance, budget)
WS   /ws                      Real-time event broadcast
```

---

## Testing

```bash
# Full test suite (425 tests)
python3 -m unittest discover -s tests -p "test_*.py"

# Single module
python3 -m unittest tests.test_validator

# CI gate — hash correctness (must always pass)
python3 ci/check_vectors.py
```

All tests use `unittest`. Each test file is self-contained — no shared fixtures or conftest.

---

## Specification

The full protocol specification lives in [`pact-spec/`](pact-spec/spec/README.md). Start with:

1. [`PHILOSOPHY.md`](pact-spec/PHILOSOPHY.md) — the protocol constitution
2. [`GLOSSARY.md`](pact-spec/GLOSSARY.md) — canonical vocabulary
3. [`spec/scope/SCHEMA.md`](pact-spec/spec/scope/SCHEMA.md) — scope structure and validity
4. [`spec/receipts/RECEIPT.md`](pact-spec/spec/receipts/RECEIPT.md) — receipt envelope
5. [`spec/crypto/HASHING.md`](pact-spec/spec/crypto/HASHING.md) — JCS canonicalization + 13 test vectors

**Protocol version: v0.2** — complete geometry, no open gaps.

---

## Requirements

- **Python** 3.11+ (tested on 3.13.9)
- **Node.js** 18+ (for frontend, tested on 22.x)
- No external runtime dependencies beyond `cryptography` (core) and `fastapi`/`uvicorn`/`websockets` (server)

---

## License

This project is dedicated to the **public domain** under [CC0 1.0 Universal](LICENSE.md).

You can copy, modify, distribute, and perform the work — even for commercial purposes — all without asking permission. No attribution required.

---

Generated on 2026-03-01 — @smazor project
