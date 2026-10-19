#!/usr/bin/env python3
"""Utility script to verify and fetch metadata for Wrist & Hand clinical cards.
Checks:
- DOI registration via doi.org handle API
- Open-access full text verification on PMC / journals
- YouTube oEmbed verification (status 200, retrieves exact title)
"""
import sys, json, urllib.request, urllib.parse, re

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'}

def verify_doi(doi):
    clean = doi.strip()
    if 'doi.org/' in clean:
        clean = clean.split('doi.org/', 1)[1]
    clean = urllib.parse.unquote(clean)
    api = 'https://doi.org/api/handles/' + urllib.parse.quote(clean, safe='/:;()')
    try:
        req = urllib.request.Request(api, headers=UA)
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.load(r)
            return d.get('responseCode') == 1
    except Exception as e:
        print(f"Error checking DOI {clean}: {e}")
        return False

def verify_youtube(url):
    api = f"https://www.youtube.com/oembed?url={urllib.parse.quote(url)}&format=json"
    try:
        req = urllib.request.Request(api, headers=UA)
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.load(r)
            return True, d.get('title')
    except Exception as e:
        return False, None

def check_url(url):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 200
    except Exception:
        return False

if __name__ == '__main__':
    print("Source verifier loaded.")
