import re
from collections import Counter

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())

def word_count(text: str) -> int:
    tokens = re.findall(r"\b\w+'\w+|\b\w+\b", normalize(text))
    return len(tokens)

def char_count(text: str) -> int:
    return len(re.sub(r"\s+", "", text))

def is_palindrome(text: str) -> bool:
    s = re.sub(r"[^a-z0-9]", "", text.lower())
    return s == s[::-1]

def most_common_word(text: str):
    tokens = re.findall(r"\b\w+'\w+|\b\w+\b", normalize(text))
    return Counter(tokens).most_common(1)[0][0] if tokens else None
