# CoW PoC – Golden Questions (Fase 3)

Perguntas de referência para validar o assistente nas áreas prioritárias da RFP. Use para avaliação manual ou em scripts de regressão.

## Order creation (slippage, amounts)

1. How do I set buyAmount with slippage when creating an order?
2. Does buyAmount include slippage or do I have to pack it in myself?
3. What format should sellAmount and buyAmount use (wei, decimal)?
4. How do I create a limit order via the Order Book API?
5. What is validTo and how do I set it correctly?
6. How do I compute or pass appData / appDataHash when creating an order?

## Approval setup (ABI, relay, gasless)

7. How do I set token approval via ABI for a gasless swap?
8. What is the GPv2VaultRelayer and where do I find its address per chain?
9. How do I configure approval for the CoW Protocol relayer?
10. What signing scheme should I use for orders (eip712, etc.)?

## Quoting (fast vs optimal)

11. When should I use fast vs optimal quoting?
12. What is the difference between fast, optimal, and verified price quality?
13. How do I get a quote before creating an order?
14. How long is a quote valid and when should I request a new one?

## Errors and troubleshooting

15. What does InsufficientBalance mean and how do I fix it?
16. What does "No route was found for the specified order" mean?
17. What does OrderPostError 400 mean?
18. How do I interpret and handle 429 (rate limit) from the API?
19. What does "Invalid signature" (401) mean when submitting an order?

## Endpoints and usage

20. What endpoint do I use to create an order?
21. What endpoint do I use to get a quote?
22. How do I cancel an order (on-chain vs off-chain)?
23. What are the base URLs for mainnet and Sepolia?
24. How do I get the status of an order after submitting it?

---

**Critérios de sucesso (sugerido):** a resposta deve citar a documentação ou o spec (docs.cow.fi / Order Book API), ser precisa em nível de parâmetro quando aplicável, e não inventar endpoints ou comportamentos.
