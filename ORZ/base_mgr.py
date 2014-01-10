import sys
from functools import wraps
from MySQLdb import IntegrityError
from functools import wraps
from contextlib import contextmanager

class OrmItem(object):
    def __init__(self, field_name, output_filter=lambda x: x):
        self.field_name = field_name
        self.output_filter = output_filter

    def __set__(self, obj, value):
        value = int(value) if type(value) == bool else value

        if not obj._initted:
            setattr(obj, "hidden____org_" + self.field_name, value)
        else:
            obj.dirty_fields.add(self.field_name)

        setattr(obj, "hidden____" + self.field_name, value)

    def __get__(self, obj, objtype):
        return self.output_filter(getattr(obj, "hidden____" + self.field_name, None))


class OrzField(object):
    NO_DEFAULT = sys.maxint
    name = None

    class KeyType(object):
        NOT_INDEX, DESC, ASC, AD = range(4)

    def __init__(self, as_key=KeyType.NOT_INDEX, default=NO_DEFAULT, output_filter=lambda x:x):
        self.name = None
        self.as_key = as_key
        self.default = default
        self.output_filter = output_filter


class OrzPrimaryField(OrzField):
    class OrderType(object):
        DESC, ASC, AD = range(3)

    _order_tranformation = {
        OrderType.DESC: ('-%s',),
        OrderType.ASC: ('%s', ),
        OrderType.AD: ('-%s', ),
    }

    def __init__(self, order_kind=OrderType.DESC):
        keytype_tranform = {
            self.OrderType.DESC: OrzField.KeyType.DESC,
            self.OrderType.ASC: OrzField.KeyType.ASC,
            self.OrderType.AD: OrzField.KeyType.AD,
        }
        super(OrzPrimaryField, self).__init__(keytype_tranform[order_kind])
        self.order_kind = order_kind

    def as_default_order_key(self):
        if self.name is None:
            raise ValueError('name is needed')
        return tuple([i % self.name for i in self._order_tranformation[self.order_kind]])

def orz_get_multi(func):
    @wraps(func)
    def __(self_or_cls, *a, **kw):
        return self_or_cls.objects.get_multiple_ids(func(self_or_cls, *a, **kw))
    return __

@contextmanager
def start_transaction(*cls_or_ins):
    assert len(cls_or_ins) > 0

    for c in cls_or_ins:
        for i in ['delete', 'save', 'create']:
            setattr(c, 'old_'+i, getattr(c, i))
            setattr(c, i, getattr(c, i+'_transactionally'))

    try:
        yield cls_or_ins
    except (IntegrityError, OrzForceRollBack):
        cls_or_ins[0].objects.sql_executor.sqlstore.rollback()
    else:
        cls_or_ins[0].objects.sql_executor.sqlstore.commit()
    finally:
        for c in cls_or_ins:
            for i in ['delete', 'save', 'create']:
                setattr(c, i, getattr(c, 'old_'+i))


class OrzForceRollBack(Exception):
    pass


if __name__=='__main__':
    pass
