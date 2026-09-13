import socket
import ssl


def check_https(host, port=443, timeout=5):
    context = ssl.create_default_context()

    try:
        with socket.create_connection(
            (host, port),
            timeout=timeout
        ) as tcp_socket:

            with context.wrap_socket(
                tcp_socket,
                server_hostname=host
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
        }
