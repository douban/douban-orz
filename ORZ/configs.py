from itertools import combinations, chain
from collections import defaultdict
from operator import attrgetter
from functools import partial
import logging


class Forward(object):
    def __init__(self, dest_obj_member, attr_name):
        self.dest = attr_name
        self.dest_obj_member = dest_obj_member

    def __get__(self, obj, objtype):
        return getattr(getattr(obj, self.dest_obj_member), self.dest)


def serialize_kv_alphabetically(di):
    def change_bool(value):
        return int(value) if type(value) == bool else value
    return '|'.join(["%s=%s" % (k, change_bool(di[k])) for k in sorted(di.keys())]).replace(" ", "")


class ConfigColl(object):
    def __init__(self):
        self._coll = {}

    def __getitem__(self, key):
        try:
            return self._coll[key]
        except KeyError:
            logging.warning("your query key [%s] doesn't match your previous definition" % str(key))
            return None

    def __setitem__(self, key, val):
        self._coll[key] = val

    def itervalues(self):
        return self._coll.itervalues()

    def __len__(self):
        return len(self._coll)

    def keys(self):
        return self._coll.keys()


class CacheConfigMgr(object):
    def __init__(self):
        self.gets_by_config_coll = ConfigColl()
        self.normal_config_coll = ConfigColl()
        self.key_related = defaultdict(list)

    def add_to(self, config_coll, config):
        for key in config.keys:
            self.key_related[key].append(config)

        config_coll[config.as_key()] = config

    def items(self):
        for member in [self.gets_by_config_coll, self.normal_config_coll]:
            for i in member.itervalues():
                yield i

    def generate_basic_configs(self, prefix, key_field_names, orders=tuple()):
        comb = list(chain(*[combinations(key_field_names, i) for i in range(1, len(key_field_names)+1)]))
        cfgs = []

        for i in comb:
            c = Config(prefix, i)
            self.add_to(self.normal_config_coll, c)
            cfgs.append(c)

        for c in cfgs:
            for e in orders:
                self.add_to(self.gets_by_config_coll, GetsByConfig(c, e))


    def lookup_normal(self, raw_keywords):
        keywords = tuple(sorted(raw_keywords))
        return self.normal_config_coll[keywords]

    def lookup_related(self, field):
        return self.key_related[field]

    def lookup_gets_by(self, fields, order_by_fields=('-id',)):
        order_bys = ('order_by:%s' % ('|'.join(sorted(order_by_fields))), )
        keywords = tuple(sorted(tuple(fields) + order_bys))
        return self.gets_by_config_coll[keywords]


class Config(object):
    def __init__(self, prefix, keys):
        self.keys = keys
        self.prefix = prefix

    def as_key(self):
        return tuple(sorted(self.keys))

    def to_string(self, data):
        if type(data) == dict:
            func = data.get
        else:
            func = lambda x: getattr(data, x)

        _t_str = serialize_kv_alphabetically(dict((f, func(f)) for f in self.keys))
        return self.prefix + ":" + _t_str


class GetsByConfig(object):
    def __init__(self, config, order):
        self.config = config
        # self.keys = tuple(config.keys) + order
        self.keys = tuple(config.keys) + tuple(i.strip("-") for i in order)
        self.order = 'order_by:' + ('|'.join(sorted(order)).replace(" ", ""))

    def as_key(self):
        return tuple(sorted(self.config.as_key() + (self.order, )))

    def to_string(self, data):
        return self.config.to_string(data) + "|" + self.order
