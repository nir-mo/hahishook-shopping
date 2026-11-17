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

### Remove from the cart — reuses the saved session
```
python3 scripts/remove_item.py <id> [<id> ...]
```
Removes the matching line(s) from the built cart by product id. (To drop
something from the weekly list *before* checkout, edit `list.json` — see below.)

## Handoff

Items go into the user's account cart. They open `https://hahishook.com/cart/`
in their own browser (same account) → WooCommerce loads the persisted cart →
they pay. The "link" is just `/cart/`.

## State lives in ~/.hahishook/ — never in the skill directory

All per-user state goes in `~/.hahishook/` (override with the `HAHISHOOK_HOME`
env var). The scripts already put `cookies.txt` there; keep `list.json` and
`usuals.json` there too. The skill directory is pure code — every user who
installs it gets their own session and list automatically.

## Day-to-day list (conversational)

The agent keeps two JSON files in `~/.hahishook/` and edits them directly —
they are state, not scripts (don't wrap them in CRUD scripts):

- `~/.hahishook/list.json` — the current cart-to-be:
  `[{"id": 178225, "qty": 2, "name": "אורז בסמטי"}]`
- `~/.hahishook/usuals.json` — remembered picks so a name resolves without
  re-asking: `{"coffee": 259946, "rice": 178225}`

Handle messages like "add coffee", "remove milk", "checkout":

- **add X** — if `X` is in `usuals.json`, append its id to `list.json` (bump the
  qty if it's already there). If not, run `search.py X`, choose the best match,
  append it, and record `X → id` in `usuals.json` so next time is one-shot.
- **remove X** — drop the matching entry from `list.json`.
- **checkout** (or end of week) — run `login.py` if needed, then `add_to_cart.py`
  with every `list.json` item, send the user the `/cart/` link, and clear
  `list.json`.

`remove_item.py` is for pulling something out of the *already-built* cart (after
checkout); a day-to-day "remove" just edits `list.json`.

## Extending

Need an operation the scripts don't cover yet (e.g. pull the bulk price feed)? Add a script under `scripts/` — see `_http.py` for
the shared TLS + cookie helpers and the existing scripts for the request
pattern. The endpoint knowledge lives in the code, not in this file.
