---
name: hahishook-shopping
description: Build a weekly grocery cart on hahishook.com (Israeli nonprofit grocery store, WooCommerce). Use when the user wants to search products, add items to a shopping list, or assemble a cart to check out. Product names are in Hebrew.
---

# Hahishook shopping

hahishook.com (החישוק) is a nonprofit grocery store running on WooCommerce. Its
WooCommerce **Store API** is public for reads, and the cart binds to a logged-in
account — so the user pays from their own browser, and no payment is automated.

## Endpoints (all verified against the live site)

### Search / resolve product IDs — no auth
```
GET /wp-json/wc/store/v1/products?search=<term>&per_page=20
→ [{ id, name, prices:{ price, currency_minor_unit }, permalink }]
```
Prices are in **minor units** (agorot): shekels = `price / 10**currency_minor_unit`.

### Cart — Store API
```
GET  /wp-json/wc/store/v1/cart           → response headers carry Cart-Token (JWT) + Nonce
POST /wp-json/wc/store/v1/cart/add-item  body {"id":<id>,"quantity":<n>}
     headers: Cart-Token + Nonce   (guest cart)
     — OR send logged-in cookies   (binds cart to the account)  ← what we use
```

### Login — standard WooCommerce form, NO captcha on the login form
```
GET  /my-account/   → scrape `woocommerce-login-nonce` + session cookies
POST /my-account/   fields:
       username, password, rememberme=forever,
       woocommerce-login-nonce=<nonce>, _wp_http_referer=/my-account/,
       hh_login_method=password, login=Log in
→ sets wordpress_logged_in_* cookies. Reuse that cookie jar on Store API calls
  and the cart persists to the user's account.
```
Login is fully scriptable (no captcha) → the EC2 agent re-logs-in whenever the
cookie expires. Store credentials in a secret store, never in the repo.

### Daily price feed — official, owner-published
```
GET /wp-content/uploads/chp/YYYYMMDD.tsv
cols: 0 itemcode  1 price  2 disc_price  3 capacity  4 deeplink
      5 short_name  6 units  8 image  9 leading_barcodes  10 similar_barcodes
```
Use for bulk prices / catalog. Only `leading_barcodes` set prices.

## Handoff model
Build into the **account** cart (logged in). The user opens
`https://hahishook.com/cart/` in their own browser (same account) → WooCommerce
loads the persisted cart → they pay. The "link" is just `/cart/`.
**Never automate payment.**

## Weekly flow
List-as-data all week → materialize the cart once at the end:
1. Agent searches and appends `{id, qty, name}` to `list.json` over the week.
2. End-of-week: log in, add every item to the account cart.
3. Notify the user: "cart ready → hahishook.com/cart/".

## Scripts
- `scripts/search.py <term> [per_page]` — product search (id / price / name), no auth.
- `scripts/login.py` — log in (HAHISHOOK_USER / HAHISHOOK_PASS env vars), saves `cookies.txt`.
- `scripts/add_to_cart.py <id>:<qty> ...` — add items to your account cart (reuses `cookies.txt`); prints the `/cart/` link.
  _(coming: build_list.py — weekly list.json accumulation)_
