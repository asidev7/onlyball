#!/usr/bin/env python3
"""Offline verifier for an OnlyBall drawing.

Usage:
    python verify_draw.py <draw_id> [--base-url https://your-onlyball-site]

Fetches /api/draws/<draw_id>/ and independently recomputes the winning
ticket number from the revealed server_seed, snapshot_hash and beacon,
using the exact same algorithm as the server (see core/services/fairness.py
compute_winning_number):

    winning_number = int(HMAC_SHA256(key=server_seed, msg=snapshot_hash + beacon), 16) % total_tickets

No third-party dependencies are required beyond the Python standard library.
"""
import argparse
import hashlib
import hmac
import json
import sys
import urllib.request


def compute_winning_number(server_seed_hex: str, snapshot_hash_hex: str, beacon_blockhash: str, total_tickets: int) -> int:
    key = bytes.fromhex(server_seed_hex)
    msg = (snapshot_hash_hex + beacon_blockhash).encode('utf-8')
    digest = hmac.new(key, msg, hashlib.sha256).hexdigest()
    return int(digest, 16) % total_tickets


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('draw_id', type=int)
    parser.add_argument('--base-url', default='http://localhost:8000')
    args = parser.parse_args()

    url = f'{args.base_url.rstrip("/")}/api/draws/{args.draw_id}/'
    with urllib.request.urlopen(url) as resp:
        draw = json.load(resp)

    if draw['status'] not in ('drawn', 'paid'):
        print(f"Drawing {args.draw_id} has not been revealed yet (status={draw['status']}).")
        sys.exit(1)

    computed_hash = hashlib.sha256(bytes.fromhex(draw['server_seed'])).hexdigest()
    hash_ok = computed_hash == draw['server_seed_hash']

    computed_number = compute_winning_number(
        draw['server_seed'], draw['snapshot_hash'], draw['beacon_blockhash'], draw['total_tickets'],
    )
    number_ok = computed_number == draw['winning_number']

    print(f"Draw {args.draw_id} ({draw['draw_date']})")
    print(f"  server_seed_hash matches SHA-256(server_seed): {hash_ok}")
    print(f"  computed winning_number: {computed_number}")
    print(f"  published winning_number: {draw['winning_number']}")
    print(f"  match: {number_ok}")
    print(f"  winner: {draw.get('winner')}")
    print(f"  payout_tx: {draw.get('payout_tx') or '(credited to internal balance)'}")

    sys.exit(0 if (hash_ok and number_ok) else 2)


if __name__ == '__main__':
    main()
