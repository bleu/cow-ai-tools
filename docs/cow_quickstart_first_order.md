# Quickstart: First Order in <10 min (CoW Protocol)

Minimal guide to create your first order via the Order Book API. For parameter questions (slippage, buyAmount, approvals, errors), use this **PoC chat** or the official documentation.

## Prerequisites

- Account on a supported network (e.g. [Sepolia](https://docs.cow.fi/cow-protocol/reference/smart-contracts/contract-addresses#sepolia)).
- Wallet with ETH for gas and the token you want to sell.
- Approval of the sell token for the [GPv2VaultRelayer](https://docs.cow.fi/cow-protocol/reference/smart-contracts/contract-addresses) (see [token approval](https://docs.cow.fi/cow-protocol/reference/smart-contracts/allowance) doc).

## Steps summary

1. **Get a quote**  
   Call the quote endpoint (e.g. `GET /api/v1/quote`) with `sellToken`, `buyToken`, `sellAmount` or `buyAmount`, and `validTo`. See [Order Book API – Quote](https://docs.cow.fi/cow-protocol/reference/apis/orderbook#quote).

2. **Build and sign the order**  
   Use the quote payload (or build manually) with all required fields (`sellToken`, `buyToken`, `sellAmount`, `buyAmount`, `validTo`, `appData`, etc.) and sign with EIP-712. See [Order creation](https://docs.cow.fi/cow-protocol/reference/apis/orderbook#order-creation).

3. **Submit the order**  
   `POST /api/v1/orders` with the signed order body. Base URLs: [mainnet](https://api.cow.fi) / [Sepolia](https://api.cow.fi) (see [API base URLs](https://docs.cow.fi/cow-protocol/reference/apis/orderbook)).

4. **Track**  
   Use the returned `orderUid` to check status (order status endpoint on the API).

## Useful links

- [Order Book API (docs.cow.fi)](https://docs.cow.fi/cow-protocol/reference/apis/orderbook)
- [Contract addresses (by network)](https://docs.cow.fi/cow-protocol/reference/smart-contracts/contract-addresses)
- [Token approval](https://docs.cow.fi/cow-protocol/reference/smart-contracts/allowance)
- This PoC chat: use the frontend with `NEXT_PUBLIC_BRAND=cow` for questions on parameters, slippage, approvals and errors.

---

*An example script (e.g. Node/TS or Python) that creates an order on Sepolia may be added as a future extension.*
