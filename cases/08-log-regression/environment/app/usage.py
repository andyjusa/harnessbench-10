import re

def total_tokens(lines):
    return sum(int(m.group(1)) for line in lines if (m := re.search(r"usage tokens=(\d+)", line)))
