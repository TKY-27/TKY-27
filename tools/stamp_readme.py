"""Keep the footer's byte count true: rewrite the marked numbers in README.md from the built hero."""

import math
import os
import re
import sys

QR_BYTES = 2953  # byte-mode capacity of a Version 40-L code, the size QRnel fits in


def stamp(readme, hero):
    size = os.path.getsize(hero)
    values = {"hero-bytes": f"{size:,}", "hero-qrs": str(math.ceil(size / QR_BYTES))}
    with open(readme) as f:
        text = f.read()
    for key, value in values.items():
        text, count = re.subn(rf"(<!--{key}-->).*?(<!--/{key}-->)", rf"\g<1>{value}\g<2>", text)
        if count != 1:
            raise ValueError(f"README.md should contain the {key} marker exactly once, found {count}")
    with open(readme, "w") as f:
        f.write(text)


if __name__ == "__main__":
    stamp(sys.argv[1], sys.argv[2])
