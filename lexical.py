"""Tag pairs lexically clean: neither side has a slur, profanity or sexual insult token.

Usage: python3 lexical.py          # rewrites clean_ids.txt from data/
       python3 lexical.py --check  # fails if clean_ids.txt differs from what data/ gives

The stems below are the filter itself; it prints counts only, never the texts.
"""
import re
import sys
from collections import Counter

from run import N_PAIRS, load_pairs

# Stems matched at a word start; covers common spellings and plurals in this corpus
STEMS = [
    r"nigg", r"n[i1]gg", r"nigga", r"niqq", r"negro",
    r"fuck", r"fuk", r"fck", r"phuck", r"fcuk", r"mf\b", r"mfs\b",
    r"shit", r"sh[i1]t", r"bitch", r"b[i1]tch", r"biatch", r"bish\b",
    r"hoe\b", r"hoes\b", r"thot", r"slut", r"whore",
    r"puss", r"dick", r"cock", r"cunt", r"twat", r"tits?\b", r"titties",
    r"ass\b", r"asses\b", r"asshole", r"azz\b", r"booty",
    r"damn", r"dammit", r"goddamn", r"hell\b",
    r"fag", r"dyke", r"retard", r"bastard", r"wtf\b", r"stfu\b", r"lmfao",
    r"piss", r"crap\b", r"skank", r"trick\b",
]
# Strong stems also match inside run-together words (the corpus drops many spaces)
ANYWHERE = [r"fuck", r"shit", r"bitch", r"nigg", r"niqq", r"cunt", r"asshole", r"pussy", r"whore", r"slut"]
RX = re.compile(r"(?<![a-z])(" + "|".join(STEMS) + ")|(" + "|".join(ANYWHERE) + ")", re.I)
NWORD = re.compile(r"(?<![a-z])n[i1]gg|(?<![a-z])niqq", re.I)


def dirty(text):
    return bool(RX.search(text))


def clean_ids(aae, sae):
    return [i for i in range(N_PAIRS) if not dirty(aae[i]) and not dirty(sae[i])]


def main():
    aae, sae = load_pairs()
    clean = clean_ids(aae, sae)
    text = "\n".join(map(str, clean))
    if "--check" in sys.argv:
        if open("clean_ids.txt").read() != text:
            sys.exit("clean_ids.txt does not match the filter output")
        print(f"clean_ids.txt matches: {len(clean)} clean pairs")
        return
    print("clean pairs:", len(clean), "excluded:", N_PAIRS - len(clean))
    print("AAE texts flagged:", sum(dirty(t) for t in aae), "SAE texts flagged:", sum(dirty(t) for t in sae))
    print("n-word AAE:", sum(bool(NWORD.search(t)) for t in aae), "SAE:", sum(bool(NWORD.search(t)) for t in sae))
    c = Counter()
    for t in aae + sae:
        for m in RX.finditer(t):
            c[(m.group(1) or m.group(2)).lower()] += 1
    print("distinct stem hits:", len(c))
    open("clean_ids.txt", "w").write(text)


if __name__ == "__main__":
    main()
