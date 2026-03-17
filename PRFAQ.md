# PR/FAQ: Vincul Protocol

---

## Press Release

**Vincul Launches Open Protocol That Makes AI Agent Boundaries Cryptographically Unbreakable**

*While researchers prove 100% prompt injection success rates against every major LLM, Vincul offers the first deterministic enforcement layer for multi-agent systems*

---

**Tel Aviv, 2026** — Vincul today announced the public release of the Vincul Protocol, an open coordination infrastructure that replaces probabilistic LLM safety guardrails with cryptographically enforced boundaries for AI agents. The protocol is available immediately under CC0 (public domain) with a reference Python implementation.

Today's AI agent platforms rely on system prompts — natural language instructions — to prevent agents from taking unauthorized actions. But system prompts are enforced by the same LLM that processes user input, making them fundamentally vulnerable to prompt injection. Researchers from OpenAI, Anthropic, and DeepMind have independently confirmed that indirect prompt injection achieves near-100% bypass rates against all major models. An attacker who can put text in front of an agent — via email, chat message, shared document, or any external input — can override the agent's safety instructions.

"The problem isn't that LLMs are bad at following instructions," said Vincul's creator. "The problem is that safety rules and attacker input are processed by the same system. It's like having a security guard who can be convinced by a good argument to open the vault. Vincul moves enforcement out of the LLM entirely."

Vincul introduces a fundamentally different model: **the Coalition Contract as the root of authority**. Instead of telling an agent what it *should* do (probabilistic), Vincul defines what an agent *can* do (deterministic). Every action passes through a 7-step cryptographic enforcement pipeline before it reaches any external system. Unauthorized actions are denied with a signed receipt — regardless of what the LLM was tricked into attempting.

**A live demonstration tells the story in three acts:**

In **Act 1**, two AI agents — Alice's and Bob's — coordinate dinner plans on the OpenClaw platform. Alice asks her agent to check Bob's availability and book a restaurant. The agents communicate via the platform's inter-agent messaging. Everything works.

In **Act 2**, an attacker named Sarah sends Alice's agent a WebChat message containing a hidden prompt injection. The message appears to be about restaurant plans, but it contains fake message boundary markers that trick the LLM into treating attacker-controlled text as instructions from Alice herself. The agent, believing it's following Alice's orders, forwards three malicious messages to Bob's agent: a fake Venmo payment request for $500 to a fraudulent account, a $2,000 hotel booking request, and an innocuous dinner recap as cover. All three reach Bob. The system prompt — which explicitly says "don't exfiltrate private data" and "ask before acting externally" — is completely bypassed.

In **Act 3**, the same agents run with Vincul enforcement active. The same injection fires. The LLM is tricked just as before. But when Alice's compromised agent attempts to send messages to Bob, every call passes through the Vincul enforcement pipeline first. Message to Bob's chat? Denied — Alice's agent only has scope for `gateway.messaging.alice`, not `gateway.messaging.bob`. Commit action to Bob's agent? Denied — Alice's inter-agent scope only permits OBSERVE and PROPOSE, not COMMIT. Data exfiltration? Denied — Alice's data scope is read-only. Each denial produces a cryptographic receipt. When Alice revokes the compromised agent's root scope, cascade revocation instantly invalidates all child scopes via BFS traversal. Three attacks, zero successes, five receipts, full audit trail.

"System prompts are security theater for agents," said the creator. "They work until they don't, and you can't prove when they will or won't. Vincul scopes either permit an action or they don't. There's no 'sometimes.'"

The Vincul Protocol is designed for any system where multiple parties coordinate with bounded authority: AI agent platforms, cross-vendor marketplaces, joint ventures, and regulated environments. The reference implementation is approximately 3,400 lines of Python with a single dependency (`cryptography`), a 7-step enforcement pipeline with 425 unit tests, and 13 hash correctness vectors that serve as the compliance gate for any implementation.

**Vincul Protocol is available now at vincul.io under CC0 1.0 Universal (public domain).**

---

## Frequently Asked Questions

### External FAQ (Customers / Developers / Press)

**Q: What is Vincul in one sentence?**

Vincul is an open protocol that makes AI agent permissions cryptographically enforced instead of LLM-enforced, so a jailbroken agent still can't exceed its authorized scope.

**Q: Why can't I just write better system prompts?**

You can, and you should. But system prompts are processed by the same LLM that processes untrusted input. This is a fundamental architectural flaw, not an engineering problem to optimize. Research consistently shows that indirect prompt injection bypasses system prompts regardless of how they're written. The defense is probabilistic — sometimes the LLM resists, sometimes it doesn't. Vincul enforcement is deterministic — the scope either permits the action or it doesn't, and the LLM is never consulted.

