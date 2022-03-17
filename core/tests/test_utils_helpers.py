from django.test import TestCase

from core.utils.helpers import bool_to_yes_no


class BoolToYesNo(TestCase):
    def test_true(self):
        self.assertEqual(bool_to_yes_no(True), "yes")

    def test_false(self):
        self.assertEqual(bool_to_yes_no(False), "no")

    def test_not_boolean(self):
        with self.assertRaises(TypeError):
            bool_to_yes_no("")
