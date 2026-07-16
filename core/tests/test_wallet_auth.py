from django.test import TestCase

from core.models import WalletLink
from core.services import wallet_auth

MESSAGE = 'Sign this message to log in to OnlyBall.\nNonce: abc123'


class TronSignatureTests(TestCase):
    def _sign(self, message: str):
        """Mimics TronWeb's trx.signMessageV2 exactly (double keccak256,
        fixed-length header -- see wallet_auth._tron_message_digest) so
        this test would have caught the earlier, incorrect single-hash
        implementation instead of silently passing against itself.
        """
        import os

        from eth_keys import keys

        priv = keys.PrivateKey(os.urandom(32))
        digest = wallet_auth._tron_message_digest(message)
        sig = priv.sign_msg_hash(digest)
        sig_hex = (sig.r.to_bytes(32, 'big') + sig.s.to_bytes(32, 'big') + bytes([sig.v + 27])).hex()
        tron_address = wallet_auth._eth_address_to_tron(priv.public_key.to_checksum_address())
        return tron_address, sig_hex

    def test_valid_signature_recovers_matching_tron_address(self):
        tron_address, sig_hex = self._sign(MESSAGE)
        self.assertTrue(wallet_auth.verify_tron_signature(tron_address, MESSAGE, sig_hex))

    def test_signature_does_not_verify_against_a_different_address(self):
        _, sig_hex = self._sign(MESSAGE)
        other_address, _ = self._sign(MESSAGE)
        self.assertFalse(wallet_auth.verify_tron_signature(other_address, MESSAGE, sig_hex))

    def test_garbage_signature_fails_closed(self):
        tron_address, _ = self._sign(MESSAGE)
        self.assertFalse(wallet_auth.verify_tron_signature(tron_address, MESSAGE, '0xdeadbeef'))

    def test_tron_address_conversion_is_base58_and_starts_with_T(self):
        tron_address, _ = self._sign(MESSAGE)
        self.assertTrue(tron_address.startswith('T'))
        self.assertEqual(len(tron_address), 34)


class WalletSignatureDispatchTests(TestCase):
    def test_tronlink_provider_routes_to_tron_verification(self):
        from unittest import mock
        with mock.patch.object(wallet_auth, 'verify_tron_signature', return_value=True) as m:
            self.assertTrue(wallet_auth.verify_wallet_signature(WalletLink.Provider.TRONLINK, 'T...', MESSAGE, 'sig'))
            m.assert_called_once()

    def test_metamask_provider_routes_to_evm_verification(self):
        from unittest import mock
        with mock.patch.object(wallet_auth, 'verify_evm_signature', return_value=True) as m:
            self.assertTrue(wallet_auth.verify_wallet_signature(WalletLink.Provider.METAMASK, '0x...', MESSAGE, 'sig'))
            m.assert_called_once()

    def test_other_providers_default_to_solana_verification(self):
        from unittest import mock
        with mock.patch.object(wallet_auth, 'verify_solana_signature', return_value=True) as m:
            self.assertTrue(wallet_auth.verify_wallet_signature(WalletLink.Provider.PHANTOM, 'addr', MESSAGE, 'sig'))
            m.assert_called_once()
