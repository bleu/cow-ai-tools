# CoW AI – Test Questions

Use these to validate the RAG: **in-docs** questions should be answered with citations; **out-of-docs** questions should get a polite out-of-scope or “I don’t have that in the context” response (no invented endpoints or behavior).

---

## In documentation (should answer with references)

### Order creation (amounts, slippage, limit orders)

1. How do I set buyAmount with slippage when creating an order?
2. Does buyAmount include slippage or do I have to pack it in myself?
3. What format should sellAmount and buyAmount use (wei, decimal)?
4. How do I create a limit order via the Order Book API?
5. What is validTo and how do I set it correctly?
6. How do I compute or pass appData / appDataHash when creating an order?

### Approval (ABI, relayer, gasless)

7. How do I set token approval via ABI for a gasless swap?
8. What is the GPv2VaultRelayer and where do I find its address per chain?
9. How do I configure approval for the CoW Protocol relayer?
10. What signing scheme should I use for orders (eip712, etc.)?

### Quoting (fast vs optimal)

11. When should I use fast vs optimal quoting?
12. What is the difference between fast, optimal, and verified price quality?
13. How do I get a quote before creating an order?
14. How long is a quote valid and when should I request a new one?

### Errors and troubleshooting

15. What does InsufficientBalance mean and how do I fix it?
16. What does "No route was found for the specified order" mean?
17. What does OrderPostError 400 mean?
18. How do I interpret and handle 429 (rate limit) from the API?
19. What does "Invalid signature" (401) mean when submitting an order?

### Endpoints and usage

20. What endpoint do I use to create an order?
21. What endpoint do I use to get a quote?
22. How do I cancel an order (on-chain vs off-chain)?
23. What are the base URLs for mainnet and Sepolia?
24. How do I get the status of an order after submitting it?

---

## Not in documentation (should refuse or say “I don’t have that”)

Use these to check that the AI does **not** invent answers or endpoints.

### Out of scope (per RFP: not in docs we index)

25. How does the CoW Solver work internally?
26. How do I integrate with MEV Blocker?
27. Where is the documentation for migrating from CoW AMM to Order Book?
28. What are the CoW DAO governance proposals for next quarter?
29. How do I use the CoW SDK for mobile apps? (if not in indexed docs)

### Unrelated to CoW / wrong product

30. How do I create an order on Uniswap?
31. What is the Optimism governance process?
32. How do I get a quote from 1inch API?
33. What is the Curve Finance pool address for USDC/ETH?

### Fake or non-existent API details

34. What does the POST /v1/orders/advanced endpoint return?
35. How do I use the slippageTolerancePercent field in the order body?
36. What is the rate limit for GET /v1/health?
37. Does the API support the legacy /v0/quote endpoint?

### Too specific / not documentable

38. What was the exact gas cost of order 0x123... on mainnet yesterday?
39. Will the Order Book API add WebSocket support next month?
40. What is the recommended sellAmount for a 1000 USDC swap on Sepolia right now?

---

## How to use

- **In-docs (1–24):** Expect an answer that cites docs.cow.fi or the Order Book API; no made-up parameters or paths.
- **Out-of-docs (25–40):** Expect “I can only answer about CoW Protocol / Order Book API / docs”, or “I don’t have that in the provided context”, or a short refusal—not a confident fake answer.

If the model invents endpoint paths, parameter names, or behaviors not in the context, treat that as a failure and tighten the responder instructions or retrieval.
