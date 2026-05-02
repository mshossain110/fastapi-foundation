from datetime import datetime, timezone, timedelta

def get_default_server_time() -> datetime:
    gmt_minus_4 = timezone(timedelta(hours=-4))
    return datetime.now(gmt_minus_4)

def get_server_time(date: datetime) -> datetime:
    gmt_minus_4 = timezone(timedelta(hours=-4))
    return date.astimezone(gmt_minus_4)