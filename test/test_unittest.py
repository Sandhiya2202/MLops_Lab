import unittest
from src.text_utils import normalize, word_count, char_count, is_palindrome, most_common_word

class TestTextUtils(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalize("A \n B  C"), "a b c")
    def test_word_count(self):
        self.assertEqual(word_count("hi there"), 2)
    def test_char_count(self):
        self.assertEqual(char_count(" a \n a "), 2)
    def test_is_palindrome(self):
        self.assertTrue(is_palindrome("Able was I ere I saw Elba"))
        self.assertFalse(is_palindrome("python"))
    def test_most_common_word(self):
        self.assertEqual(most_common_word("go go stop"), "go")

if __name__ == "__main__":
    unittest.main()
