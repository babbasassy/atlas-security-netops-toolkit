from netdiag.logs import analyze_auth_log


def test_auth_log_analysis():
    result = analyze_auth_log("sample-data/auth.log")

    assert result["total_failed"] == 9

    assert result["counts"]["192.168.1.50"] == 7
    assert result["counts"]["192.168.1.75"] == 1
    assert result["counts"]["192.168.1.90"] == 1

    assert "192.168.1.50" in result["suspicious"]

    assert "192.168.1.75" not in result["suspicious"]
