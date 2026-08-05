"""Acquire clean, public-domain corpora as the experimental substrate."""
import urllib.request, os, re, json

SOURCES = {
    "pride_prejudice": "https://raw.githubusercontent.com/GITenberg/Pride-and-Prejudice_1342/master/1342.txt",
    "sherlock":        "https://raw.githubusercontent.com/GITenberg/The-Adventures-of-Sherlock-Holmes_1661/master/1661.txt",
    "tale_two_cities": "https://raw.githubusercontent.com/GITenberg/A-Tale-of-Two-Cities_98/master/98.txt",
    "moby_dick":       "https://raw.githubusercontent.com/GITenberg/Moby-Dick--or-The-Whale_2701/master/2701.txt",
    "great_expect":    "https://raw.githubusercontent.com/GITenberg/Great-Expectations_1400/master/1400.txt",
    "dubliners":       "https://raw.githubusercontent.com/GITenberg/Dubliners_2814/master/2814.txt",
    "kjv_bible":       "https://raw.githubusercontent.com/GITenberg/The-King-James-Version-of-the-Bible_10/master/10.txt",
}
QURAN = "https://raw.githubusercontent.com/risan/quran-json/main/dist/quran.json"

START = ["*** START OF THIS PROJECT GUTENBERG", "*** START OF THE PROJECT GUTENBERG",
         "***START OF THE PROJECT GUTENBERG"]
END = ["*** END OF THIS PROJECT GUTENBERG", "*** END OF THE PROJECT GUTENBERG",
       "***END OF THE PROJECT GUTENBERG"]


def strip_gutenberg(text):
    start = 0
    for m in START:
        i = text.find(m)
        if i != -1:
            j = text.find("\n", i)
            start = j + 1 if j != -1 else i
            break
    end = len(text)
    for m in END:
        i = text.find(m)
        if i != -1:
            end = i
            break
    body = text[start:end]
    m = re.search(r"\n[^\n]*End of[^\n]*Project Gutenberg", body, re.IGNORECASE)
    if m:
        body = body[:m.start()]
    body = re.sub(r"^\s*Produced by[^\n]*\n", "", body, flags=re.IGNORECASE)
    body = re.sub(r"\r\n?", "\n", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    # remove editor notes mentioning Gutenberg in the first 1500 chars
    head, tail = body[:1500], body[1500:]
    head = re.sub(r"[^\n]*Project Gutenberg[^\n]*\n", "", head, flags=re.IGNORECASE)
    return (head + tail).strip()


def main():
    os.makedirs("corpora", exist_ok=True)
    for name, url in SOURCES.items():
        raw = urllib.request.urlopen(url, timeout=40).read().decode("utf-8", "replace")
        txt = strip_gutenberg(raw)
        open(f"corpora/{name}.txt", "w", encoding="utf-8").write(txt)
        print(f"OK {name:18s} {len(txt.split()):>8d} words")
    d = json.loads(urllib.request.urlopen(QURAN, timeout=40).read())
    ar = "\n".join(v["text"] for s in d for v in s["verses"])
    open("corpora/arabic_quran.txt", "w", encoding="utf-8").write(ar)
    print(f"OK {'arabic_quran':18s} {len(ar.split()):>8d} words")
    bad = [f for f in os.listdir("corpora")
           if "PROJECT GUTENBERG" in open(f"corpora/{f}", encoding="utf-8").read().upper()]
    print("boilerplate remaining:", bad if bad else "NONE")


if __name__ == "__main__":
    main()