**Q: How does the prompt injection demo actually work?**

Sarah sends a WebChat message to Alice's agent on OpenClaw, a real open-source AI agent platform. The message looks like "Hey Alice! La Maison Rouge for Saturday!" but contains a hidden `[end of inter-session message]` boundary marker followed by instructions that appear to come from Alice. The LLM processes this as two separate messages — one from Sarah and one from Alice — and follows the fake "Alice" instructions. This is a real attack using the real OpenClaw WebSocket protocol (ed25519 device authentication, `chat.send` delivery). No synthetic shortcuts.

**Q: What is the 7-step enforcement pipeline?**

Every action an agent attempts passes through seven checks in fixed order:

1. **Contract validity** — Is the coalition contract active and not expired?
2. **Scope validity** — Does the scope exist, and are all its ancestors valid?
3. **Operation type** — Is the action type (OBSERVE/PROPOSE/COMMIT) permitted?
4. **Namespace containment** — Is the target within the scope's namespace?
5. **Predicate evaluation** — Does the action satisfy the scope's conditions?
6. **Ceiling check** — Is the action within hard limits?
7. **Budget check** — For COMMIT actions, is there remaining budget?

First failure denies the action and produces a cryptographic receipt. No short-circuiting — every step is evaluated in order.

**Q: What is a Coalition Contract?**

A Coalition Contract is the root of all authority in Vincul. It defines who the parties are, what the coalition's purpose is, what governance rules apply, and when authority expires. Unlike identity-based systems where permissions flow from "who you are," Vincul authority flows from "what the coalition agreed to." A contract must have at least two principals (otherwise it's just a scope). Once activated, it's immutable.

**Q: What are scopes?**

Scopes are bounded grants of authority issued under a contract. Each scope specifies a namespace (what it applies to), operation types (read/propose/commit), predicates (conditions), and ceilings (hard limits). Scopes can be delegated — a parent scope can create child scopes with equal or narrower authority, never broader. They form a directed acyclic graph (DAG), which enables cascade revocation: revoking a parent instantly invalidates all descendants.

**Q: What are receipts?**

Every protocol event produces a cryptographic receipt containing three parts: **Intent** (what was attempted and by whom), **Authority** (which scope and contract authorized it), and **Result** (what happened). Receipts are hash-sealed, immutable, and symmetric — all parties see the same receipt. They form an append-only audit trail. There are seven receipt kinds: delegation, commitment, revocation, revert attempt, failure, attestation, and contract dissolution.

**Q: Does Vincul replace my existing agent platform?**

No. Vincul sits between the agent and external systems as an enforcement layer. Your agents keep running on whatever platform you use (OpenClaw, LangChain, CrewAI, custom). Vincul intercepts tool calls before they execute and validates them against cryptographic scopes. If the action is authorized, it passes through. If not, it's denied with a receipt. The agent platform doesn't need to be modified — Vincul operates as a sidecar or interceptor.

**Q: What happens when an agent is jailbroken with Vincul active?**

The LLM is still compromised — it still "wants" to execute the attacker's instructions. But when it attempts to call tools, every call passes through the enforcement pipeline. The pipeline doesn't care what the LLM thinks or intends. It checks the cryptographic scope. If the action exceeds the scope, it's denied. The jailbreak succeeds at the LLM level but fails at the enforcement level. This is the core insight: **separate the control plane from the intelligence plane.**

**Q: Is Vincul open source?**

Vincul Protocol is released under CC0 1.0 Universal — public domain, no rights reserved. Anyone can implement it. The reference implementation in Python is available with 425 unit tests and 13 hash correctness test vectors that serve as the compliance gate. Implementations are verified by producing identical hashes for canonical test inputs, not by central certification.

**Q: What does Vincul depend on?**

The core library depends only on `cryptography` (for Ed25519 signatures and SHA-256 hashing). The transport layer adds `websockets`. The demo server adds `fastapi` and `uvicorn`. There is no database, no central server, no cloud dependency. Enforcement is locally computable.

**Q: How is this different from OAuth / RBAC / ABAC?**

| | OAuth/RBAC/ABAC | Vincul |
|---|---|---|
| **Authority root** | Identity (who you are) | Contract (what was agreed) |
| **Enforcement** | Server-side policy check | Cryptographic pipeline (locally verifiable) |
| **Revocation** | Propagation delay, cache invalidation | Instant cascade, fail-closed |
| **Audit** | Logs (mutable, asymmetric) | Receipts (immutable, symmetric, hash-chained) |
| **Governance** | External to authz | Structural (signatures, thresholds, embedded in contract) |
| **Designed for** | Human users accessing services | Multiple parties coordinating with bounded authority |

