"""Real loopback TLS/HTTP checks with synthetic certificates and responses.

No package installation, network capture, external target, OS trust-store change,
VM or container is needed. Temporary keys are removed when this process exits
normally (including handled test failures); see README for interrupted runs.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import http.client
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import threading

LAB = Path(__file__).resolve().parent
ROOT = LAB.parent.parent
sys.path.insert(0, str(ROOT / 'src'))
from netdiag.https import check_https
from netdiag.tcp import check_tcp

HOST = '127.0.0.1'
NAME = 'atlas-loopback.invalid'
TIMEOUT = 3


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def do_GET(self):
        status = 200 if self.path == '/health' else 404
        body = json.dumps({'service': 'atlas-synthetic-loopback', 'status': status}).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(body)
        self.close_connection = True
        self.server.observations.append({
            'peer': self.client_address[0], 'path': self.path, 'status': status,
            'tls_version': self.connection.version(),
        })

    def log_message(self, *_args):
        pass


class LabServer(HTTPServer):
    # Bind only IPv4 loopback, with an ephemeral port assigned by the OS.
    allow_reuse_address = False

    def __init__(self, context):
        self.tls_context = context
        self.observations = []
        self.handshake_errors = []
        self.probe_resets = 0
        self.handler_errors = []
        super().__init__((HOST, 0), Handler)

    def handle_error(self, _request, _client_address):
        error = sys.exception()
        # TLS inspection closes without sending HTTP; Windows may report a reset.
        if isinstance(error, ConnectionResetError):
            self.probe_resets += 1
        else:
            self.handler_errors.append(type(error).__name__)

    def get_request(self):
        raw, address = super().get_request()
        raw.settimeout(TIMEOUT)
        try:
            return self.tls_context.wrap_socket(raw, server_side=True), address
        except (OSError, ssl.SSLError) as error:
            self.handshake_errors.append({'type': type(error).__name__, 'reason': getattr(error, 'reason', None)})
            raw.close()
            raise


def issue_certificates(openssl, directory):
    def invoke(*args):
        subprocess.run([openssl, *args], cwd=directory, check=True, timeout=30,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    (directory / 'leaf.ext').write_text(
        'basicConstraints=critical,CA:FALSE\n'
        'keyUsage=critical,digitalSignature,keyEncipherment\n'
        'extendedKeyUsage=serverAuth\n'
        f'subjectAltName=DNS:{NAME}\n'
        'subjectKeyIdentifier=hash\nauthorityKeyIdentifier=keyid,issuer\n', encoding='ascii')
    invoke('req', '-x509', '-newkey', 'rsa:2048', '-noenc', '-days', '1',
           '-keyout', 'ca.key', '-out', 'ca.pem', '-subj', '/CN=ATLAS Synthetic Lab CA',
           '-addext', 'basicConstraints=critical,CA:TRUE',
           '-addext', 'keyUsage=critical,keyCertSign,cRLSign')
    invoke('req', '-new', '-newkey', 'rsa:2048', '-noenc', '-keyout', 'server.key',
           '-out', 'server.csr', '-subj', f'/CN={NAME}')
    invoke('x509', '-req', '-in', 'server.csr', '-CA', 'ca.pem', '-CAkey', 'ca.key',
           '-CAcreateserial', '-out', 'server.pem', '-days', '1', '-sha256', '-extfile', 'leaf.ext')
    invoke('verify', '-CAfile', 'ca.pem', '-verify_hostname', NAME, 'server.pem')


def http_request(port, ca, version, path):
    context = ssl.create_default_context(cafile=str(ca))
    context.minimum_version = context.maximum_version = version
    with socket.create_connection((HOST, port), timeout=TIMEOUT) as raw:
        with context.wrap_socket(raw, server_hostname=NAME) as tls:
            tls.sendall(f'GET {path} HTTP/1.1\r\nHost: {NAME}\r\nConnection: close\r\n\r\n'.encode('ascii'))
            response = http.client.HTTPResponse(tls)
            response.begin()
            payload = response.read(4096)
            return {'status': response.status, 'body': json.loads(payload), 'tls_version': tls.version()}


def run(openssl):
    report = {
        'started_at_utc': utc_now(), 'scope': 'actual TCP/TLS/HTTP on IPv4 loopback; synthetic CA, service and responses',
        'python_version': platform.python_version(), 'os': platform.system(),
        'python_openssl': ssl.OPENSSL_VERSION, 'checks': [], 'endpoints': [],
        'limitations': ['No packet capture or Wireshark analysis', 'No DNS server, VLAN, routing, firewall or pfSense validation',
                        'No production service or enterprise PKI', 'No remote endpoints or cloud resources'],
        'source_sha256': {p.relative_to(ROOT).as_posix(): sha256(p) for p in
                          [Path(__file__).resolve(), ROOT / 'src/netdiag/https.py', ROOT / 'src/netdiag/tcp.py']},
    }

    def check(name, passed, detail=None):
        report['checks'].append({'name': name, 'passed': bool(passed), 'detail': detail})

    reports = LAB / 'reports'
    reports.mkdir(exist_ok=True)
    servers = []
    temporary_path = None
    try:
        if os.environ.get('SSLKEYLOGFILE'):
            raise RuntimeError('Refusing to run while SSLKEYLOGFILE is set; session keys must not be written outside the temporary lab')
        if not ssl.HAS_TLSv1_3:
            raise RuntimeError('TLS 1.3 support is required')
        report['openssl_cli'] = subprocess.check_output([openssl, 'version'], text=True, timeout=10).strip()
        with tempfile.TemporaryDirectory(prefix='atlas-tls-', dir=reports) as temp:
            temporary_path = Path(temp).resolve()
            if not temporary_path.is_relative_to(reports.resolve()) or temporary_path == reports.resolve():
                raise RuntimeError('Temporary path is outside the owned reports directory')
            try:
                issue_certificates(openssl, temporary_path)
                ca = temporary_path / 'ca.pem'
                check('openssl_verifies_issued_leaf_and_hostname', True)
                report['certificate_sha256'] = {'ca_pem': sha256(ca), 'server_pem': sha256(temporary_path / 'server.pem')}
                for version in (ssl.TLSVersion.TLSv1_2, ssl.TLSVersion.TLSv1_3):
                    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                    context.minimum_version = context.maximum_version = version
                    context.load_cert_chain(str(temporary_path / 'server.pem'), str(temporary_path / 'server.key'))
                    server = LabServer(context)
                    thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': 0.05},
                                              name=f'atlas-{version.name}', daemon=True)
                    servers.append((version.name, server, thread))
                    thread.start()
                    port = server.server_address[1]
                    report['endpoints'].append({'name': version.name, 'address': HOST, 'port': port})
                    check(f'{version.name}_bound_to_loopback', server.socket.getsockname()[0] == HOST)
                    tcp = check_tcp(HOST, port, TIMEOUT)
                    check(f'{version.name}_tcp_reachable', tcp['success'], tcp)
                    unknown_ca = check_https(HOST, port, TIMEOUT, server_hostname=NAME)
                    check(f'{version.name}_untrusted_ca_rejected', not unknown_ca['success'] and
                          unknown_ca.get('error_type') == 'SSLCertVerificationError', unknown_ca)
                    trusted = check_https(HOST, port, TIMEOUT, cafile=str(ca), server_hostname=NAME)
                    check(f'{version.name}_trusted_name_succeeds', trusted['success'], trusted)
                    expected = 'TLSv1.2' if version == ssl.TLSVersion.TLSv1_2 else 'TLSv1.3'
                    check(f'{version.name}_negotiated_expected_protocol', trusted.get('tls_version') == expected)
                    check(f'{version.name}_certificate_san_present',
                          ('DNS', NAME) in trusted.get('certificate', {}).get('subjectAltName', ()))
                    wrong_name = check_https(HOST, port, TIMEOUT, cafile=str(ca), server_hostname='wrong.invalid')
                    check(f'{version.name}_wrong_name_rejected', not wrong_name['success'] and
                          wrong_name.get('error_type') == 'SSLCertVerificationError', wrong_name)
                    good = http_request(port, ca, version, '/health')
                    check(f'{version.name}_health_200', good['status'] == 200 and good['body'] ==
                          {'service': 'atlas-synthetic-loopback', 'status': 200}, good)
                    missing = http_request(port, ca, version, '/missing')
                    check(f'{version.name}_missing_404', missing['status'] == 404 and missing['body']['status'] == 404, missing)
                    if version == ssl.TLSVersion.TLSv1_3:
                        try:
                            http_request(port, ca, ssl.TLSVersion.TLSv1_2, '/health')
                            check('tls12_client_rejected_by_tls13_only_server', False)
                        except ssl.SSLError as error:
                            check('tls12_client_rejected_by_tls13_only_server',
                                  error.reason == 'TLSV1_ALERT_PROTOCOL_VERSION', {'type': type(error).__name__, 'reason': error.reason})
            finally:
                for label, server, thread in servers:
                    if thread.is_alive():
                        server.shutdown()
                    server.server_close()
                    if thread.ident is not None:
                        thread.join(timeout=5)
                    check(f'{label}_server_thread_stopped', not thread.is_alive())
                    try:
                        with socket.create_connection((HOST, server.server_address[1]), timeout=TIMEOUT):
                            closed = {'refused': False}
                    except OSError as error:
                        closed = {'refused': isinstance(error, ConnectionRefusedError), 'error_type': type(error).__name__}
                    check(f'{label}_listener_closed', server.socket.fileno() == -1 and closed['refused'], closed)
                    check(f'{label}_server_observed_expected_requests',
                          [(x['path'], x['status'], x['peer']) for x in server.observations] ==
                          [('/health', 200, HOST), ('/missing', 404, HOST)], server.observations)
                    report.setdefault('server_handshake_errors', {})[label] = server.handshake_errors
                    report.setdefault('tls_probe_connection_resets', {})[label] = server.probe_resets
                    check(f'{label}_no_unexpected_handler_errors', not server.handler_errors, server.handler_errors)
    except Exception as error:
        check('run_completed_without_unhandled_error', False,
              {'type': type(error).__name__, 'message': str(error)})
    finally:
        if temporary_path is not None:
            check('temporary_keys_and_certificates_removed', not temporary_path.exists())
        report['finished_at_utc'] = utc_now()
        report['passed'] = sum(item['passed'] for item in report['checks'])
        report['failed'] = sum(not item['passed'] for item in report['checks'])
        report['success'] = bool(report['checks']) and report['failed'] == 0
        output = reports / ('run-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json')
        output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'success': report['success'], 'passed': report['passed'], 'failed': report['failed'],
                          'report': str(output)}))
    return 0 if report['success'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--openssl', default=shutil.which('openssl'), help='Existing OpenSSL 3 executable path')
    args = parser.parse_args()
    if not args.openssl:
        parser.error('OpenSSL is not on PATH. Supply --openssl with an existing executable path.')
    sys.exit(run(args.openssl))
