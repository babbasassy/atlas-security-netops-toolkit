import socket


def check_tcp(host, port, timeout=3):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return {
                "success": True,
                "host": host,
                "port": port,
            }

    except (socket.timeout, socket.gaierror, OSError) as error:
        return {
            "success": False,
            "host": host,
            "port": port,
            "error": str(error),
        }