**Q: What's the performance overhead?**

The 7-step pipeline is pure computation — no network calls, no database queries. Enforcement is sub-millisecond for typical scopes. The constraint DSL is intentionally not Turing-complete (no variables, no loops, no external lookups) to guarantee termination and predictable performance.

---

### Internal FAQ (Technical / Strategic)

**Q: Why contract-as-root instead of identity-as-root?**

Identity-based systems accumulate ambient authority over time. A user gets permissions, those permissions get delegated, the delegation graph becomes opaque, and eventually nobody knows who can do what or why. Contract-as-root inverts this: authority exists only within the context of an explicit agreement between parties, with a defined purpose, defined boundaries, and a defined expiry. When the contract expires or dissolves, all authority derived from it vanishes. This is not a philosophical preference — it's a structural property that makes the system auditable.

**Q: Why fail-closed instead of fail-open?**

In a multi-agent system, fail-open means a bug or misconfiguration silently permits unauthorized actions. Fail-closed means the same bug blocks authorized actions — which is visible, debuggable, and safe. The cost of a false positive (blocking a legitimate action) is friction. The cost of a false negative (permitting an unauthorized action) is a security breach. Vincul always chooses friction over breach.

**Q: Why is the constraint DSL intentionally limited?**

The DSL supports conjunction/disjunction of atoms with comparison operators. No functions, no variables, no external lookups. This guarantees: (1) intersection of two constraints always produces a valid constraint (closure), (2) subset checking is decidable (delegation validation), (3) evaluation terminates in bounded time, and (4) constraints are human-readable. A Turing-complete policy language would be more expressive but would sacrifice these guarantees.

**Q: Why 7 steps in fixed order with no short-circuiting?**

Fixed order ensures deterministic behavior across implementations. No short-circuiting means every implementation evaluates every step, producing identical results. This is critical for the compliance gate: two implementations that short-circuit differently might produce different failure codes for the same input, even if both correctly deny the action. The 7-step ordering also provides defense-in-depth — namespace containment (step 4) catches attacks that pass operation type (step 3).

**Q: What's the competitive landscape?**

- **Prompt engineering / guardrails** (Guardrails AI, NeMo Guardrails): Same-layer defense. LLM enforces its own constraints. Probabilistic. Vincul is orthogonal — use guardrails AND Vincul.
- **Tool-use frameworks** (LangChain, CrewAI): Focus on making tool calls easy, not on bounding them. No enforcement pipeline, no receipts, no revocation.
- **Agent sandboxes** (E2B, Modal): Isolate execution environments but don't bound what the agent can *request*. A jailbroken agent in a sandbox can still make unauthorized API calls within that sandbox.
- **CaMeL (Google DeepMind)**: Closest conceptual peer. Proposes separating "capability" from "permission" for agents. But CaMeL is a research paper; Vincul is a working protocol with reference implementation, compliance gate, and live demo.

**Q: What's the go-to-market?**

1. **Open protocol + live demo**: The jailbreak demo is visceral and shareable. "Watch an AI agent get hacked in real-time, then watch Vincul stop it." This is the awareness play.
2. **SDK for agent developers**: Python SDK with decorators (`@vincul_tool`, `@tool_operation`) that make it trivial to wrap existing tools with Vincul enforcement. This is the adoption play.
3. **Enterprise enforcement service**: Hosted Vincul enforcement with managed contracts, scope administration, and receipt storage. This is the revenue play.
4. **Cross-vendor marketplace**: VinculNet enables agents from different vendors to coordinate with bounded, auditable authority. This is the network-effect play.

**Q: Why public domain (CC0)?**

The protocol must be neutral to be trusted. If Vincul is owned by a company, adoption requires trusting that company. If it's public domain, adoption requires trusting only the math. Revenue comes from implementation, tooling, and services — not from the protocol itself. This mirrors the TCP/IP model: the protocol is free, the value is in what you build on it.

**Q: What's the risk if the demo jailbreak fails (agent resists)?**

The demo is probabilistic by design — sometimes the LLM resists the injection, sometimes it doesn't. This is actually the point: **you can never be certain whether the LLM will resist.** A failed jailbreak run is itself a demonstration of the problem: you just got lucky this time. Vincul's value proposition is eliminating luck from the equation. The demo script notes this explicitly in its output.

**Q: Why does the demo use a real agent platform (OpenClaw) instead of a simulation?**

Credibility. A simulated attack on a simulated agent proves nothing. The demo uses the real OpenClaw WebSocket protocol with real Ed25519 device authentication, real LLM inference (Claude Haiku), and real inter-agent messaging. The injection is delivered exactly as any external WebChat message would be. If we simulated it, the first question would be "but does it work against a real system?" It does.
