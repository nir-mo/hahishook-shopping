#!/usr/bin/env python3
"""Shared HTTP helpers for the hahishook scripts.

- ssl_context(): TLS verification that works on the python.org macOS build
  (which doesn't link system root certs) via certifi, falling back to the
  system default (e.g. on EC2 where system certs verify fine).
- a cookie-jar-backed opener + load/save for the authenticated flows.
"""
import ssl
import http.cookiejar
import urllib.request

UA = "hahishook-skill/0.1"


def ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def make_opener(jar):
    """URL opener that persists cookies into `jar` and verifies TLS.

    Passing our own HTTPSHandler replaces urllib's default one (so the context
    is used); the cookie processor is added; the default redirect handler stays,
    so login's 302 is followed and its Set-Cookie headers are captured.
    """
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar),
        urllib.request.HTTPSHandler(context=ssl_context()),
    )


def load_jar(path):
    """Netscape-format cookie jar (also readable by curl).

    Missing file → empty jar (log in to create it). Corrupt/truncated file →
    also an empty jar rather than a crash, so a bad cookies.txt just means
    "log in again".
    """
    jar = http.cookiejar.MozillaCookieJar(path)
    try:
        jar.load(ignore_discard=True, ignore_expires=True)
    except (FileNotFoundError, http.cookiejar.LoadError):
        pass
    return jar


def save_jar(jar):
    # ignore_discard: keep session cookies (the woo session has no expiry)
    jar.save(ignore_discard=True, ignore_expires=True)
