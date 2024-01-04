import unittest

from mqtt.utils import normalize_name_to_id


class TestUnitNormalizeNameToId(unittest.TestCase):

    def test_unit_returns_same_value_if_already_normalized(self):
        self.assertEqual('normalized_value',
                         normalize_name_to_id('normalized_value'))

    def test_unit_returns_lowercase(self):
        self.assertEqual('normalized_value',
                         normalize_name_to_id('NoRmAlIzEd VaLuE'))

    def test_unit_returns_value_with_special_chars_replaced(self):
        self.assertEqual('n0r_v_aliz3d',
                         normalize_name_to_id('n0r|v!aliz3d'))

    def test_unit_returns_value_with_special_chars_unicode_1_replaced(self):
        self.assertEqual('kozuscek',
                         normalize_name_to_id('køžuščêk'))

    def test_unit_returns_value_with_special_chars_unicode_2_replaced(self):
        self.assertEqual('__',
                         normalize_name_to_id('北亰'))


if __name__ == '__main__':
    unittest.main()
