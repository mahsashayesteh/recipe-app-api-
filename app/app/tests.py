"""
simple tests

"""

from django.test import SimpleTestCase

from app.calc import add

class CalcTest(SimpleTestCase):
    """ test test calc module. """

    def test_add_numbers(self):
        res = add(5,7)
        self.assertEqual(res, 12)

