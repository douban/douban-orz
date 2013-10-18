# -*- coding:utf8 -*-
import sys
from collections import defaultdict

from .sql_executor import SqlExecutor
from .base_mgr import OrmItem, OrzField
from .mixed_ins import *
from .configs import CacheConfigMgr, Config

mc = None

ONE_HOUR=3600

EPSILON = None

HEADQUARTER_VERSION = '3'


def make_orders(fields):
    mapper = {
        OrzField.KeyType.DESC: lambda x, y: x + [("-%s" % y.name,)],
        OrzField.KeyType.ASC: lambda x, y: x + [("%s" % y.name,)],
        OrzField.KeyType.AD: lambda x, y: x + [("%s" % y.name, ), ("-%s" % y.name)],
        OrzField.KeyType.NOT_INDEX: lambda x, y: x,
    }
    return tuple(reduce(lambda x, y:mapper[y.as_key](x, y), fields, []))

class CachedOrmManager(object):
    # TODO mgr.db_fields is sql_executor's
    def __init__(self, table_name, cls, db_fields, custom_cache, cache_ver='', extra_orders=tuple(), sqlstore=None):
        self.single_obj_ck = "a" + HEADQUARTER_VERSION + "%s:single_obj_ck:" % table_name + cache_ver
        self.sql_executor = SqlExecutor(self, table_name, [f.name for f in db_fields], sqlstore)
        self.cls = cls
        kv_to_ids_ck = "a" + HEADQUARTER_VERSION + "%s:kv_to_ids:" % table_name + cache_ver
        self.config_mgr = CacheConfigMgr()

        orders = make_orders(db_fields) + extra_orders
        self.config_mgr.generate_basic_configs(kv_to_ids_ck,
                                               [f.name for f in db_fields if f.as_key], orders)

        self.default_vals = dict((k.name, k.default) for k in db_fields if k.default is not None)

    def __getattr__(self, field):
        return getattr(self.sql_executor, field)

    def _get_and_refresh(self, sql_executor, ids):
        res = []
        di = dict(zip(ids, mc.get_list([self.single_obj_ck + str(i) for i in ids])))

        for i in ids:
            if di[i] is not None:
                obj = di[i]
            else:
                obj = self.cls(**sql_executor.get(i))
                mc.set(self.single_obj_ck + str(i), obj, ONE_HOUR)
            res.append(obj)
        return res

    def get(self, id):
        ret = self.filter(id=id).fetch()
        if len(ret) == 0:
            return None
        return ret[0]

    def get_multiple_ids(self, ids):
        return self._get_and_refresh(self.sql_executor, ids)

    def _amount_check(self, amount, start_limit):
        if not start_limit:
            return True

        start, limit = start_limit
        if start + limit > amount:
            return True

        return False

    def fetch(self, sql_executor, **kwargs):
        amount = sys.maxint
        start_limit = sql_executor.start_limit
        if sql_executor.conditions:
            config = self.config_mgr.lookup_gets_by(sql_executor.conditions.keys()+
                                                    ['order_by:'+sql_executor.org_order_key, ])
            if amount is not None and \
                self._amount_check(amount, sql_executor.start_limit):
                ids = sql_executor.get_ids()
                return [self.cls(**sql_executor.get(i)) for i in ids]

            ck = config.to_string(sql_executor.conditions)
            ids = mc.get(ck)

            sql_executor.start_limit = (0, amount) if amount is not None else tuple()
            if ids is not None:
                ret = self._get_and_refresh(sql_executor, ids)
            else:
                ids = sql_executor.get_ids()
                mc.set(ck, ids, ONE_HOUR)
                ret = self._get_and_refresh(sql_executor, ids)
        else:
            ids = sql_executor.get_ids()
            ret = [self.cls(**sql_executor.get(i)) for i in ids]

        if start_limit:
            start, limit = start_limit
            return ret[start:start + limit]
        return ret

    def count(self, sql_executor):
        config = self.config_mgr.lookup_normal(sql_executor.conditions.keys())
        ck = config.to_string(sql_executor.conditions)
        c = mc.get(ck)
        if c is None:
            ret = sql_executor.calc_count()
            mc.set(ck, ret, ONE_HOUR)
            return ret
        else:
            return c

    def create(self, raw_kwargs):
        fields_without_pk = set(self.db_fields) - set(['id'])
        kwargs = self.default_vals.copy()
        kwargs.update(raw_kwargs)
        cks = self._get_cks(kwargs, fields_without_pk)
        mc.delete_multi(cks)

        sql_data = dict((field, kwargs.pop(field)) for field in fields_without_pk)
        _id = self.sql_executor.create(sql_data)

        return self.cls(id=_id, **sql_data)

    def _get_cks(self, data_src, fields):
        cks = []
        for field in fields:
            configs = self.config_mgr.lookup_related(field)
            for c in configs:
                field_cks = c.to_string(data_src)
                cks.append(field_cks)
        return cks

    def save(self, ins):
        cks = []
        datum = dict((f, getattr(ins, "hidden____org_" + f)) for f in self.db_fields)
        cks.extend(self._get_cks(datum, ins.dirty_fields))
        cks.extend(self._get_cks(ins, ins.dirty_fields))

        all_cks = cks + [self.single_obj_ck+str(ins.id)]
        mc.delete_multi(all_cks)

        sql_data = dict((field, getattr(ins, field)) for field in ins.dirty_fields)
        self.sql_executor.update_row(ins.id, sql_data)

    def delete(self, ins):
        cks = self._get_cks(ins, ["id",]+self.db_fields)
        mc.delete_multi(cks + [self.single_obj_ck+str(ins.id)])

        self.sql_executor.delete(ins.id)

    def gets_by(self, order_by='-id', start=0, limit=sys.maxint, **kw):
        return self.filter(**kw).order_by(order_by).limit(start, limit).fetch()

    def count_by(self, **kw):
        limit = kw.pop('limit', None)
        if limit is None:
            return self.filter(**kw).count()

    def gets_custom(self, func, a, kw):
        func_name = func.func_name
        cfg = self.config_mgr.lookup_custom([func_name,]+kw.keys())
        ck = cfg.to_string(kw)
        ret = mc.get(ck)
        if ret is None:
            ret = func(self.cls, *a, **kw)
            mc.set(ck, ret)
        return ret


