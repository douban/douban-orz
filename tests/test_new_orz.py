from unittest import TestCase, skip

from .env_init import store, mc, initted
from ORZ.exports import OrzBase, OrzField, orz_get_multi, OrzPrimaryField, setup as setup_orz

setup_orz(store, mc)

class TestNewOrz(TestCase):
    def setUp(self):
        cursor = store.get_cursor()
        cursor.execute('''DROP TABLE IF EXISTS `test_orz`''')
        cursor.delete_without_where = True
        cursor.execute('''
                       CREATE TABLE `test_orz`
                       ( `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
                       `subject_id` int(10) unsigned NOT NULL,
                       `ep_num` int(10) unsigned NOT NULL,
                       `flag` smallint(1) unsigned NOT NULL,
                       `content` varchar(100) NOT NULL,
                       `extra` int(10) unsigned NOT NULL,
                       `null_field` int(10) unsigned,
                       `output_field` int(10) unsigned,
                       `callable_field` int(10) unsigned,
                       PRIMARY KEY (`id`),
                       KEY `idx_subject` (`subject_id`, `ep_num`, `id`)) ENGINE=MEMORY AUTO_INCREMENT=1''')

    def tearDown(self):
        store.get_cursor().execute('truncate table `test_orz`')
        mc.clear()

    def test_create(self):
        z = Dummy.create(subject_id=10, ep_num=10, content='hheheheh', extra_args=10)
        self.assertTrue(z.after_created)
        self.assertEqual(z.callable_field, 10)
        self.assertTrue(z.extra_args, 10)
        self.assertEqual(z.null_field, None)
        (id, subject_id, ep_num, null_field), = store.execute('''select id, subject_id, ep_num, null_field from test_orz where subject_id=10''')
        self.assertEqual((z.id, z.subject_id, ep_num, None), (str(id), str(subject_id), ep_num, null_field))

        z = Dummy.create(id=5, subject_id=10, ep_num=10, content='hheheheh1')
        self.assertEqual(z.id, '5')

        self.assertRaises(ValueError, Dummy.create, **dict(id=5, subject_id=-1, ep_num=10, content='hheheheh1'))

    def test_exist(self):
        self.assertFalse(Dummy.exist(subject_id=10, ep_num=10))

        z = Dummy.create(subject_id=10, ep_num=10, content='hheheheh', extra_args=10)
        self.assertTrue(Dummy.exist(subject_id=10, ep_num=10))
        self.assertTrue(Dummy.exist(id=z.id))

    def test_gets_by(self):
        li = [Dummy.create(subject_id=10, ep_num=ep_num, content='hheheheh', output_field=10+ep_num) for ep_num in range(10)]
        z = li[-1]
        m = Dummy.gets_by(subject_id=10)
        self.assertEqual((z.id, z.subject_id), (m[0].id, m[0].subject_id))
        self.assertEqual([int(i.id) for i in m], range(10, 0, -1))
        self.assertEqual(li[-1].output_field, str(19))

        self.assertEqual(Dummy.gets_by(output_field=19)[0].id, li[-1].id)

    def test_save(self):
        z = Dummy.create(subject_id=10, ep_num=10, content='hheheheh')
        m = Dummy.gets_by(subject_id=10)[0]
        self.assertRaises(AttributeError, lambda :m.after_saved)
        m.subject_id = 2
        m.save()
        self.assertTrue(m.after_saved)

        old_fetched = Dummy.gets_by(subject_id=10)
        new_fetched = Dummy.gets_by(subject_id=2)
        self.assertEqual(len(old_fetched), 0)
        self.assertEqual(new_fetched[0].subject_id, '2')

    def test_count_by(self):
        for i in range(10):
            Dummy.create(subject_id=10, ep_num=i, content='hheheheh')

        self.assertEqual(Dummy.count_by(subject_id=10), 10)
        m = Dummy.gets_by(subject_id=10)[0]
        m.subject_id = 2
        m.save()
        self.assertEqual(Dummy.count_by(subject_id=10), 9)

    def test_delete(self):
        m = Dummy.create(subject_id=10, ep_num=1, content='hheheheh')
        self.assertEqual(mc.get('before_delete_test'), None)
        m.delete()
        self.assertTrue(mc.get('before_delete_test'))

        ret = store.execute('''select id, subject_id, ep_num from test_orz where subject_id=10''')
        self.assertEqual(len(ret), 0)


    def test_default(self):
        a = Dummy.create(subject_id=10, ep_num=1)
        self.assertEqual(a.content, 'hello world')

        self.assertEqual(Dummy.gets_by(subject_id=10)[0].content, 'hello world')

        a = Dummy.create(subject_id=10)
        self.assertEqual(a.ep_num, 0)

        self.assertEqual(len(Dummy.gets_by(subject_id=10)), 2)

    def test_pager(self):
        for i in range(100):
            Dummy.create(subject_id=10, ep_num=i, content='hheheheh')

        data = Dummy.gets_by(subject_id=10, limit=50)
        self.assertEqual(len(data), 50)
        for i, o in enumerate(data):
            self.assertEqual(int(o.id), 100 - i)

        start = 20
        for i, o in enumerate(Dummy.gets_by(subject_id=10, start=start, limit=50), start):
            self.assertEqual(int(o.id), 100 - i)

    def test_boolean(self):
        for i in range(100):
            Dummy.create(subject_id=10, ep_num=i, content='hheheheh')

        qrset = Dummy.gets_by(flag=False)
        self.assertEqual(len(qrset), 100)

        qrset[0].flag = True
        qrset[0].save()
        self.assertEqual(len(Dummy.gets_by(flag=False)), 99)

    def test_order_by(self):
        for i in range(100, 90, -1):
            Dummy.create(subject_id=10, ep_num=i, content='hheheheh')

        self.assertEqual(range(91, 101), [i.ep_num for i in Dummy.gets_by(subject_id=10, order_by='ep_num')])

    def test_get_multiple_ids(self):
        ids = []
        for i in range(100, 90, -1):
            ids.append(Dummy.create(subject_id=10, ep_num=i, content='hheheheh').id)

        self.assertEqual([i.id for i in Dummy.objects.get_multiple_ids(ids)], ids)

    def test_orz_get_multi(self):
        for i in range(100, 90, -1):
            Dummy.create(subject_id=10, ep_num=i, content='hheheheh')

        self.assertTrue(100 not in [i.ep_num for i in Dummy.get_non_targeted(100)])

    def test_extra_order_by(self):
        # for i in range(100, 90, -1):
        #     Dummy.create(subject_id=10, ep_num=i, extra=10+i, content='hheheheh')

        # self.assertEqual(list(reversed(range(101, 111))), [i.extra for i in Dummy.gets_by(subject_id=10, order_by='-extra')])

        # Dummy.create(subject_id=10, ep_num=130, extra=130, content='hheheheh')
        # self.assertEqual([130]+list(reversed(range(101, 111))), [i.extra for i in Dummy.gets_by(subject_id=10, order_by='-extra')])

        for f in range(2):
            for j in range(23, 20, -1):
                Dummy.create(subject_id=9, ep_num=j, extra=f, content='hheheheh')
        output = [(i.ep_num, i.extra) for i in Dummy.gets_by(subject_id=9, order_by=('-extra', 'ep_num'))]
        self.assertEqual(output, [(i, j)  for j in (1, 0)  for i in range(21, 24)])

        for i in Dummy.gets_by(subject_id=9, order_by=('-extra', 'ep_num')):
            if i.extra == 0:
                i.extra = 1
                i.save()

        output = [(i.ep_num, i.extra) for i in Dummy.gets_by(subject_id=9, order_by=('-extra', 'ep_num'))]
        self.assertEqual(output, [(i, 1) for i in [21, 21, 22, 22, 23, 23]])


    def test_creation_should_delete_pk(self):
        ID = str(1000)
        empty = Dummy.get_by(ID)
        self.assertEqual(empty, None)

        Dummy.create(id=ID, subject_id=10, ep_num=1, content='hheheheh')

        new = Dummy.get_by(ID)
        self.assertEqual(new.id, ID)

    def test_flush_get(self):
        raw_num = 10
        i = Dummy.create(subject_id=10, ep_num=1, content='hheheheh')
        Dummy.get_by(id=i.id)

        store.execute('update test_orz set ep_num=%s where id=%s', (raw_num, i.id))
        store.commit()

        self.assertEqual(Dummy.get_by(id=i.id).ep_num, i.ep_num)
        flushed_obj = Dummy.get_by(id=i.id, force_flush=True)
        self.assertNotEqual(flushed_obj.ep_num, i.ep_num)
        self.assertEqual(flushed_obj.ep_num, raw_num)

        crset = []
        for i in range(10):
            crset.append(Dummy.create(subject_id=11, ep_num=11, content='hheheheh'+str(i)))

        Dummy.gets_by(subject_id=11, ep_num=11)

        self.assertEqual(len(Dummy.gets_by(subject_id=11, ep_num=11)), 10)

        store.execute('update test_orz set ep_num=%s where id=%s', (raw_num, crset[0].id))
        store.commit()

        self.assertEqual(len(Dummy.gets_by(subject_id=11, ep_num=11)), 10)
        self.assertEqual(len(Dummy.gets_by(subject_id=11, ep_num=11, force_flush=True)), 9)

    def test_detached(self):
        a = Dummy.create(subject_id=10001, ep_num=11, content='hheheheh')
        self.assertRaisesRegexp(AttributeError, "The save can't be called when the instance is detached",a.delete)

        a = Dummy.create(subject_id=10002, ep_num=11, content='hheheheh')
        self.assertRaisesRegexp(AttributeError, "The delete can't be called when the instance is detached",a.delete)

        self.assertRaisesRegexp(AttributeError,
                                "The save can't be called when the instance is detached",
                                Dummy.create, subject_id=-2, ep_num=11, content='hheheheh')
        self.assertRaisesRegexp(AttributeError,
                                "The delete can't be called when the instance is detached",
                                Dummy.create, subject_id=-3, ep_num=11, content='hheheheh')


