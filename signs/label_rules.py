"""Naming rules applied without changing stable sign IDs or artwork."""
import re

def fix_spelling(value):
    def replacement(match):
        return 'Miscellaneous' if match.group()[0].isupper() else 'miscellaneous'
    return re.sub(r'\b(?:miscellanous|miscellaneos|miscelleneous|miscelaneous|miscellaneous)\b', replacement, value, flags=re.I)

def normalize_name(name, category):
    name = fix_spelling(name).strip()
    category = category.lower()
    if not name:
        return name
    if category == 'warning':
        name = re.sub(r'\bahead\b', '', name, flags=re.I)
        name = re.sub(r'\s+', ' ', name).strip().rstrip(' .,:;-')
        return name + ' ahead'
    if category == 'mandatory' and not re.search(r'\bcompulsory\b', name, re.I):
        if re.match(r'^end of\s+', name, re.I):
            return re.sub(r'^end of\s+', 'End of compulsory ', name, flags=re.I)
        return 'Compulsory ' + name[0].lower() + name[1:]
    return name
