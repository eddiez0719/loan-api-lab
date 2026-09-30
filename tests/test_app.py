from app import app, monthly_repayment


def client():
    return app.test_client()


def test_health():
    r = client().get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_monthly_repayment_standard_rate():
    assert monthly_repayment(200000, 6.0, 30) == 1199.1


def test_quote_small_loan():
    r = client().get("/api/quote?amount=300000&rate=6.5&years=30")
    assert r.status_code == 200
    assert r.get_json()["monthly_repayment"] == 1896.2


def test_quote_missing_params():
    assert client().get("/api/quote?amount=300000").status_code == 400


def test_quote_promo_returns_a_quote():
    r = client().get("/api/quote?amount=500000&rate=6.5&years=30")
    assert r.status_code == 200
    assert r.get_json()["monthly_repayment"] > 0
