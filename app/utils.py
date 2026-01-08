from datetime import datetime, timedelta

def to_utc_minus_5(utc_dt):
    return utc_dt - timedelta(hours=5)
