#!/usr/bin/env python3
"""Read the current hahishook cart using the saved authenticated session.

Shows what's in your account cart (what add_to_cart.py built) so you can review
before paying. Run login.py first.

Usage:  read_cart.py
"""
import os
import sys
import json
import html
import urllib.request

from _http import make_opener, load_jar, data_path, UA

CART = "https://hahishook.com/wp-json/wc/store/v1/cart"
CART_URL = "https://hahishook.com/cart/"
COOKIES = data_path("cookies.txt")


def get_cart(opener):
    req = urllib.request.Request(CART, headers={"User-Agent": UA})
    with opener.open(req, timeout=30) as r:
        return json.load(r)


def shekels(obj):
    """Convert a Store API minor-unit total to shekels, or None if absent."""
    try:
        minor = int(obj.get("currency_minor_unit", 2))
        return int(obj["total_price" if "total_price" in obj else "line_total"]) / (10 ** minor)
    except (KeyError, ValueError, TypeError):
        return None


def main():
    jar = load_jar(COOKIES)
    if not any(c.name.startswith("wordpress_logged_in") for c in jar):
        sys.exit("not logged in — run login.py first (no wordpress_logged_in cookie)")
    opener = make_opener(jar)

    cart = get_cart(opener)
    items = cart.get("items") or []
    if not items:
        print("cart is empty")
        return

    for it in items:
        price = shekels(it.get("totals") or {})
        price_s = f"₪{price:.2f}" if price is not None else "?"
        name = html.unescape(it.get("name", ""))
        print(f"{it.get('id')}\tx{it.get('quantity')}\t{price_s}\t{name}")

    total = shekels(cart["totals"])
    total_s = f"₪{total:.2f}" if total is not None else "?"
    print(f"\ncart: {cart['items_count']} items, {total_s}")
    print(f"pay here (same account): {CART_URL}")


if __name__ == "__main__":
    main()
