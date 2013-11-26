from unittest import TestCase
from ORZ import OrzField, OrzPrimaryField
from ORZ.klass_init import _initialize_primary_field

class TestClassInit(TestCase):
    def setUp(self):
        class ORZFieldTest(object):
            foo = OrzField()
            bar = OrzField()
        self.klass = ORZFieldTest

    def test_as_order_key(self):
        NAME = 'hello'
        assertions = {
            OrzPrimaryField.OrderType.DESC: ("-%s" % NAME, ),
            OrzPrimaryField.OrderType.ASC: ("%s" % NAME, ),
            OrzPrimaryField.OrderType.AD: ("-%s" % NAME, ),
        }

        for order_t, asst in assertions.iteritems():
            foo = OrzPrimaryField(order_t)
            foo.name = NAME
            self.assertEqual(foo.as_default_order_key(), asst)

    def test_basic_primary_field(self):
        field = _initialize_primary_field(self.klass)
        self.assertTrue(hasattr(self.klass, 'id'))
        self.assertEqual(field.name, 'id')
        self.assertTrue(isinstance(self.klass.id, OrzPrimaryField))

    def test_customized_primary_field(self):
        class ORZFieldTest(object):
            foo_bar = OrzPrimaryField()
            foo = OrzField()
            bar = OrzField()

        field = _initialize_primary_field(ORZFieldTest)
        self.assertTrue(hasattr(ORZFieldTest, 'foo_bar'))
        self.assertEqual(field.name, 'foo_bar')
        self.assertTrue(isinstance(ORZFieldTest.foo_bar, OrzPrimaryField))
