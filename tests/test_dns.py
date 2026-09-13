import socket

from netdiag.dns import resolve_domain


def test_dns_success(monkeypatch):
    def fake_lookup(domain):
        return (
            domain,
            [],
            ["203.0.113.10"]
        )

    monkeypatch.setattr(
        socket,
        "gethostbyname_ex",
        fake_lookup
    )

    result = resolve_domain("example.com")

    assert result["success"] is True
    assert result["hostname"] == "example.com"
    assert result["addresses"] == ["203.0.113.10"]


def test_dns_failure(monkeypatch):
    def fake_failure(domain):
        raise socket.gaierror("DNS lookup failed")

    monkeypatch.setattr(
        socket,
        "gethostbyname_ex",
        fake_failure
    )

    result = resolve_domain("invalid.example")

    assert result["success"] is False
    assert "error" in result
