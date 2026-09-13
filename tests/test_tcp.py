import socket

from netdiag.tcp import check_tcp


class FakeConnection:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def test_tcp_success(monkeypatch):
    def fake_connection(address, timeout):
        return FakeConnection()

    monkeypatch.setattr(
        socket,
        "create_connection",
        fake_connection
    )

    result = check_tcp("example.com", 443)

    assert result["success"] is True
    assert result["host"] == "example.com"
    assert result["port"] == 443


def test_tcp_failure(monkeypatch):
    def fake_failure(address, timeout):
        raise socket.timeout("Connection timed out")

    monkeypatch.setattr(
        socket,
        "create_connection",
        fake_failure
    )

    result = check_tcp("example.com", 443)

    assert result["success"] is False
    assert result["host"] == "example.com"
    assert result["port"] == 443
    assert "error" in result
