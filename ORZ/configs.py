from itertools import combinations, chain
from collections import defaultdict
from operator import attrgetter
from functools import partial


class Forward(object):
    def __init__(self, dest_obj_member, attr_name):
        self.dest = attr_name
        self.dest_obj_member = dest_obj_member

    def __get__(self, obj, objtype):
        return getattr(getattr(obj, self.dest_obj_member), self.dest)


def partial_method(func, **kw):
    def __(*a, **nkw):
        nkw.update(kw)
        return func(*a, **nkw)
    return __



def serialize_kv_alphabetically(di):
    def change_bool(value):
        return int(value) if type(value) == bool else value
    return '|'.join(["%s=%s" % (k, change_bool(di[k])) for k in sorted(di.keys())]).replace(" ", "")


class CacheConfigMgr(object):
    def __init__(self):
        self.gets_by_config_coll = {}
        self.normal_config_coll = {}
        self.custom_config_coll = {}
        self.key_related = defaultdict(list)

    def _add(self, config):
        if isinstance(config, Config):
            config_coll = self.normal_config_coll
        elif isinstance(config, GetsByConfig):
            config_coll = self.gets_by_config_coll
        else:
            raise ValueError("Config like object only")

        config_coll[config.as_key()] = config

    def items(self):
        for member in [self.gets_by_config_coll, self.normal_config_coll]:
            for i in member.itervalues():
                yield i

    def add_custom(self, config):
        self.custom_config_coll[(config.prefix,)+config.as_key()] = config
        for k in config.keys:
            self.key_related[k].append(config)


    def generate_basic_configs(self, prefix, key_field_names, orders=tuple()):
        comb = list(chain(*[combinations(key_field_names, i) for i in range(1, len(key_field_names)+1)]))
        cfgs = []

        for i in comb:
            c = Config(prefix, i)
            cfgs.append(c)
            self._add(c)

        for c in cfgs:
            for e in orders:
                self._add(GetsByConfig(c, e))

        for i in self.items():
            for k in i.keys:
                self.key_related[k].append(i)

    def _lookup(self, raw_keywords, configs_getter):
        keywords = tuple(sorted(raw_keywords))
        return configs_getter(self)[keywords]

    def lookup_related(self, field):
        return self.key_related[field]


    lookup_gets_by, lookup_normal, lookup_custom = \
            [partial_method(_lookup, configs_getter = attrgetter(i+'_config_coll')) for i in ['gets_by', 'normal', 'custom']]



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
        self.keys = tuple(config.keys) + order
        self.order = 'order_by:' + ('|'.join(order).replace(" ", ""))

    def as_key(self):
        return tuple(sorted(self.config.as_key() + (self.order, )))

    def to_string(self, data):
        return self.config.to_string(data) + "|" + self.order