import pandas as pd

from aulens.lifecycle import liquidity_profile


def test_liquidity_profile_uses_whole_lives_and_trading_days_to_expiry():
    days = pd.bdate_range("2026-01-01", "2026-03-31")
    rows = []
    for exp, listed in [(pd.Timestamp("2026-02-27"), pd.Timestamp("2026-01-15")),     # whole life in the data
                        (pd.Timestamp("2026-03-31"), pd.Timestamp("2026-02-02")),     # whole life in the data
                        (pd.Timestamp("2026-04-30"), pd.Timestamp("2026-01-01"))]:    # listed before data, still live
        life = [d for d in days if listed <= d <= exp]
        for k, d in enumerate(life):
            rows.append({"date": d, "symbol": "GOLDTEN", "expiry": exp, "volume": 10 * k})   # volume builds with age
    prof, summary = liquidity_profile(pd.DataFrame(rows), "GOLDTEN", min_volume=150)
    assert summary["contracts"] == 2
    assert prof["days_to_expiry"].min() == 0 and prof.loc[prof["days_to_expiry"] == 0, "contracts"].item() == 2
    lives = [len([d for d in days if pd.Timestamp("2026-01-15") <= d <= pd.Timestamp("2026-02-27")]),
             len([d for d in days if pd.Timestamp("2026-02-02") <= d <= pd.Timestamp("2026-03-31")])]
    assert summary["listed_days"] == sorted(lives)[0] + (sorted(lives)[1] - sorted(lives)[0]) / 2
    # volume reaches 150 lots once a contract is 15 rows old; the shorter life sets the median
    assert summary["liquid_from"] == prof.loc[prof["volume"] >= 150, "days_to_expiry"].max()
    assert (prof["contracts"] == 2).all()                         # only days both contracts lived through
    assert summary["peak_day"] == 0                               # volume builds until expiry here
