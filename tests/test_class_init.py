from unittest import TestCase
from ORZ import OrzField, OrzPrimaryField
from ORZ.klass_init import _initialize_primary_field

class TestClassInit(TestCase):
    def setUp(self):
        class ORZFieldTest(object):
            foo = OrzField()
            bar = OrzField()
        self.klass = ORZFieldTest

    def test_basic_primary_field(self):
        field_name, field = _initialize_primary_field(self.klass)
        self.assertTrue(hasattr(self.klass, 'id'))
        self.assertEqual(field_name, 'id')
        self.assertTrue(isinstance(self.klass.id, OrzPrimaryField))

    def test_customized_primary_field(self):
        class ORZFieldTest(object):
            foo_bar = OrzPrimaryField()
            foo = OrzField()
            bar = OrzField()

        field_name, field = _initialize_primary_field(ORZFieldTest)
        self.assertTrue(hasattr(ORZFieldTest, 'foo_bar'))
        self.assertEqual(field_name, 'foo_bar')
        self.assertTrue(isinstance(ORZFieldTest.foo_bar, OrzPrimaryField))
