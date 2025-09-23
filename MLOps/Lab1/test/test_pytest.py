from src.text_utils import (
    normalize,
    word_count,
    char_count,
    is_palindrome,
    most_common_word,
)


def test_normalize():
    assert normalize("  Hello \n World  ") == "hello world"


def test_word_count():
    assert word_count("one  two three") == 3


def test_char_count():
    assert char_count("a b\nc") == 3


def test_is_palindrome():
    assert is_palindrome("Never odd or even")
    assert not is_palindrome("hello")


def test_most_common_word():
    txt = "Red fish, blue fish. Red RED!"
    assert most_common_word(txt) == "red"
