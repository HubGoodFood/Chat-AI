import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from product_manager import ProductManager

class TestChineseNumberConversion(unittest.TestCase):
    def setUp(self):
        self.pm = ProductManager()

    def test_single_digits(self):
        self.assertEqual(self.pm.convert_chinese_number_to_int('五'), 5)
        self.assertEqual(self.pm.convert_chinese_number_to_int('十'), 10)

    def test_complex_numbers(self):
        self.assertEqual(self.pm.convert_chinese_number_to_int('十一'), 11)
        self.assertEqual(self.pm.convert_chinese_number_to_int('二十'), 20)
        self.assertEqual(self.pm.convert_chinese_number_to_int('二十五'), 25)

    def test_unknown(self):
        self.assertEqual(self.pm.convert_chinese_number_to_int('百'), 1)

if __name__ == '__main__':
    unittest.main()
