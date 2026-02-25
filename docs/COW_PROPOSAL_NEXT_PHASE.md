# CoW Protocol Integration Documentation – Proposal (Next Phase)

**Grant Title:** CoW Protocol Integration Documentation – Next Phase

**Context:** CoW Grants RFP – [CoW Protocol Integration Documentation](https://forum.cow.fi/t/cow-protocol-integration-documentation/3360)  
**Repo:** [cow-ai-tools](https://github.com/bleu/cow-ai-tools) (fork of op-ai-tools, adapted for CoW). **Live PoC:** [chat](https://cow-ai-tools-iitlrwya9-bruno-1237s-projects.vercel.app/chat)

---

## Author

[@bleu](https://forum.cow.fi/u/bleu) [@yvesfracari](https://forum.cow.fi/u/yvesfracari) [@ribeirojose](https://forum.cow.fi/u/ribeirojose) [@mendesfabio](https://forum.cow.fi/u/mendesfabio)

---

## About You

bleu collaborates with companies and DAOs as a web3 technology and user experience partner. We’re passionate about bridging the experience gap we see in blockchain and web3.

---

## Additional Links

We developed multiple grants with CoW. The ones that are more related to this project are:

- [CoW] [Framework Agnostic SDK](https://forum.cow.fi/t/grant-application-framework-agnostic-sdk/2811): Restructured SDK architecture to be more composable with framework-agnostic base packages with EVM adapters.
- [CoW] [Hook dApps](https://forum.cow.fi/t/grant-application-cow-hooks-dapps/2544): Hook dApps integrated on the CoW Swap frontend; developed the `cow-shed` module of `@cowprotocol/cow-sdk`.
- [CoW] [Community-built Python SDK](https://forum.cow.fi/t/grant-application-community-built-python-sdk/2026): Python version of the CoW SDK (cow-py) for querying on-chain data, managing orders, and integrating with CoW Protocol smart contracts (grant-funded, complete).
- [CoW] [Migration of CoW Swap Frontend to Viem & Wagmi](https://forum.cow.fi/t/grant-application-migration-of-cow-swap-frontend-to-viem-wagmi/3308): Migrating the CoW Swap frontend from ethers to viem and Wagmi (grant-funded).
- [CoW] [Offline Development Mode](https://forum.cow.fi/t/grant-application-cow-playground-offline-development-mode/3262): Self-contained offline development environment for backend engineers (grant-funded).
- [CoW] [Performance Testing Suite](https://forum.cow.fi/t/grant-application-cow-protocol-playground-performance-testing-suite/3263): Performance testing suite for the CoW Playground (RFP response).
- [CoW] [Improving Solver Infrastructure Onboarding](https://forum.cow.fi/t/retro-round-improving-solver-infrastructure-onboarding/3197) (retro round): Solver template updates, Python Baseline, examples & tests, documentation refresh, and tooling.

**Other relevant work:** [OP Chat (GovGPT)](https://op-chat.bleu.builders/chat) — RAG-based governance chat for Optimism (docs + forum); same conceptual stack (RAG, embeddable chat, citations) as the CoW PoC.

**All Bleu proposals on the CoW Forum:** [bleu – activity/topics](https://forum.cow.fi/u/bleu/activity/topics)

---

## Grant Category

Core Infrastructure & Developer Tooling

---

## Simple Summary

We delivered a PoC for the Integration Documentation RFP (Track A – RAG-based assistant). This proposal extends it to a production-ready offering: embed the chat inside docs.cow.fi, automate index updates from a single CI in our repo (no CI on upstream repos), add all desired CoW-related repos as RAG sources (each with separate budget), and improve models and UX.

---

## Grant Goals and Impact

This grant aims to turn the Integration Documentation PoC into a production-ready RAG assistant for CoW Protocol: embedded in docs, kept up to date via CI, and optionally extended to more repos. The impact extends beyond the PoC—it will reduce friction for integrators, keep docs and API in sync with the chat, and provide a single place to ask integration questions with citations.

**Goal (details)**

The PoC already provides a RAG chat over CoW docs and the Order Book API. To maximize value for integrators, the assistant should be:

- **Where developers read:** Embedded in [docs.cow.fi](https://docs.cow.fi) so answers appear in context.
- **Always up to date:** Automated pipeline so when `cowprotocol/docs` (or the OpenAPI spec) changes, the index and deployed backend update without manual steps.
- **Optionally broader:** Additional sources (e.g. cow-sdk, composable-cow) can help with SDK usage and advanced flows, if CoW wants to expand scope.
- **Improving over time:** Compare AI models (accuracy, latency, cost) and refine the PoC (frontend and backend).

**Benefits for the CoW ecosystem:**

- Lower friction for integrators: answers in-context while reading docs.
- Docs and API stay in sync with the chat: CI keeps the index aligned with Git.
- Single place to ask integration questions, with citations to docs and API reference.
- Optional path to cover SDK and composable orders without overloading the index.

---

## What We Delivered (PoC)

**Live PoC:** [cow-ai-tools chat](https://cow-ai-tools-iitlrwya9-bruno-1237s-projects.vercel.app/chat)

- **RAG chat** over CoW Protocol docs ([cowprotocol/docs](https://github.com/cowprotocol/docs)) and the **Order Book OpenAPI** (endpoints, schemas, errors).
- **Backend:** Quart API (`/up`, `/predict`), FAISS index, Gemini for embeddings and chat. Deployable on Railway/Render (Docker).
- **Frontend:** Next.js chat UI with CoW branding, quick prompts, and reference links.
- **RAG coverage:** The assistant answers integration questions using docs and the Order Book API; we validated it on the RFP priority areas (order creation, approvals, errors, quoting). Answers cite docs and API reference where relevant.
- **Docs and scripts:** Ingestion from `cowprotocol/docs` and OpenAPI fetch; quickstart; golden questions; deploy guide.

**References:** [COW_POC_PLAN.md](COW_POC_PLAN.md), [COW_FLUXO_COMPLETO.md](COW_FLUXO_COMPLETO.md).

---

## Grant Description

Our solution is a **production-ready RAG assistant** for CoW Protocol integration documentation. Below we describe what we will build, what we will use, and the main decisions (including how multi-repo ingestion and CI will work).

**Technical solution**

- **Backend:** Python (Quart) API, FAISS for vector search, configurable embeddings (e.g. OpenAI, Gemini) and LLM (e.g. Gemini, Claude). Same stack as the PoC; we will harden it (error handling, citation ordering, optional streaming).
- **Frontend:** Next.js chat UI, embeddable as a widget (iframe or component) or sidebar for [docs.cow.fi](https://docs.cow.fi), aligned with CoW’s docs stack (e.g. Docusaurus) and design.
- **Data:** CoW docs ([cowprotocol/docs](https://github.com/cowprotocol/docs)), Order Book OpenAPI, and—within this grant—all desired additional repositories listed below. Each source is ingested, chunked, embedded, and merged into a **single FAISS index** so the assistant can answer from docs, API, and code in one place.
- **CI/CD:** All pipelines run from **one repository** (the grant repo: e.g. [cow-ai-tools](https://github.com/bleu/cow-ai-tools) or a dedicated CoW docs-assistant repo). We do **not** add CI jobs or webhooks to upstream repos (cowprotocol/docs, cow-sdk, etc.). Our CI will: (1) clone or fetch from configured sources on a schedule or on trigger, (2) run ingestion scripts per source, (3) rebuild the unified index, (4) run tests, (5) deploy or publish the updated backend. Adding a new repo as a source means adding a config entry and ingestion logic in our repo only—no changes required in the upstream repos. This keeps maintenance and ownership clear and avoids touching every CoW repo.

**Why we propose ingesting more repositories**

- **Coverage:** Docs and OpenAPI already cover concepts and API parameters. Additional repos (SDK, composable-cow, hooks, etc.) add concrete usage, types, and examples so the assistant can answer “how do I do X with the SDK?” or “how do conditional orders work?” with citations to real code.
- **How it works:** Each repo is added as a configured source in our single repo. We implement a small ingestion adapter (clone/fetch → parse → chunk by file/section → metadata with URL to blob). Chunks are embedded and merged into the same FAISS index; the retriever and responder already support multiple source types. So multi-repo is an extension of the current design, not a new system.
- **All desired repos in this grant:** We propose including all of the following repositories in the grant scope. CoW can choose to phase them (e.g. high-value first) or approve the full set; we assign a **separate budget per repo** so the cost of each source is transparent and can be approved or deferred independently.

**Repositories in scope (with separate budget per repo, see Milestones)**

| Repository | Use case | Note |
|------------|----------|------|
| [cowprotocol/docs](https://github.com/cowprotocol/docs) | Official docs | Already in PoC; CI in this grant. |
| Order Book OpenAPI | API reference | Already in PoC; CI in this grant. |
| [cowprotocol/cow-sdk](https://github.com/cowprotocol/cow-sdk) | SDK usage, types, examples | High value, structured. |
| [cowprotocol/composable-cow](https://github.com/cowprotocol/composable-cow) | Composable orders, conditional orders | High value for advanced integration. |
| [cowprotocol/hooks-trampoline](https://github.com/cowprotocol/hooks-trampoline) | Hooks integration | Focused, likely useful. |
| [cowprotocol/watch-tower](https://github.com/cowprotocol/watch-tower) | Monitoring / order status | Focused. |
| [cowprotocol/flash-loan-router](https://github.com/cowprotocol/flash-loan-router) | Flash loans | Focused. |
| [cowdao-grants/cow-shed](https://github.com/cowdao-grants/cow-shed) | Tooling / examples | Grant-related. |
| [cowdao-grants/cow-py](https://github.com/cowdao-grants/cow-py) | Python SDK / examples | Useful for Python integrators. |
| [cowdao-grants/weiroll](https://github.com/cowdao-grants/weiroll) | Weiroll usage | Niche. |
| [cowprotocol/contracts](https://github.com/cowprotocol/contracts) | Contract references | Possible noise (raw Solidity); add if desired. |
| [cowprotocol/cowswap](https://github.com/cowprotocol/cowswap) | Frontend app | Possible noise (app-specific); add if desired. |
| [cowprotocol/services](https://github.com/cowprotocol/services) | Backend/services | Possible noise (broad); add if desired. |

**Complexity assessment for M4 (RAG ingestion)**

For each repo we consider **size**, **structure**, **content types**, and **fit for our pipeline** (clone → parse → chunk → metadata → embed). Complexity drives adapter effort, filtering logic, and duration.

| Repo | Size / languages | Structure & content | Ingestion complexity | What we use |
|------|------------------|----------------------|----------------------|-------------|
| **cow-sdk** | ~2.1M lines TS; ~7.6 MB | Monorepo: `packages/`, `docs/`, `examples/`, `src/`. Many subpackages (order-book, app-data, trading, cow-shed, etc.). | **High** — First TS monorepo; need to include README, `docs/`, `examples/`, and public API surface; exclude tests, config, lockfiles, build artifacts. Per-package chunking and blob URLs. | README, docs/, examples/, selected package sources (or JSDoc/export summary). |
| **composable-cow** | Solidity; ~8.5 MB | Foundry: `src/`, `test/`, `script/`, `lib/`. README ~25 KB (substantial). | **Medium–high** — Solidity + NatSpec; large README is very useful. Exclude test/, script/, broadcast/, out/. Chunk by contract or file. | README, src/ (contracts + NatSpec). |
| **hooks-trampoline** | Small; ~269 KB | Foundry: `src/`, `test/`, README ~4.7 KB. | **Low** — Few files; README + `src/`; straightforward Solidity. | README, src/. |
| **watch-tower** | TypeScript; ~1.5 MB | Service: `src/`, `abi/`, README ~8 KB, `config.json.example`. | **Medium** — TS codebase; README and config example are integration-relevant; exclude lockfiles. | README, config example, selected src/ (or key modules). |
| **flash-loan-router** | Solidity; ~2.5 MB | Foundry: `src/`, `test/`, README ~11 KB. | **Low–medium** — README is strong; Solidity + NatSpec; standard layout. | README, src/. |
| **cow-shed** | Solidity; ~3.9 MB | Contracts + tooling. | **Medium** — Solidity; filter to contracts + any user-facing docs. | README, contract sources. |
| **cow-py** | Python; ~820 KB | SDK: modules, README, docstrings. | **Medium** — Same language as our stack; docstrings and README; exclude tests. | README, main modules (docstrings + signatures). |
| **weiroll** | Very small; ~42 KB | Minimal Solidity/code. | **Low** — Tiny codebase; quick to ingest. | README, src/. |
| **contracts** (opt.) | Large Solidity; ~6.4 MB | Core GPv2 contracts; many files. | **High** — Raw Solidity can be noisy; may focus on NatSpec and high-level docs only. | NatSpec + selected interfaces; or README-only if scoped down. |
| **cowswap** (opt.) | Very large; ~192 MB | Frontend monorepo (TS/React). | **Very high** — App UI code; heavy filtering (e.g. SDK usage, order flow only); lots of noise for “integration” Q&A. | Scoped paths (e.g. SDK usage, order-related); or exclude. |
| **services** (opt.) | Rust; ~29 MB | Backend (orderbook, solvers, etc.). | **Very high** — Different language; Order Book API already in OpenAPI; rest is solver/infra, likely noisy for integrators. | Scoped (e.g. API-related docs only) or exclude. |

Durations and payments in the milestone table below reflect this complexity (and size). Optional repos (M4i–M4k) are only in scope if CoW approves them.

---

## Milestones

**Rate:** $3,000 USD per work week (Bleu). M4 durations are based on repo **size and ingestion complexity** (structure, content types, filtering; see complexity assessment above).

| Milestone | Description | Duration | Payment (USD) |
|-----------|-------------|----------|----------------|
| M1 — Model comparison & PoC improvements | Report on 2–3 model combos; improve FE/BE (refs, robustness, UX). Validates production stack before scaling. | 1 week | 3,000 |
| M2 — Chat in docs | Embed chat widget/panel in docs.cow.fi (or agreed subpath) | 1 week | 3,000 |
| M3 — CI (single repo) | Single-repo pipeline: docs + OpenAPI (and all configured sources) → ingest → rebuild index → deploy backend. No CI added to upstream repos. | 1 week | 3,000 |
| M4a — Ingest: cow-sdk | [cowprotocol/cow-sdk](https://github.com/cowprotocol/cow-sdk): TS monorepo (packages/docs/examples). **Complexity: high** — first TS adapter; filter to public API + docs + examples. | 1.5 weeks | 4,500 |
| M4b — Ingest: composable-cow | [cowprotocol/composable-cow](https://github.com/cowprotocol/composable-cow): Solidity + large README. **Complexity: medium–high** — NatSpec + README; exclude test/script. | 1.5 weeks | 4,500 |
| M4c — Ingest: hooks-trampoline | [cowprotocol/hooks-trampoline](https://github.com/cowprotocol/hooks-trampoline): Small Solidity + README. **Complexity: low**. | 0.5 week | 1,000 |
| M4d — Ingest: watch-tower | [cowprotocol/watch-tower](https://github.com/cowprotocol/watch-tower): TypeScript service + README + config example. **Complexity: medium**. | 0.5 week | 1,500 |
| M4e — Ingest: flash-loan-router | [cowprotocol/flash-loan-router](https://github.com/cowprotocol/flash-loan-router): Solidity + README. **Complexity: low–medium**. | 0.5 week | 1,500 |
| M4f — Ingest: cow-shed | [cowdao-grants/cow-shed](https://github.com/cowdao-grants/cow-shed): Solidity contracts. **Complexity: medium**. | 0.5 week | 1,500 |
| M4g — Ingest: cow-py | [cowdao-grants/cow-py](https://github.com/cowdao-grants/cow-py): Python SDK (docstrings, README). **Complexity: medium** — same stack as our pipeline. | 0.5 week | 1,000 |
| M4h — Ingest: weiroll | [cowdao-grants/weiroll](https://github.com/cowdao-grants/weiroll): Very small codebase. **Complexity: low**. | 0.5 week | 1,000 |
| M4i — Ingest: contracts (optional) | [cowprotocol/contracts](https://github.com/cowprotocol/contracts): Large Solidity core. **Complexity: high** — possible noise; NatSpec or high-level only. Only if CoW wants. | 1.5 weeks | 4,500 |
| M4j — Ingest: cowswap (optional) | [cowprotocol/cowswap](https://github.com/cowprotocol/cowswap): Very large frontend monorepo. **Complexity: very high** — heavy filtering; possible noise. Only if CoW wants. | 2 weeks | 6,000 |
| M4k — Ingest: services (optional) | [cowprotocol/services](https://github.com/cowprotocol/services): Large Rust backend. **Complexity: very high** — Order Book already in OpenAPI; solver/infra noise. Only if CoW wants. | 2 weeks | 6,000 |

**Core (M1 + M2 + M3):** 3 weeks, 9,000 USD. **M4 (per repo):** Duration and payment as above; CoW can approve or defer each repo independently. Optional repos (M4i–M4k) only if CoW includes them in scope.

---

## Specification

### M1: Model comparison and PoC improvements

- **Models:** Run golden questions against 2–3 embedding + chat combinations (e.g. OpenAI, Anthropic, Gemini variants, open-source). Report accuracy, latency, cost; recommend a production stack.
- **Backend:** Improve error handling, citation ordering (only cited refs), prompts; consider streaming if useful.
- **Frontend:** Improve references, formatting, accessibility; prepare for embedding in docs (layout, theming).
- **Deliverable:** Model comparison report and improved PoC (FE and BE). Validates the stack before embedding in docs and adding more sources.

### M2: Chat in docs

- Integrate the assistant **inside [docs.cow.fi](https://docs.cow.fi)** (or a dedicated subpath).
- Options: embeddable widget (iframe or component), or “Ask” panel/sidebar. Align with CoW’s docs stack (e.g. Docusaurus) and design.
- **Deliverable:** Chat usable in-context while browsing CoW documentation.

### M3: CI (single repo)

- **Single repository:** All CI lives in the grant repo. No CI jobs or webhooks are added to upstream repos (cowprotocol/docs, cow-sdk, etc.).
- **Pipeline:** On schedule or on trigger (e.g. manual or webhook to our repo), the pipeline: (1) clones or fetches all configured sources (docs, OpenAPI, and any M4 repos), (2) runs ingestion scripts per source, (3) rebuilds the unified FAISS index and keyword/question indices, (4) runs tests, (5) deploys or publishes the updated backend.
- **Deliverable:** One CI pipeline in the grant repo that keeps the chat index and deployment in sync with docs, OpenAPI, and all ingested repos.

### M4: Multi-repo ingestion (separate budget per repo)

All desired repos are in scope; each has its own milestone line (M4a–M4k) and budget. For each repo we deliver: ingestion adapter (clone/fetch → parse → chunk with metadata, e.g. URL to blob), integration into the unified index, and documentation. Optional repos (contracts, cowswap, services) are only implemented if CoW approves that line item.

- **M4a:** [cowprotocol/cow-sdk](https://github.com/cowprotocol/cow-sdk) — SDK usage, types, examples.
- **M4b:** [cowprotocol/composable-cow](https://github.com/cowprotocol/composable-cow) — Composable orders, conditional orders.
- **M4c:** [cowprotocol/hooks-trampoline](https://github.com/cowprotocol/hooks-trampoline) — Hooks integration.
- **M4d:** [cowprotocol/watch-tower](https://github.com/cowprotocol/watch-tower) — Monitoring / order status.
- **M4e:** [cowprotocol/flash-loan-router](https://github.com/cowprotocol/flash-loan-router) — Flash loans.
- **M4f:** [cowdao-grants/cow-shed](https://github.com/cowdao-grants/cow-shed) — Tooling / examples.
- **M4g:** [cowdao-grants/cow-py](https://github.com/cowdao-grants/cow-py) — Python SDK / examples.
- **M4h:** [cowdao-grants/weiroll](https://github.com/cowdao-grants/weiroll) — Weiroll usage.
- **M4i (optional):** [cowprotocol/contracts](https://github.com/cowprotocol/contracts) — Contract references; add only if CoW wants.
- **M4j (optional):** [cowprotocol/cowswap](https://github.com/cowprotocol/cowswap) — Frontend app; add only if CoW wants.
- **M4k (optional):** [cowprotocol/services](https://github.com/cowprotocol/services) — Backend/services; add only if CoW wants.

**Deliverable per repo:** RAG chunks and metadata in the unified index; doc for adding further repos. CoW can phase or skip repos by not approving the corresponding budget line.

---

## Method

**Technical approach:** Reuse the existing PoC stack (Quart, FAISS, ingestion scripts). Chat-in-docs is an integration layer (widget/iframe or sidebar) plus theming. All CI runs from the grant repo only (clone/fetch → ingest → build index → deploy); no CI is added to upstream repos. New sources follow the same chunking-and-embedding pattern as docs and OpenAPI; each repo has a separate budget line (M4a–M4k) so CoW can approve or phase them independently.

**Open source:** All code will remain open source. We’re open to feedback during implementation and will align with CoW’s standards.

**Flexibility:** We can phase scope (e.g. M1 first to validate stack; then M2 + M3; then M4a–M4k per repo) or drop optional items to match CoW’s roadmap and budget.

---

## Funding Request

We propose that milestone payments be released upon each milestone’s approval.

**Rate:** $3,000 USD per work week (Bleu). Core milestones M1–M3: 3 weeks = 9,000 USD. Each M4 repo has its own duration and payment (see table); total for M4 depends on which repos CoW approves (e.g. M4a–M4h only ≈ 17,000 USD; adding optional M4i–M4k adds 16,500 USD). Payment in xDAI or USDC at equivalent value. We’re happy to propose a concrete budget and timeline once priorities are fixed (e.g. embed + CI only vs. full scope including multi-repo and model comparison).

### Budget Breakdown

The budget includes the hourly rates of a developer during the execution and a project manager on a need basis. The xDAI part of the budget shall be paid after each milestone’s completion.

In addition, we request a 10k COW payment vested over 1 year to cover diluted maintenance and related costs for the same period. The vesting should be created once all the project milestones are completed.

### Gnosis Chain Address (to receive the grant)

0x5D40015034DA6cD75411c54dd826135f725c2498

---

## Other Information

- All the code will be open-source from day 0. We’re open to feedback during PRs as well.
- We’re happy to answer any questions and are open to feedback about this proposal.

---

## Terms and Conditions

By submitting this grant application, we acknowledge and agree to be bound by the CoW DAO Participation Agreement and the CoW Grant Terms and Conditions.

- [RFP: CoW Protocol Integration Documentation](https://forum.cow.fi/t/cow-protocol-integration-documentation/3360)
