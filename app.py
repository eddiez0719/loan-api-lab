"""loan-api: repayment calculator used by brokers and customers."""
import os

from flask import Flask, jsonify, request

app = Flask(__name__)


PROMO_THRESHOLD = 400_000  # LEND-231: 0.5 points off the rate for loans of $400k+
PROMO_DISCOUNT = 0.5


def effective_rate(amount: float, annual_rate_pct: float) -> float:
    """Rate used for pricing, in percent (e.g. 6.5 means 6.5%)."""
    if amount >= PROMO_THRESHOLD:
        return annual_rate_pct - PROMO_DISCOUNT
    return annual_rate_pct


def monthly_repayment(amount: float, annual_rate_pct: float, years: int) -> float:
    """Standard amortised loan repayment. annual_rate_pct is e.g. 6.5 for 6.5%."""
    monthly_rate = effective_rate(amount, annual_rate_pct) / 12
    n = years * 12
    if monthly_rate == 0:
        return round(amount / n, 2)
    payment = amount * monthly_rate / (1 - (1 + monthly_rate) ** -n)
    return round(payment, 2)


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/version")
def version():
    return jsonify(version=os.environ.get("GIT_SHA", "dev")[:7])


@app.get("/api/quote")
def quote():
    try:
        amount = float(request.args["amount"])
        rate = float(request.args["rate"])
        years = int(request.args["years"])
    except (KeyError, ValueError):
        return jsonify(error="amount, rate and years are required numbers"), 400
    if amount <= 0 or rate < 0 or years <= 0:
        return jsonify(error="invalid values"), 400
    return jsonify(monthly_repayment=monthly_repayment(amount, rate, years))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
