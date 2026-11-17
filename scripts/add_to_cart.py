#!/usr/bin/env python3
"""Add items to the hahishook cart using the saved authenticated session.

Because the session is logged in (cookies.txt), the cart binds to your account —
open https://hahishook.com/cart/ in your browser (same account) to pay.

Usage:  add_to_cart.py <id>:<qty> [<id>:<qty> ...]
        add_to_cart.py 178225:2 259946:1
"""
import os
import sys
import json
import urllib.request
import urllib.error

from _http import make_opener, load_jar, data_path, UA

BASE = "https://hahishook.com/wp-json/wc/store/v1"
CART = f"{BASE}/cart"
ADD = f"{BASE}/cart/add-item"
CART_URL = "https://hahishook.com/cart/"
COOKIES = data_path("cookies.txt")


def parse_items(args):
    items = []
    for a in args:
        try:
            pid, qty = a.split(":")
            items.append((int(pid), int(qty)))
        except ValueError:
            sys.exit(f"bad item '{a}' — use <id>:<qty>, e.g. 178225:2")
    return items


def get_nonce(opener):
    """A cart-mutating request needs the Store API nonce; GET /cart returns it."""
    req = urllib.request.Request(CART, headers={"User-Agent": UA})
    with opener.open(req, timeout=30) as r:
        return r.headers.get("Nonce")


def add_item(opener, nonce, pid, qty):
    body = json.dumps({"id": pid, "quantity": qty}).encode()
    req = urllib.request.Request(
        ADD,
        data=body,
        headers={"User-Agent": UA, "Content-Type": "application/json", "Nonce": nonce},
    )
    with opener.open(req, timeout=30) as r:
        # each response carries a fresh nonce for the next request
        return json.load(r), r.headers.get("Nonce", nonce)


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: add_to_cart.py <id>:<qty> [<id>:<qty> ...]")
    items = parse_items(sys.argv[1:])

    jar = load_jar(COOKIES)
    if not any(c.name.startswith("wordpress_logged_in") for c in jar):
        sys.exit("not logged in — run login.py first (no wordpress_logged_in cookie)")
    opener = make_opener(jar)

    nonce = get_nonce(opener)
    if not nonce:
        sys.exit("no cart nonce returned from /cart — session may have expired")

    cart = None
    for pid, qty in items:
        try:
            cart, nonce = add_item(opener, nonce, pid, qty)
            print(f"added  {pid} x{qty}")
        except urllib.error.HTTPError as e:
            msg = json.loads(e.read() or b"{}").get("message", e.reason)
            print(f"FAILED {pid} x{qty}: {msg}")

    if cart:
        totals = cart["totals"]
        minor = int(totals.get("currency_minor_unit", 2))
        total = int(totals["total_price"]) / (10 ** minor)
        print(f"\ncart: {cart['items_count']} items, ₪{total:.2f}")
        print(f"pay here (same account): {CART_URL}")


if __name__ == "__main__":
    main()
