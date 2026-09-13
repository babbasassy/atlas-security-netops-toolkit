import re
from collections import Counter


FAILED_LOGIN_PATTERN = re.compile(
    r"Failed password.*from\s+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)"
)


def analyze_auth_log(file_path, threshold=5):
    failed_ips = []

    with open(file_path, "r", encoding="utf-8") as log_file:
        for line in log_file:
            match = FAILED_LOGIN_PATTERN.search(line)

            if match:
                failed_ips.append(match.group(1))

    counts = Counter(failed_ips)

    suspicious = {
        ip: count
        for ip, count in counts.items()
        if count >= threshold
    }

    return {
        "total_failed": len(failed_ips),
        "counts": counts,
        "suspicious": suspicious,
    }
