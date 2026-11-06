"""Display-only annotations of the user-provided Kitab al-Iman text.

Never rewrite quotations, footnotes, saved block IDs or source anchors.
Mixed passages are labelled "verse with commentary", never a bare verse.
"""
from copy import deepcopy
import re

VERSE = re.compile(r"^«[\s\S]+»\s*\[\d+:\d+(?:[–-]\d+)?\]\.?$")
VERSE_REF = re.compile(r"\[\d+:\d+(?:[–-]\d+)?\]")
ALLAH_SAID = re.compile(r"(?:всевышний\s+аллах|аллах|всевышний)[^.!?]{0,25}\b(?:сказал|говорит|сказав)\s*:", re.I)
PROPHET_SAID = re.compile(r"(?:пророк|посланник\s+аллаха)[^.!?]{0,105}\b(?:сказал|говорил)\s*:", re.I)
SCHOLAR_SAID = re.compile(r"^(?:муджахид|ибн\s|абу\s|аль[-\s]|шейх\s|суфьян\s|хасан\s|катада\s|ата\s|ад[-\s])[^\n]{0,145}\b(?:сказал|говорил|объяснял|утверждал)\s*:", re.I)


def classify_quote(text):
    value = text.strip()
    if VERSE.fullmatch(value):
        return "verse"
    if len(value) > 790 or "«" not in value or "»" not in value:
        return None
    if ALLAH_SAID.search(value[:155]) and VERSE_REF.search(value):
        return "verse_context"
    if PROPHET_SAID.search(value[:225]) and not VERSE_REF.search(value):
        return "hadith"
    if SCHOLAR_SAID.search(value[:180]) and not VERSE_REF.search(value):
        return "scholar"
    return None


def prepare_display_book(book):
    result = deepcopy(book)
    if len(result["chapters"]) != 131:
        raise ValueError("Unexpected chapter count")
    previous = {b["id"]: b for c in book["chapters"] for b in c["blocks"]}
    if len(previous) != 1795:
        raise ValueError("Unexpected original text block count")
    for chapter in result["chapters"]:
        if chapter["section"].startswith("Страница оригинала:"):
            chapter["section"] = ""
        for block in chapter["blocks"]:
            if block["type"] != "text":
                continue
            style = classify_quote(block["text"])
            if style:
                block["type"] = style
                if style == "verse":
                    refs = VERSE_REF.findall(block["text"])
                    if len(refs) == 1:
                        block["quranReference"] = refs[0][1:-1]
    current = {b["id"]: b for c in result["chapters"] for b in c["blocks"]}
    if previous.keys() != current.keys():
        raise ValueError("Changed source block IDs")
    protected = ("id", "anchor", "text", "sourcePage", "sourcePages",
                 "anchorAliases", "footnoteRefs", "footnoteNumber",
                 "referenceAnchor", "referenceNumber")
    for id_, original in previous.items():
        if any(original.get(field) != current[id_].get(field) for field in protected):
            raise ValueError("Changed book content: " + id_)
    if sum(b["type"] == "footnote" for b in current.values()) != 242:
        raise ValueError("Source footnotes changed")
    if sum(b["type"] == "verse" for b in current.values()) != 3:
        raise ValueError("Three Russian verse blocks not recovered")
    if any(c["section"].startswith("Страница оригинала:") for c in result["chapters"]):
        raise ValueError("PDF page labels still visible")
    return result