def method_combine(func):
    def _(*a, **kw):
        # 参数的问题没有想清楚，所以下面有些BadSmell
        def call_after(belonged):
            if hasattr(belonged, "after_"+func.func_name):
                getattr(belonged, "after_"+func.func_name)()

        if hasattr(a[0], "before_"+func.func_name):
            getattr(a[0], "before_"+func.func_name)()

        ret = func(*a, **kw)
        call_after(a[0] if ret is None else ret)
        return ret
    return _



def cached_wrapper(cls, table_name, cache_ver='', id2str=True, inj_store=None, inj_mc=None):
    # 3 lines below is temporary fix
    global mc
    mc = inj_mc

    setattr(cls, 'id', OrzField(as_key=OrzField.KeyType.DESC))
    raw_db_fields = []
    db_fields = []
    custom_cache = []
    for i, v in cls.__dict__.iteritems():
        if isinstance(v, OrzField):
            v.name = i
            raw_db_fields.append(v)
            db_fields.append(i)
        # elif callable(getattr(cls, i)) and hasattr(getattr(cls, i), 'related_key_names'):
        #     custom_cache.append((i, getattr(cls, i).related_key_names))

    if hasattr(cls, "OrzMeta"):
        extra_orders = tuple([(tuple(i) if type(i)==str else i) for i in getattr(cls.OrzMeta, 'extra_orders', tuple())])
    else:
        extra_orders = tuple()



    cls.objects = CachedOrmManager(table_name,
                                   cls,
                                   raw_db_fields,
                                   custom_cache,
                                   cache_ver=cache_ver,
                                   extra_orders=extra_orders,
                                   sqlstore=inj_store)

    cls.dirty_fields = set()
    cls.id_casting = int if not id2str else str
    cls.save = method_combine(save)
    cls.create = classmethod(method_combine(create))
    cls.delete = method_combine(delete)
    cls.__org_init__ = cls.__init__
    cls.__init__ = init
    cls.__setstate__ = setstate
    cls.__getstate__ = getstate
    cls.db_fields = db_fields
    cls.gets_by = cls.objects.gets_by
    cls.count_by = cls.objects.count_by
    cls.get_by = cls.objects.get

    for k in db_fields:
        setattr(cls, k,  OrmItem(k))
    return cls

