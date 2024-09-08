import pytz
from datetime import datetime
from functools import wraps
from django.core.exceptions import PermissionDenied


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
    

# Filter items based on table columns
def filter_items(column_field, column_search, item, num_columns=None):
    column_value = str(item.get(column_field, '')).lower()
    if num_columns is not None and column_field in num_columns:
        try:
            item_value = float(column_value) if column_value else 0.0
            if column_search.startswith('-') and column_search[1:].isdigit():
                max_value = int(column_search[1:])
                return item_value <= max_value
            elif column_search.endswith('-') and column_search[:-1].isdigit():
                min_value = int(column_search[:-1])
                return item_value >= min_value
            elif column_search.replace(',', '').isdigit():
                target_value = float(column_search.replace(',', ''))
                return item_value == target_value
        except ValueError:
            return False
    return column_search.lower() in column_value


def admin_required():
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            if user.is_authenticated and user.is_admin:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapped_view
    return decorator