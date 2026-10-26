import socket
import ssl
import unittest
from unittest.mock import MagicMock, patch

from netdiag.https import check_https


class HttpsTests(unittest.TestCase):
    def test_default_context_requires_certificate_and_hostname(self):
        contexts = []
        real_create = ssl.create_default_context

        def capture(**kwargs):
            context = real_create(**kwargs)
            contexts.append(context)
            return context

        with patch('netdiag.https.ssl.create_default_context', side_effect=capture):
            with patch('netdiag.https.socket.create_connection', side_effect=socket.timeout):
                result = check_https('example.invalid')
        self.assertFalse(result['success'])
        self.assertEqual(contexts[0].verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(contexts[0].check_hostname)

    def test_default_name_and_timeout_remain_unchanged(self):
        context = MagicMock()
        tls = context.wrap_socket.return_value.__enter__.return_value
        tls.version.return_value = 'TLSv1.3'
        tls.cipher.return_value = ('TLS_AES_256_GCM_SHA384', 'TLSv1.3', 256)
        tls.getpeercert.return_value = {'subject': 'mock certificate'}
        with patch('netdiag.https.ssl.create_default_context', return_value=context) as create:
            with patch('netdiag.https.socket.create_connection') as connect:
                result = check_https('example.invalid', 8443, 2)
        create.assert_called_once_with(cafile=None)
        connect.assert_called_once_with(('example.invalid', 8443), timeout=2)
        self.assertEqual(context.wrap_socket.call_args.kwargs['server_hostname'], 'example.invalid')
        self.assertTrue(result['success'])
        self.assertEqual(result['tls_version'], 'TLSv1.3')
        self.assertEqual(result['cipher'], 'TLS_AES_256_GCM_SHA384')

    def test_custom_trust_and_name_do_not_change_destination(self):
        context = MagicMock()
        with patch('netdiag.https.ssl.create_default_context', return_value=context) as create:
            with patch('netdiag.https.socket.create_connection') as connect:
                check_https('127.0.0.1', 8443, cafile='lab-ca.pem', server_hostname='atlas-loopback.invalid')
        create.assert_called_once_with(cafile='lab-ca.pem')
        connect.assert_called_once_with(('127.0.0.1', 8443), timeout=5)
        self.assertEqual(context.wrap_socket.call_args.kwargs['server_hostname'], 'atlas-loopback.invalid')

    def test_invalid_trust_file_fails_before_connection(self):
        with patch('netdiag.https.ssl.create_default_context', side_effect=FileNotFoundError('missing CA')):
            with patch('netdiag.https.socket.create_connection') as connect:
                result = check_https('127.0.0.1', cafile='missing.pem')
        connect.assert_not_called()
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'FileNotFoundError')

    def test_certificate_failure_is_not_swallowed_as_success(self):
        context = MagicMock()
        context.wrap_socket.side_effect = ssl.SSLCertVerificationError('untrusted certificate')
        with patch('netdiag.https.ssl.create_default_context', return_value=context):
            with patch('netdiag.https.socket.create_connection'):
                result = check_https('127.0.0.1')
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'SSLCertVerificationError')

    def test_network_failure_is_reported(self):
        with patch('netdiag.https.socket.create_connection', side_effect=ConnectionRefusedError('closed')):
            result = check_https('127.0.0.1')
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'ConnectionRefusedError')


if __name__ == '__main__':
    unittest.main()
