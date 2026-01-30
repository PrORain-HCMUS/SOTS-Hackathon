"""
Time and date utilities for AgriPulse.
"""

from datetime import datetime, timedelta, timezone
from typing import Tuple, List, Optional

from dateutil.relativedelta import relativedelta


def get_utc_now() -> datetime:
    """Get current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)


def parse_iso_datetime(dt_str: str) -> datetime:
    """Parse ISO format datetime string to datetime object."""
    if dt_str.endswith("Z"):
        dt_str = dt_str[:-1] + "+00:00"
    return datetime.fromisoformat(dt_str)


def to_iso_string(dt: datetime) -> str:
    """Convert datetime to ISO format string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def get_month_range(year: int, month: int) -> Tuple[datetime, datetime]:
    """
    Get start and end datetime for a given month.
    
    Returns:
        Tuple of (start_of_month, end_of_month) with UTC timezone
    """
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc) - timedelta(microseconds=1)
    else:
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc) - timedelta(microseconds=1)
    return start, end


def get_week_range(date: datetime) -> Tuple[datetime, datetime]:
    """
    Get start and end datetime for the week containing the given date.
    Week starts on Monday.
    
    Returns:
        Tuple of (start_of_week, end_of_week) with UTC timezone
    """
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    
    # Get Monday of the week
    days_since_monday = date.weekday()
    start = date - timedelta(days=days_since_monday)
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get Sunday end
    end = start + timedelta(days=7) - timedelta(microseconds=1)
    
    return start, end


def get_monthly_periods(
    end_year: int,
    end_month: int,
    window_len: int = 6,
) -> List[Tuple[datetime, datetime]]:
    """
    Get list of monthly periods going backwards from end_year/end_month.
    
    Args:
        end_year: End year
        end_month: End month (1-12)
        window_len: Number of months
        
    Returns:
        List of (period_start, period_end) tuples, oldest first
    """
    periods = []
    
    for i in range(window_len - 1, -1, -1):
        # Calculate year/month going backwards
        target_date = datetime(end_year, end_month, 1) - relativedelta(months=i)
        start, end = get_month_range(target_date.year, target_date.month)
        periods.append((start, end))
    
    return periods


def format_period_key(period_start: datetime, period_end: datetime) -> str:
    """
    Format a period as a string key for use in file names.
    
    Returns:
        String like "2024-01-01_2024-01-31"
    """
    return f"{period_start.strftime('%Y-%m-%d')}_{period_end.strftime('%Y-%m-%d')}"


def get_sensing_date_str(sensing_time: datetime) -> str:
    """Format sensing time as date string YYYY-MM-DD."""
    return sensing_time.strftime("%Y-%m-%d")


def weeks_between(start: datetime, end: datetime) -> int:
    """Calculate number of weeks between two dates."""
    delta = end - start
    return delta.days // 7


def months_between(start: datetime, end: datetime) -> int:
    """Calculate number of months between two dates."""
    return (end.year - start.year) * 12 + (end.month - start.month)
