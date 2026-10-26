import socket
import ssl


def check_https(host, port=443, timeout=5, *, cafile=None, server_hostname=None):
    """Inspect TLS with certificate and hostname verification always enabled.

    ``host`` is the connection destination. ``server_hostname`` optionally
    supplies the certificate name/SNI when connecting to a known IP address.
    ``cafile`` supplies an explicit trust bundle for a private lab or CA.
    These options are Python API parameters; the CLI retains its defaults.
    """
    try:
        context = ssl.create_default_context(cafile=cafile)
        with socket.create_connection(
            (host, port),
            timeout=timeout
        ) as tcp_socket:

            with context.wrap_socket(
                tcp_socket,
                server_hostname=host if server_hostname is None else server_hostname
            ) as tls_socket:

                certificate = tls_socket.getpeercert()
                cipher = tls_socket.cipher()

                return {
                    "success": True,
                    "host": host,
                    "port": port,
                    "tls_version": tls_socket.version(),
                    "cipher": cipher[0] if cipher else "Unknown",
                    "certificate": certificate,
                }

    except (socket.timeout, socket.gaierror, OSError, ssl.SSLError) as error:
        return {
            "success": False,
            "host": host,
            "port": port,
            "error": str(error),
            "error_type": type(error).__name__,
        }
