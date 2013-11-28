# -*- coding:utf8 -*-
from .cache_mgr import CachedOrmManager
from .mixed_ins import *
from .base_mgr import OrmItem, OrzField, OrzPrimaryField
from .klass_init import _split_dictonary, _initialize_primary_field, _collect_fields, _collect_order_combs

def method_combine(func, reserved_args=tuple()):
    def _combine(cls_or_self, **kw):
        # 参数的问题没有想清楚，所以下面有些BadSmell
        reserved_kw, exclude_kw = _split_dictonary(kw, lambda k, _: k in reserved_args)
        def call_after(belonged):
            if hasattr(belonged, "after_"+func.func_name):
                after_func = getattr(belonged, "after_"+func.func_name)
                after_func(**exclude_kw)

        if hasattr(cls_or_self, "before_"+func.func_name):
            before_func = getattr(cls_or_self, "before_"+func.func_name)
            before_func(**kw)

        ret = func(cls_or_self, **reserved_kw)
        call_after(cls_or_self if ret is None else ret)
        return ret
    return _combine

def cached_wrapper(cls, table_name, sqlstore=None, mc=None, cache_ver='', id2str=True):
    primary_field = _initialize_primary_field(cls)
    db_fields, raw_db_fields = zip(*_collect_fields(cls, id2str))
    order_combs = _collect_order_combs(cls)


    cls.objects = CachedOrmManager(table_name,
                                   cls,
                                   raw_db_fields,
                                   sqlstore=sqlstore,
                                   mc=mc,
                                   cache_ver=cache_ver,
                                   order_combs=order_combs)


    cls.save = method_combine(save)
    cls.create = classmethod(method_combine(create, db_fields))
    cls.delete = method_combine(delete)
    cls.__org_init__ = cls.__init__
    cls.__init__ = init
    cls.__setstate__ = setstate
    cls.__getstate__ = getstate
    cls.db_fields = db_fields
    cls.gets_by = cls.objects.gets_by
    cls.count_by = cls.objects.count_by
    cls.get_by = cls.objects.get

    for f in raw_db_fields:
        setattr(cls, f.name, OrmItem(f.name, f.output_filter))
    return cls

