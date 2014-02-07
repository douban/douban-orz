from mock import patch
from unittest import TestCase
from ORZ import OrzField, OrzPrimaryField
from ORZ.klass_init import _initialize_primary_field, _collect_order_combs

class TestField(TestCase):
    def test_as_order_key(self):
        NAME = 'hello'
        assertions = {
            OrzPrimaryField.OrderType.DESC: ("-%s" % NAME, ),
            OrzPrimaryField.OrderType.ASC: ("%s" % NAME, ),
            OrzPrimaryField.OrderType.AD: ("-%s" % NAME, ),
        }

        for order_t, asst in assertions.iteritems():
            foo = OrzPrimaryField(order_t)
            foo.field_name = NAME
            self.assertEqual(foo.as_default_order_key(), asst)

    def test_basic_primary_field(self):
        class ORZFieldTest(object):
            foo = OrzField()
            bar = OrzField()
        self.klass = ORZFieldTest

        field = _initialize_primary_field(self.klass)
        self.assertTrue(hasattr(self.klass, 'id'))
        self.assertEqual(field.field_name, 'id')

    def test_customized_primary_field(self):
        class ORZFieldTest(object):
            foo_bar = OrzPrimaryField()
            foo = OrzField()
            bar = OrzField()

        field = _initialize_primary_field(ORZFieldTest)
        self.assertTrue(hasattr(ORZFieldTest, 'foo_bar'))
        self.assertEqual(field.field_name, 'foo_bar')


@patch("ORZ.klass_init.warnings.warn")
class TestOrderDecl(TestCase):
    def test_functionality(self, mock_warn):
        class ORZTest(object):
            class OrzMeta:
                order_combs = (("hello", ), ('mm','-yy'), "zzz")
        combs = _collect_order_combs(ORZTest)
        self.assertEqual(combs, (('hello',), ('mm', '-yy'), ("zzz", )))

    def test_deprecated(self, mock_warn):
        class ORZTest(object):
            class OrzMeta:
                extra_orders = (("hello", ),)

        combs = _collect_order_combs(ORZTest)
        mock_warn.assert_called_with("extra_orders is deprecated; use order_combs instead.")

    def test_override(self, mock_warn):
        class ORZTest(object):
            class OrzMeta:
                order_combs = (("hello", "yy"),)
                extra_orders = (("hello", ),)

        combs = _collect_order_combs(ORZTest)
        mock_warn.assert_called_with("order_combs will override extra_orders. use order_combs only")
