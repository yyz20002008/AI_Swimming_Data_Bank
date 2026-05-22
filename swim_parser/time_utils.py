from __future__ import annotations

"""
Time conversion utilities and event name normalization for swimming data.
"""
import re
from typing import Optional


# Stroke codes used in CL2/HY3 files
STROKE_MAP = {
    "1": "Freestyle",   "A": "Freestyle",   "FR": "Freestyle",
    "2": "Backstroke",  "B": "Backstroke",  "BK": "Backstroke",
    "3": "Breaststroke","C": "Breaststroke","BR": "Breaststroke",
    "4": "Butterfly",   "D": "Butterfly",   "FL": "Butterfly",
    "5": "IM",          "E": "IM",          "IM": "IM",
    "6": "Medley Relay","F": "Medley Relay",
    "7": "Free Relay",  "G": "Free Relay",
}

STROKE_ABBREVIATIONS = {
    "Freestyle": "FR",
    "Backstroke": "BK",
    "Breaststroke": "BR",
    "Butterfly": "FL",
    "IM": "IM",
    "Medley Relay": "MR",
    "Free Relay": "FRR",
}

COURSE_MAP = {
    "Y": "SCY",  "S": "SCY",  "1": "SCY",
    "L": "LCM",  "2": "LCM",
    "M": "SCM",  "3": "SCM",
}


def parse_time_string(time_str: str) -> Optional[float]:
    """
    Convert a swimming time string to total seconds as float.
    
    Handles formats:
        "32.63"     -> 32.63
        "1:22.36"   -> 82.36
        "1:22.36Y"  -> 82.36  (strips course suffix)
        "10:22.36"  -> 622.36
        "NT"        -> None
        "NS"        -> None
        "DQ"        -> None
        "SCR"       -> None
        ""          -> None
    """
    if not time_str:
        return None
    
    # Strip whitespace and course suffix (Y/L/S)
    time_str = time_str.strip().rstrip("YLSyls")
    
    # Handle special values
    if not time_str or time_str.upper() in ("NT", "NS", "DQ", "SCR", "DFS", "DNF", "DNQ"):
        return None
    
    try:
        # Check for MM:SS.ss or H:MM:SS.ss format
        if ":" in time_str:
            parts = time_str.split(":")
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60.0 + seconds
            elif len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = float(parts[2])
                return hours * 3600.0 + minutes * 60.0 + seconds
        else:
            return float(time_str)
    except (ValueError, IndexError):
        return None


def format_time(seconds: Optional[float]) -> str:
    """Convert seconds to display time string (e.g., 82.36 -> '1:22.36')."""
    if seconds is None:
        return "NT"
    if seconds < 0:
        return "NT"
    
    minutes = int(seconds // 60)
    remaining = seconds - minutes * 60
    
    if minutes > 0:
        return f"{minutes}:{remaining:05.2f}"
    else:
        return f"{remaining:.2f}"


def parse_hy3_time(raw: str) -> Optional[float]:
    """
    Parse time from HY3 format.
    HY3 stores times as right-justified strings like:
        "   42.70Y" -> 42.70
        "  118.46Y" -> 78.46 (but actually stored as raw seconds * 100?)
    
    Actually looking at the data more carefully:
        "   42.70Y" means 42.70 seconds
        "  118.46Y" means 1:18.46 -> but stored as 118.46 as a number
    
    So we need to convert: if >= 100, it means M:SS.ss encoded as MMMSS.ss
    """
    if not raw:
        return None
    raw = raw.strip().rstrip("YLSyls ")
    if not raw or raw.upper() in ("NT", "NS", "DQ", "SCR"):
        return None
    
    try:
        val = float(raw)
        if val <= 0:
            return None
        # HY3 stores times as total hundredths-format: MMMSS.ss
        # So 118.46 means 1 minute 18.46 seconds = 78.46
        # And 42.70 means 42.70 seconds
        # Actually: looking at the data, 118.46Y maps to 1:18.46 in results
        # The format is: minutes * 100 + seconds
        if val >= 6000:  # 60+ minutes, likely hours encoding
            hours = int(val // 10000)
            remainder = val - hours * 10000
            minutes = int(remainder // 100)
            seconds = remainder - minutes * 100
            return hours * 3600 + minutes * 60 + seconds
        elif val >= 100:
            minutes = int(val // 100)
            seconds = val - minutes * 100
            return minutes * 60 + seconds
        else:
            return val
    except ValueError:
        return None


def normalize_event_name(distance: int, stroke_code: str, relay: bool = False) -> tuple:
    """
    Normalize event to standard name and code.
    Returns (event_name, event_code, stroke_name)
    """
    stroke = STROKE_MAP.get(stroke_code, stroke_code)
    abbr = STROKE_ABBREVIATIONS.get(stroke, stroke_code)
    
    if relay:
        event_name = f"{distance} {stroke}"
        event_code = f"{distance}{abbr}"
    else:
        event_name = f"{distance} {stroke}"
        event_code = f"{distance}{abbr}"
    
    return event_name, event_code, stroke


def parse_course(code: str) -> str:
    """Convert course code to standard format."""
    return COURSE_MAP.get(code.strip().upper(), "SCY")
