"""Wallet-based authentication: issue a one-time nonce, then verify a
signature over that nonce to prove control of the address.

Three signature schemes are supported: native Solana wallets (Phantom/
Solflare/Trust Wallet, ed25519), MetaMask/EVM wallets (secp256k1 /
Ethereum's `personal_sign`), and TronLink (also secp256k1, but with a
different message prefix and a base58check address instead of 0x-hex --
see verify_tron_signature).
"""
import hashlib

import base58
from django.utils import timezone

NONCE_TTL_SECONDS = 5 * 60


def nonce_message(nonce: str) -> str:
    return f'Sign this message to log in to OnlyBall.\nNonce: {nonce}'


def is_nonce_fresh(wallet_link) -> bool:
    if not wallet_link.nonce_created_at:
        return False
    age = (timezone.now() - wallet_link.nonce_created_at).total_seconds()
    return age <= NONCE_TTL_SECONDS


def verify_solana_signature(address: str, message: str, signature_b58: str) -> bool:
    """ed25519 verification for Phantom / Solflare / Trust Wallet (Solana)."""
    try:
        from nacl.exceptions import BadSignatureError
        from nacl.signing import VerifyKey

        pubkey_bytes = base58.b58decode(address)
        signature_bytes = base58.b58decode(signature_b58)
        VerifyKey(pubkey_bytes).verify(message.encode('utf-8'), signature_bytes)
        return True
    except BadSignatureError:
        return False
    except Exception:
        return False


def verify_evm_signature(address: str, message: str, signature_hex: str) -> bool:
    """secp256k1 `personal_sign` verification for MetaMask / WalletConnect
    (EVM-style address).
    """
    try:
        from eth_account import Account
        from eth_account.messages import encode_defunct

        recovered = Account.recover_message(encode_defunct(text=message), signature=signature_hex)
        return recovered.lower() == address.lower()
    except Exception:
        return False


def _eth_address_to_tron(eth_address_hex: str) -> str:
    """Tron reuses secp256k1 + Keccak256 exactly like Ethereum -- an
    address is the same last-20-bytes-of-pubkey-hash -- but encodes it as
    base58check with a 0x41 prefix byte instead of 0x-hex + EIP-55.
    """
    raw = bytes.fromhex(eth_address_hex[2:] if eth_address_hex.startswith('0x') else eth_address_hex)
    payload = b'\x41' + raw
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    return base58.b58encode(payload + checksum).decode()


def _tron_message_digest(message: str) -> bytes:
    """TronWeb's trx.signMessageV2 (TIP-191) is NOT Ethereum's personal_sign
    with a different prefix string -- it's a genuinely different, two-step
    hash:

        digest  = keccak256(utf8(message))
        result  = keccak256(b"\\x19TRON Signed Message:\\n32" + digest)

    The "32" in the header is the *digest's* fixed length, not the
    original message's length -- it never changes regardless of message
    size. Treating this like Ethereum's single-hash, variable-length-
    prefix scheme (as an earlier version of this function did) recovers
    the wrong public key for every message and fails verification 100% of
    the time, no matter how correct the address math is.
    """
    from eth_utils import keccak

    digest = keccak(message.encode('utf-8'))
    return keccak(b'\x19TRON Signed Message:\n32' + digest)


def verify_tron_signature(address: str, message: str, signature_hex: str) -> bool:
    """secp256k1 verification for TronLink's trx.signMessageV2 (TIP-191).
    See _tron_message_digest for the hashing scheme; the address is
    recovered the same way as Ethereum (last 20 bytes of the pubkey's
    Keccak256), just re-encoded as a Tron base58check address.
    """
    try:
        from eth_keys import keys

        sig_bytes = bytes.fromhex(signature_hex[2:] if signature_hex.startswith('0x') else signature_hex)
        if len(sig_bytes) != 65:
            return False
        r = int.from_bytes(sig_bytes[0:32], 'big')
        s = int.from_bytes(sig_bytes[32:64], 'big')
        v = sig_bytes[64]
        v = v - 27 if v >= 27 else v

        signature = keys.Signature(vrs=(v, r, s))
        pubkey = signature.recover_public_key_from_msg_hash(_tron_message_digest(message))
        return _eth_address_to_tron(pubkey.to_checksum_address()) == address
    except Exception:
        return False


def verify_wallet_signature(provider: str, address: str, message: str, signature: str) -> bool:
    from ..models import WalletLink

    if provider == WalletLink.Provider.METAMASK:
        return verify_evm_signature(address, message, signature)
    if provider == WalletLink.Provider.TRONLINK:
        return verify_tron_signature(address, message, signature)
    return verify_solana_signature(address, message, signature)
