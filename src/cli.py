import argparse
from src.text_utils import (
    normalize,
    word_count,
    char_count,
    is_palindrome,
    most_common_word,
)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("text", help="input text")
    args = p.parse_args()
    t = args.text
    print("normalize:", normalize(t))
    print("words:", word_count(t))
    print("chars:", char_count(t))
    print("palindrome:", is_palindrome(t))
    print("most_common_word:", most_common_word(t))


if __name__ == "__main__":
    main()
