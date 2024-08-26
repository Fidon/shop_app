import pytz
from datetime import datetime


def EA_TIMEZONE():
    return pytz.timezone('Etc/GMT-3')


# Helper function to parse dates
def parse_datetime(date_str, format_str, to_date=False, to_utc=False):
    try:
        if date_str is not None:
            dt = datetime.strptime(date_str, format_str)
            if to_utc:
                dt = dt.replace(tzinfo=pytz.UTC)
            if to_date:
                dt = dt.date()
            return dt
    except ValueError:
        return None