class DummyBase(OrzBase):
    subject_id = OrzField()
    updated_at = OrzField()
    ep_num = OrzField()

class DummyCS(DummyBase):
    __orz_table__ = 'test_orz'

class TestFlushGetAfterCreationAndSaving(TestCase):

    def setUp(self):
        cursor = store.get_cursor()
        cursor.execute('''DROP TABLE IF EXISTS `test_orz`''')
        cursor.delete_without_where = True
        cursor.execute('''
                       CREATE TABLE `test_orz`
                       (
                       `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT,
                       `ep_num` int(10) unsigned NOT NULL,
                       `subject_id` int(10) unsigned DEFAULT 1001 NOT NULL,
                       `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                       PRIMARY KEY (`id`)
                       ) ENGINE=MEMORY AUTO_INCREMENT=1''')

    def tearDown(self):
        mc.clear()

    def test_create(self):
        from datetime import datetime, timedelta
        a = DummyCS.create(ep_num=1)
        now = datetime.now()
        self.assertEqual(a.subject_id, 1001)
        self.assertTrue(now - a.updated_at < timedelta(seconds=1))

    def test_save(self):
        import time
        a = DummyCS.create(ep_num=1)
        old_updated_at = a.updated_at

        time.sleep(1)
        a.ep_num = 10
        a.save()

        self.assertTrue(a.updated_at > old_updated_at)
        self.assertEqual(DummyCS.get_by(id=a.id).updated_at, a.updated_at)

