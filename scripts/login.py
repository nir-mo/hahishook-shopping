#!/usr/bin/env python3
"""Log in to hahishook.com with username + password and save the session.

Usage:  python3 login.py                 # prompts for credentials (no echo)
        HAHISHOOK_USER / HAHISHOOK_PASS in env → non-interactive (EC2 / cron)

Performs the WooCommerce My-Account login (no captcha on that form) and writes
the cookie jar so the other scripts reuse the authenticated session.
"""
import getpass
import os
import re
import sys
import urllib.parse
import urllib.request

from _http import make_opener, load_jar, save_jar, UA

BASE = "https://hahishook.com"
ACCOUNT = f"{BASE}/my-account/"
COOKIES = os.path.join(os.path.dirname(__file__), os.pardir, "cookies.txt")

NONCE_INPUT = re.compile(r'<input[^>]*name="woocommerce-login-nonce"[^>]*>')
VALUE = re.compile(r'value="([^"]+)"')


def get(opener, url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with opener.open(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


def post(opener, url, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "User-Agent": UA,
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": ACCOUNT,
        },
    )
    with opener.open(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


def find_nonce(html):
    tag = NONCE_INPUT.search(html)
    m = VALUE.search(tag.group(0)) if tag else None
    return m.group(1) if m else None


def logged_in(jar):
    return any(c.name.startswith("wordpress_logged_in") for c in jar)


def main():
    # env vars for automation (EC2 / Secrets Manager); prompt otherwise, which
    # keeps the password out of shell history and `ps` output.
    user = os.environ.get("HAHISHOOK_USER") or input("hahishook username: ").strip()
    pw = os.environ.get("HAHISHOOK_PASS") or getpass.getpass("hahishook password: ")
    if not user or not pw:
        sys.exit("username and password required")

    jar = load_jar(COOKIES)
    opener = make_opener(jar)

    nonce = find_nonce(get(opener, ACCOUNT))  # GET also seeds session cookies
    if not nonce:
        sys.exit("could not find the login nonce on /my-account/ (layout changed?)")

    post(
        opener,
        ACCOUNT,
        {
            "username": user,
            "password": pw,
            "rememberme": "forever",
            "woocommerce-login-nonce": nonce,
            "_wp_http_referer": "/my-account/",
            "hh_login_method": "password",
            "login": "Log in",
        },
    )

    if not logged_in(jar):
        sys.exit("login failed — no wordpress_logged_in cookie set (check credentials)")

    save_jar(jar)
    print(f"logged in as {user}; session saved to {os.path.relpath(COOKIES)}")


if __name__ == "__main__":
    main()
