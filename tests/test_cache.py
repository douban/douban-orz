from unittest import TestCase, skip

from .env_init import store, mc, initted
from ORZ.exports import OrzBase, OrzField, orz_get_multi, OrzPrimaryField, setup as setup_orz

class MCDetector(object):
    def __init__(self, mc):
        self.mc = mc
        self.hitted = False

    def get(self, key):
        ret = self.mc.get(key)
        self.hitted = (ret is not None)
        return ret


    def __getattr__(self, attr):
        return getattr(self.mc, attr)

mcd = MCDetector(mc)
setup_orz(store, mcd)

class Dummy(OrzBase):
    __orz_table__ = 'test_orz'

    subject_id = OrzField(as_key=OrzField.KeyType.ASC)
    ep_num = OrzField(as_key=OrzField.KeyType.ASC, default=0)
    content = OrzField(default='hello world')

class TestCache(TestCase):
    def setUp(self):
        cursor = store.get_cursor()
        cursor.execute('''DROP TABLE IF EXISTS `test_orz`''')
        cursor.delete_without_where = True
        cursor.execute('''
                       CREATE TABLE `test_orz`
                       ( `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
                       `subject_id` int(10) unsigned NOT NULL,
                       `ep_num` int(10) unsigned NOT NULL,
                       `content` varchar(100) NOT NULL,
                       PRIMARY KEY (`id`),
                       KEY `idx_subject` (`subject_id`, `ep_num`, `id`)) ENGINE=MEMORY AUTO_INCREMENT=1''')

    def tearDown(self):
        store.get_cursor().execute('truncate table `test_orz`')
        mc.clear()

    def test_invalidation(self):
        def run_pred(cond_and_pred):
            for cond, pred in cond_and_pred:
                Dummy.gets_by(**cond)
                self.assertEqual(mcd.hitted, pred)

        cond_all = dict(subject_id=1, ep_num=1)
        cond_1 = dict(subject_id=1)
        d = Dummy.create(**cond_all)
        before = (
            (cond_all, False),
            (cond_all, True),
            (cond_1, False),
            (cond_1, True),
        )

        after = (
            (cond_all, False),
            (cond_1, False),
        )

        run_pred(before)
        d.invalidate_cache()
        run_pred(after)

        mcd.clear()

        run_pred(before)
        Dummy.invalidate_cache_by_condition(**cond_all)
        run_pred(after)
