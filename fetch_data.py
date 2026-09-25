"""Download the Groenwold et al. (2020) AAE/SAE pairs into data/.

Usage: python3 fetch_data.py

The texts are released for research use and are not redistributed here; this script
fetches them from the ACL Anthology and checks they are the exact files the published
run used. Pair id N is the 0-based line N of both files.
"""
import hashlib
import io
import os
import sys
import urllib.request
import zipfile

URL = "https://aclanthology.org/attachments/2020.emnlp-main.473.OptionalSupplementaryMaterial.zip"
FILES = {
    "aave_samples.txt": "8c7bf485cdc4bd5dfd18eca40af7f6343b917641196c83f212abf43e4c78639a",
    "sae_samples.txt": "5087d21d1655f6c4fdc7a1a4a379f3c67d55153504c45f079425eced92b7a8cc",
}
N_PAIRS = 2019
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def main():
    print(f"Downloading {URL}")
    with urllib.request.urlopen(URL, timeout=60) as r:
        z = zipfile.ZipFile(io.BytesIO(r.read()))
    os.makedirs(OUT, exist_ok=True)
    for name, want in FILES.items():
        raw = z.read(f"EMNLP-AAVE-files/{name}")
        got = hashlib.sha256(raw).hexdigest()
        if got != want:
            sys.exit(f"{name}: sha256 {got} does not match the published run's {want}")
        # The files have no trailing newline, so 2,019 texts split on 2,018 newlines
        lines = raw.decode("utf-8").split("\n")
        if len(lines) != N_PAIRS:
            sys.exit(f"{name}: expected {N_PAIRS} lines, found {len(lines)}")
        with open(os.path.join(OUT, name), "wb") as f:
            f.write(raw)
        print(f"{name}: {len(lines)} lines, sha256 ok")
    print(f"Wrote {OUT}/ (gitignored; do not commit the texts)")


if __name__ == "__main__":
    main()
