# -*- coding:utf8 -*-
from functools import wraps

from .cache_mgr import CachedOrmManager
from .base_mgr import OrmItem, OrzField, OrzPrimaryField
import warnings

def _split_dictonary(di, predicate):
    include_kw, exclude_kw  = {}, {}
    for k, v in di.iteritems():
        if predicate(k, v):
            include_kw[k] = v
        else:
            exclude_kw[k] = v
    return include_kw, exclude_kw


def _initialize_primary_field(cls):
    primary_fields = [(i, v) for i, v in cls.__dict__.iteritems() if isinstance(v, OrzPrimaryField)]
    if len(primary_fields) > 1:
        raise ValueError("one primary_field only")

    if len(primary_fields) == 0:
        v = OrzPrimaryField()
        v.name = "id"
        setattr(cls, 'id', v)
        return v
    else:
        field_name, field = primary_fields[0]
        field.name = field_name
        return field


def _collect_fields(cls, id2str):
    for i, v in cls.__dict__.iteritems():
        if isinstance(v, OrzField):
            v.name = i
            if id2str and i=='id' or i.endswith("_id"):
                v.output_filter = str
            yield (i, v)


def _collect_order_combs(cls):
    if hasattr(cls, "OrzMeta"):
        declarations = tuple()

        if hasattr(cls.OrzMeta, 'extra_orders'):
            declarations = getattr(cls.OrzMeta, "extra_orders")
            warnings.warn("extra_orders is deprecated; use order_combs instead.")

        if hasattr(cls.OrzMeta, 'order_combs'):
            if declarations:
                warnings.warn("order_combs will override extra_orders. use order_combs only")
            declarations = getattr(cls.OrzMeta, "order_combs")

        order_combs = tuple(((i, ) if type(i) is str else i) for i in declarations)
    else:
        order_combs = tuple()
    return order_combs


class OrzMeta(type):
    def __init__(cls, cls_name, bases, di):
        if cls.__orz_table__ is not None:
            from .environ import orz_mc, orz_sqlstore

            table_name = cls.__orz_table__
            cache_ver = getattr(cls.OrzMeta, 'cache_ver', '')
            id2str = getattr(cls.OrzMeta, 'id2str', False)
            primary_field = _initialize_primary_field(cls)
            db_fields, raw_db_fields = zip(*_collect_fields(cls, id2str))
            order_combs = _collect_order_combs(cls)
            cls.db_fields = db_fields
            cls.objects = CachedOrmManager(table_name,
                                           cls,
                                           raw_db_fields,
                                           sqlstore=orz_sqlstore,
                                           mc=orz_mc,
                                           cache_ver=cache_ver,
                                           order_combs=order_combs)
            for f in raw_db_fields:
                setattr(cls, f.name, OrmItem(f.name, f.output_filter))


class OrzBase(object):

    objects = None

    __metaclass__ = OrzMeta

    __orz_table__ = None

    __orz_cache_ver__ = ""

    class OrzMeta:
        cache_ver = ""

    def _refresh_db_fields(self, kw):
        self.dirty_fields = set()
        for i in self.db_fields:
            val = kw.pop(i)
            setattr(self, i, val)
        self._initted = True

    def __init__(self, to_create=False, *a, **kw):
        self.to_create = to_create
        if not to_create:
            self._initted = False
            self._refresh_db_fields(kw)
            self._initted = True
            self._detached = False
        else:
            self._initted = False
            for k, v in kw.iteritems():
                setattr(self, k, v)
            self._initted = False
            self._detached = True

    def _do_create(self, **kw):
        reserved_kw, exclude_kw = _split_dictonary(kw, lambda k, _: k in self.db_fields)
        self._detached = True
        self.before_create(**exclude_kw)

        data = self.objects.create_record(reserved_kw)
        self._detached = False
        self._refresh_db_fields(data)

        self.after_create(**exclude_kw)

    def __detached_proof(func):
        @wraps(func)
        def __(self, *a, **kw):
            if self._detached:
                raise AttributeError("The %s can't be called when the instance is detached, namely not created or just deleted" % func.func_name)
            return func(self, *a, **kw)
        return __

    @classmethod
    def create(cls, **kw):
        ins = cls(to_create=True, detached=False, **kw)
        ins._do_create(**kw)
        return ins

    @__detached_proof
    def save(self):
        self.before_save()
        self.objects.save(self)
        self.after_save()

    @__detached_proof
    def delete(self):
        self.before_delete()

        self.objects.delete(self)

        self._detached = True
        self.after_delete()

    def __getstate__(self):
        ret = {'dict': self.__dict__.copy(), 'db_fields': {}}

        for i in self.db_fields:
            ret['db_fields'][i] = getattr(self, i)

        return ret

    def __setstate__(self, state):
        self.__dict__.update(state['dict'])
        self._initted = False
        for i in self.db_fields:
            setattr(self, i, state['db_fields'][i])
        self._initted = True

    @classmethod
    def gets_by(cls, *a, **kw):
        return cls.objects.gets_by(*a, **kw)

    @classmethod
    def get_by(cls, *a, **kw):
        return cls.objects.get(*a, **kw)

    @classmethod
    def count_by(cls, *a, **kw):
        return cls.objects.count_by(*a, **kw)

    def after_create(self, **kw):
        pass

    def before_create(self, **kw):
        pass

    def before_save(self):
        pass

    def after_save(self):
        pass

    def before_delete(self):
        pass

    def after_delete(self):
        pass

