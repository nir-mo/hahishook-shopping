#!/usr/bin/env python3
"""Search hahishook.com products via the WooCommerce Store API (no auth).

Usage:  search.py <hebrew-term> [per_page]
Output: <id>\t<₪price>\t<name>   (one product per line)

Stdlib only — runs as-is on macOS and on EC2.
"""
import sys
import json
import html
import urllib.parse
import urllib.request

from _http import ssl_context, UA

BASE = "https://hahishook.com/wp-json/wc/store/v1/products"


def search(term, per_page=20):
    q = urllib.parse.urlencode({"search": term, "per_page": per_page})
    req = urllib.request.Request(f"{BASE}?{q}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30, context=ssl_context()) as r:
        return json.load(r)


def price_shekels(product):
    """Store API prices are in minor units (agorot); convert to shekels."""
    prices = product.get("prices") or {}
    try:
        minor = int(prices.get("currency_minor_unit", 2))
        return int(prices["price"]) / (10 ** minor)
    except (KeyError, ValueError, TypeError):
        return None


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: search.py <term> [per_page]")
    term = sys.argv[1]
    per_page = int(sys.argv[2]) if len(sys.argv) > 2 else 20

    for product in search(term, per_page):
        price = price_shekels(product)
        price_s = f"₪{price:.2f}" if price is not None else "?"
        name = html.unescape(product.get("name", ""))
        print(f"{product.get('id')}\t{price_s}\t{name}")


if __name__ == "__main__":
    main()
