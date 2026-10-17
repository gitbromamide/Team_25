import re
MONTHS = ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]

def snapshot_from_name(name):
    """'standard_jan24frl_xml.zip' -> '2024-01'. Returns None if no month+year found."""
    m = re.search(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[_-]?(\d{4}|\d{2})", name.lower())
    if not m:
        return None
    mon = MONTHS.index(m.group(1)) + 1
    yr = int(m.group(2))
    if yr < 100:
        yr += 2000
    return f"{yr}-{mon:02d}"

FORMATS = ["standard", "rapid", "blitz"]

def format_from_name(name):
    """'rapid_jan20frl_xml.zip' -> 'rapid'. Defaults to 'standard'."""
    n = name.lower()
    for f in FORMATS:
        if n.startswith(f):
            return f
    return "standard"
