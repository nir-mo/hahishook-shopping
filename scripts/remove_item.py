#!/usr/bin/env python3
"""Remove products from the hahishook cart (by product id) using the saved session.

Removes the cart line(s) whose product id matches, from your account cart. This
edits the *built* cart; to drop something from the weekly list before checkout,
just edit list.json (no script needed).

Usage:  remove_item.py <id> [<id> ...]
"""
import os
import sys
import json
import urllib.request
import urllib.error

from _http import make_opener, load_jar, data_path, UA

BASE = "https://hahishook.com/wp-json/wc/store/v1"
CART = f"{BASE}/cart"
REMOVE = f"{BASE}/cart/remove-item"
CART_URL = "https://hahishook.com/cart/"
COOKIES = data_path("cookies.txt")


def get_cart(opener):
    req = urllib.request.Request(CART, headers={"User-Agent": UA})
    with opener.open(req, timeout=30) as r:
        return json.load(r), r.headers.get("Nonce")


def remove(opener, nonce, key):
    body = json.dumps({"key": key}).encode()
    req = urllib.request.Request(
        REMOVE,
        data=body,
        headers={"User-Agent": UA, "Content-Type": "application/json", "Nonce": nonce},
    )
    with opener.open(req, timeout=30) as r:
        return json.load(r), r.headers.get("Nonce", nonce)


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: remove_item.py <id> [<id> ...]")
    try:
        ids = [int(a) for a in sys.argv[1:]]
    except ValueError:
        sys.exit("ids must be integers, e.g. remove_item.py 259946")

    jar = load_jar(COOKIES)
    if not any(c.name.startswith("wordpress_logged_in") for c in jar):
        sys.exit("not logged in — run login.py first (no wordpress_logged_in cookie)")
    opener = make_opener(jar)

    cart, nonce = get_cart(opener)
    # product id -> cart line key(s)
    keys = {}
    for it in cart.get("items") or []:
        keys.setdefault(it["id"], []).append(it["key"])

    for pid in ids:
        if pid not in keys:
            print(f"not in cart: {pid}")
            continue
        for key in keys[pid]:
            try:
                cart, nonce = remove(opener, nonce, key)
                print(f"removed {pid}")
            except urllib.error.HTTPError as e:
                msg = json.loads(e.read() or b"{}").get("message", e.reason)
                print(f"FAILED  {pid}: {msg}")

    if cart.get("items"):
        totals = cart["totals"]
        minor = int(totals.get("currency_minor_unit", 2))
        total = int(totals["total_price"]) / (10 ** minor)
        print(f"\ncart: {cart['items_count']} items, ₪{total:.2f}")
    else:
        print("\ncart is empty")
    print(f"cart: {CART_URL}")


if __name__ == "__main__":
    main()
