import socket


def resolve_domain(domain):
    try:
        hostname, aliases, addresses = socket.gethostbyname_ex(domain)

        return {
            "success": True,
            "hostname": hostname,
            "addresses": addresses,
        }

    except socket.gaierror as error:
        return {
            "success": False,
            "error": str(error),
        }
