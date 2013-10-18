from unittest import TestCase
from itertools import combinations, chain
from orz.configs import GetsByConfig, Config, CacheConfigMgr

class TestGetsByConfigs(TestCase):
    def test_hash_keys(self):
        keys = ['a', 'b', 'c', 'd']
        config = Config('111', keys)
        cfg = GetsByConfig(config, 'c')
        self.assertEqual(cfg.as_key(), tuple(sorted(config.as_key()+(cfg.order,))))

    def test_to_strings(self):
        kw = {'a':1, 'b':2}
        cfg = GetsByConfig(Config('111', kw.keys()), 'a')
        self.assertEqual(cfg.to_string(kw), '111:a=1|b=2|order_by:a')


class TestConfigMgr(TestCase):
    def setUp(self):
        self.config = Config("11111", ("a", "b"))
        self.gets_by_config = GetsByConfig(self.config, "a")

    def test_add(self):
        mgr = CacheConfigMgr()
        mgr._add(self.config)
        self.assertEqual(len(mgr.normal_config_coll), 1)
        self.assertEqual(mgr.normal_config_coll[self.config.as_key()], self.config)

        mgr._add(self.gets_by_config)
        self.assertEqual(len(mgr.normal_config_coll), 1)
        self.assertEqual(len(mgr.gets_by_config_coll), 1)
        self.assertEqual(mgr.gets_by_config_coll[self.gets_by_config.as_key()], self.gets_by_config)

    def test_lookup(self):
        mgr = CacheConfigMgr()
        mgr._add(self.config)
        mgr._add(self.gets_by_config)

        self.assertEqual(mgr.lookup_normal(("b", "a")) , self.config)
        self.assertEqual(mgr.lookup_gets_by(("b", "a", "order_by:a")) , self.gets_by_config)

    def test_gen_basic_configs(self):
        sort_ = lambda x: sorted(x, key= lambda x:''.join(x))
        keys = ("a", "b", "c")
        mgr = CacheConfigMgr()
        mgr.generate_basic_configs('1111', keys, keys)

        self.assertEqual(len(mgr.normal_config_coll), 7)
        self.assertEqual(len(mgr.gets_by_config_coll), 7*3)

        key_combs = list(chain(*[combinations(keys, i) for i in range(1, 4)]))

        self.assertEqual(sort_(mgr.normal_config_coll.keys()), sort_(key_combs))

        key_combs_with_order = [k+("order_by:"+i, ) for k in key_combs for i in keys]
        self.assertEqual(sort_(mgr.gets_by_config_coll.keys()), sort_(key_combs_with_order))

    def test_lookup_related(self):
        sort_ = lambda x: sorted(x, key= lambda x:''.join(x))
        keys = ("a", "b")
        mgr = CacheConfigMgr()
        mgr.generate_basic_configs('1111', keys)
        cfgs = mgr.lookup_related("a")
        predate_configs = [c for c in mgr.items() if "a" in c.keys]
        self.assertEqual(sort_([i.as_key() for i in cfgs]),
                         sort_([i.as_key() for i in predate_configs]))