# class TestCustomizedPrimaryKey(TestCase):
#     @orz_decorate('test_orz', sqlstore=store, mc=mc)
#     class Dummy(object):
#         subject_id = OrzField(as_key=OrzField.KeyType.ASC)
#         ep_num = OrzPrimaryField()

#     def setUp(self):

#     def tearDown(self):
#         mc.clear()

class Dummy(OrzBase):
    __orz_table__ = 'test_orz'

    subject_id = OrzField(as_key=OrzField.KeyType.ASC)
    ep_num = OrzField(as_key=OrzField.KeyType.ASC, default=0)
    content = OrzField(default='hello world')
    flag = OrzField(as_key=OrzField.KeyType.ASC, default=False)
    extra = OrzField(default=1)
    null_field = OrzField(default=None)
    output_field = OrzField(output_filter=str, default=10)
    callable_field = OrzField(default=lambda :10)

    class OrzMeta:
        id2str = True
        order_combs = (('-extra', 'ep_num'), )

    def before_create(self, extra_args=None):
        if self.subject_id == '-1':
            raise ValueError

        if self.subject_id == '-2':
            self.save()

        if self.subject_id == '-3':
            self.delete()

    def after_create(self, extra_args=None):
        self.after_created = True
        self.extra_args = extra_args

    def after_save(self):
        self.after_saved = True

    def before_delete(self):
        mc.set('before_delete_test', True)

    def after_delete(self):
        if self.subject_id=='10001':
            self.save()

        if self.subject_id=='10002':
            self.delete()

    @classmethod
    @orz_get_multi
    def get_non_targeted(cls, non_targeted_ep_num):
        return [i for i, in store.execute('select id from test_orz where ep_num!=%s', non_targeted_ep_num)]


