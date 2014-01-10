MEMCACHED = {
    'servers' : [],
    'disabled' : False,
}

# from corelib.config import MEMCACHED
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "stub"))

from douban.mc import mc_from_config
from douban.mc.wrapper import LocalCached
mc = LocalCached(mc_from_config(MEMCACHED))

from douban.sqlstore import store_from_config
from ORZ import orz_decorate, OrzField, orz_get_multi, start_transaction, OrzForceRollBack

DATABASE = {
    'farms': {
        "luz_farm": {
            "master": "localhost:test_vagrant9010:eye:sauron",
            "tables": ["*"],
            },
    },
    'options': {
        'show_warnings': True,
    }
}

from unittest import TestCase

store = store_from_config(DATABASE)
mc.clear()

cursor = store.get_cursor()
cursor.delete_without_where = True
cursor.execute('''DROP TABLE IF EXISTS `test_t`''')
cursor.execute('''
               CREATE TABLE `test_t`
               ( `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
               `subject_id` int(10) unsigned NOT NULL,
               PRIMARY KEY (`id`),
               UNIQUE KEY `uk_subject` (`subject_id`)) ENGINE=MEMORY AUTO_INCREMENT=1''')
cursor.execute('''DROP TABLE IF EXISTS `test_a`''')
cursor.execute('''
               CREATE TABLE `test_a`
               ( `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
               `ep_num` int(10) unsigned NOT NULL,
               PRIMARY KEY (`id`),
               KEY `ep_num_idx` (`ep_num`)
               ) ENGINE=MEMORY AUTO_INCREMENT=1''')

@orz_decorate('test_t', sqlstore=store, mc=mc)
class TestT(object):
    subject_id = OrzField(OrzField.KeyType.DESC)

    def after_create(self):
        print "333d"
        self.after_create = True

    def after_save(self):
        print "333d"*3
        self.after_save = True

@orz_decorate('test_a', sqlstore=store, mc=mc)
class TestA(object):
    ep_num = OrzField(OrzField.KeyType.DESC)


class TestTransacation(TestCase):
    def tearDown(self):
        cursor.execute("truncate table `test_a`")
        cursor.execute("truncate table `test_t`")

    def test_basic(self):
        TestA.create(ep_num=1)
        TestA.gets_by(ep_num=1)
        TestA.count_by(ep_num=1)

        m = 0
        before = TestA.create
        with start_transaction(TestT, TestA) as (test_t, test_a):
            zz = test_t.create(subject_id=1)
            m = test_a.create(ep_num=1)
            self.assertNotEqual(before, TestA.create)
            self.assertEqual(TestA.create, TestA.create_transactionally)

        after = TestA.create

        self.assertEqual(before, after)
        self.assertTrue(zz.after_create)
        qrset = [str(i) for i, in store.execute('select id from test_a order by id')]
        self.assertEqual(qrset[-1], m.id)
        self.assertEqual(len(TestA.gets_by(ep_num=1)), 2)
        self.assertEqual(TestA.gets_by(ep_num=1)[0].id, m.id)

    def test_rollback(self):
        TestT.create(subject_id=1)
        with start_transaction(TestT, TestA) as (test_t, test_a):
            test_t.create(subject_id=1)
            m = test_a.create(ep_num=1)
        qrset = [str(i) for i, in store.execute('select id from test_a order by id')]
        self.assertEqual(len(qrset), 0)

    def test_rollback2(self):
        m = TestT.create(subject_id=1)
        TestA.create(ep_num=10)
        a = TestA.gets_by(ep_num=10)[0]

        def run(t_ins, a_ins):
            with start_transaction(t_ins, a_ins) as (test_t_ins, test_a_ins):
                ret = test_a_ins.delete()
                if ret == 0:
                    raise OrzForceRollBack
                test_t_ins.subject_id = 2
                test_t_ins.save()
        store.execute('delete from test_a where id=%s', a.id)
        run(m, a)
        self.assertEqual(TestT.gets_by(subject_id=1)[0].id, m.id)

        new_a = TestA.create(ep_num=10)
        run(m, new_a)
        self.assertEqual(TestT.gets_by(subject_id=2)[0].id, m.id)
