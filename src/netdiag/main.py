import argparse
import json

from netdiag.dns import resolve_domain
from netdiag.tcp import check_tcp
from netdiag.https import check_https
from netdiag.logs import analyze_auth_log


def print_json(data):
    print(json.dumps(data, indent=2, default=str))


def main():
    parser = argparse.ArgumentParser(
        description="ATLAS Security NetOps Toolkit"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Return output as JSON"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True
    )

    dns_parser = subparsers.add_parser(
        "dns",
        help="Resolve a domain name"
    )
    dns_parser.add_argument("domain")

    tcp_parser = subparsers.add_parser(
        "tcp",
        help="Test TCP connectivity"
    )
    tcp_parser.add_argument("host")
    tcp_parser.add_argument("port", type=int)

    https_parser = subparsers.add_parser(
        "https",
        help="Inspect HTTPS/TLS"
    )
    https_parser.add_argument("host")

    logs_parser = subparsers.add_parser(
        "logs",
        help="Analyze authentication logs"
    )
    logs_parser.add_argument("file")

    args = parser.parse_args()

    if args.command == "dns":
        result = resolve_domain(args.domain)

        if args.json:
            print_json(result)
            return

        if result["success"]:
            print(f"Domain: {args.domain}")
            print(f"Hostname: {result['hostname']}")
            print("IP addresses:")

            for address in result["addresses"]:
                print(f"  - {address}")
        else:
            print(f"DNS lookup failed: {result['error']}")

    elif args.command == "tcp":
        result = check_tcp(args.host, args.port)

        if args.json:
            print_json(result)
            return

        print(f"Host: {args.host}")
        print(f"Port: {args.port}")

        if result["success"]:
            print("Status: reachable")
        else:
            print("Status: unreachable")
            print(f"Reason: {result['error']}")

    elif args.command == "https":
        result = check_https(args.host)

        if args.json:
            print_json(result)
            return

        print(f"Host: {args.host}")
        print("Port: 443")

        if result["success"]:
            print("HTTPS/TLS: reachable")
            print(f"TLS version: {result['tls_version']}")
            print(f"Cipher: {result['cipher']}")

            certificate = result["certificate"]

            print(f"Certificate subject: {certificate.get('subject', [])}")
            print(f"Certificate issuer: {certificate.get('issuer', [])}")
            print(f"Certificate expires: {certificate.get('notAfter', 'Unknown')}")
        else:
            print("HTTPS/TLS: failed")
            print(f"Reason: {result['error']}")

    elif args.command == "logs":
        result = analyze_auth_log(args.file)

        if args.json:
            print_json({
                "total_failed": result["total_failed"],
                "counts": dict(result["counts"]),
                "suspicious": result["suspicious"],
            })
            return

        print(f"Failed SSH attempts: {result['total_failed']}")

        print("\nSource IPs:")
        for ip, count in result["counts"].most_common():
            print(f"  {ip}: {count}")

        print("\nPotential brute-force sources:")

        if result["suspicious"]:
            for ip, count in result["suspicious"].items():
                print(f"  {ip}: {count} failed attempts")
        else:
            print("  None detected")


if __name__ == "__main__":
    main()
