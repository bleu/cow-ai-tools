# Quickstart: do primeiro order em &lt;10 min (CoW Protocol)

Guia mínimo para criar o primeiro order via Order Book API. Para dúvidas de parâmetro (slippage, buyAmount, approvals, erros), use o **chat desta PoC** ou a documentação oficial.

## Pré-requisitos

- Conta em rede suportada (ex.: [Sepolia](https://docs.cow.fi/cow-protocol/reference/smart-contracts/contract-addresses#sepolia)).
- Wallet com ETH para gas e token que pretende vender.
- Aprovação do token de venda para o [GPv2VaultRelayer](https://docs.cow.fi/cow-protocol/reference/smart-contracts/contract-addresses) (ver doc de [token approval](https://docs.cow.fi/cow-protocol/reference/smart-contracts/allowance)).

## Passos resumidos

1. **Obter um quote**  
   Chamar o endpoint de quote (ex.: `GET /api/v1/quote`) com `sellToken`, `buyToken`, `sellAmount` ou `buyAmount`, e `validTo`. Ver [Order Book API – Quote](https://docs.cow.fi/cow-protocol/reference/apis/orderbook#quote).

2. **Montar e assinar o order**  
   Usar o payload do quote (ou montar manualmente) com todos os campos obrigatórios (`sellToken`, `buyToken`, `sellAmount`, `buyAmount`, `validTo`, `appData`, etc.) e assinar com EIP-712. Ver [Order creation](https://docs.cow.fi/cow-protocol/reference/apis/orderbook#order-creation).

3. **Submeter o order**  
   `POST /api/v1/orders` com o body do order assinado. Base URLs: [mainnet](https://api.cow.fi) / [Sepolia](https://api.cow.fi) (ver [API base URLs](https://docs.cow.fi/cow-protocol/reference/apis/orderbook)).

4. **Acompanhar**  
   Usar o `orderUid` devolvido para consultar o status (endpoint de order status na API).

## Links úteis

- [Order Book API (docs.cow.fi)](https://docs.cow.fi/cow-protocol/reference/apis/orderbook)
- [Contract addresses (por rede)](https://docs.cow.fi/cow-protocol/reference/smart-contracts/contract-addresses)
- [Token approval](https://docs.cow.fi/cow-protocol/reference/smart-contracts/allowance)
- Chat desta PoC: use o frontend com `NEXT_PUBLIC_BRAND=cow` para perguntas sobre parâmetros, slippage, approvals e erros.

---

*Script de exemplo (ex.: Node/TS ou Python) que cria um order na Sepolia pode ser adicionado como extensão futura.*
