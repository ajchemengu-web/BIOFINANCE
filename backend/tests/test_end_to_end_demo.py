"""
Runs the Phase 6 end-to-end demonstration (scripts/demo_end_to_end.py)
against the TestClient fixture, so the exact flow scripts/demo_end_to_end.py
narrates when run against a live server is also checked by the regular
test suite — not just a standalone script nobody re-runs.
"""

from scripts.demo_end_to_end import run_demo


def test_phase_6_end_to_end_demonstration(client, capsys):
    result = run_demo(client)

    assert result["transaction"]["status"] == "COMPLETED"
    assert result["transaction"]["selected_provider"] == "MPESA"

    narrated = capsys.readouterr().out
    assert "BioFinance ID issued" in narrated
    assert "PAYMENT SUCCESSFUL" in narrated
