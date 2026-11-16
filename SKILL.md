---
name: hahishook-shopping
description: Build a weekly grocery cart on hahishook.com (Israeli nonprofit grocery store, WooCommerce). Use when the user wants to search products, add items to a shopping list, or assemble a cart to check out. Product names are in Hebrew.
---

# Hahishook shopping

hahishook.com (החישוק) is a nonprofit grocery store on WooCommerce. This skill
searches products, logs in with the user's account, and builds a cart they pay
for in their own browser. **Never automate payment.**

## The scripts are the interface

Do everything through these scripts (run with `python3`) and read their
plain-text output. They encode the details you'd otherwise get wrong by hand —
TLS on the macOS python.org build, the login and cart nonces, cookie reuse, and
minor-unit price math. Don't hand-roll HTTP.

### Search — no login needed
```
python3 scripts/search.py "<hebrew term>" [per_page]
```
One product per line: `<id><TAB>₪<price><TAB><name>`. Use `<id>` for the cart.
A `₪0.00` price means a variable/unpurchasable product — skip it.

### Log in — saves the session to cookies.txt
```
python3 scripts/login.py
```
Prompts for credentials (no echo). For automation, set `HAHISHOOK_USER` /
`HAHISHOOK_PASS` in the environment and it runs non-interactively. The saved
session lasts ~14 days; re-run when it expires.

### Add to cart — reuses the saved session
```
python3 scripts/add_to_cart.py <id>:<qty> [<id>:<qty> ...]
```
Adds items to the user's **account** cart and prints the totals plus the
`/cart/` link. Requires a valid `cookies.txt` (run `login.py` first).

### Read the cart — reuses the saved session
```
python3 scripts/read_cart.py
```
Prints the current account cart (`<id><TAB>x<qty><TAB>₪<line><TAB><name>`) plus
the total and the `/cart/` link, or `cart is empty`. Requires `cookies.txt`.

## Handoff

Items go into the user's account cart. They open `https://hahishook.com/cart/`
in their own browser (same account) → WooCommerce loads the persisted cart →
they pay. The "link" is just `/cart/`.

## Weekly flow

List-as-data all week → materialize the cart once at the end:
1. Search and append `{id, qty, name}` to `list.json` over the week.
2. End-of-week: run `login.py`, then `add_to_cart.py` for every item.
3. Tell the user: "cart ready → hahishook.com/cart/".

## Extending

Need an operation the scripts don't cover yet (remove an item, or pull the
bulk price feed)? Add a script under `scripts/` — see `_http.py` for
the shared TLS + cookie helpers and the existing scripts for the request
pattern. The endpoint knowledge lives in the code, not in this file.
