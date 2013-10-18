The Missing Data Manager In Shire
===========================================

这是什么？
----------------------------------------

封装了基础的数据库CRUD和Cache管理的数据层，并提供基于method-combination的方式进行扩展操作

In a nutshell
--------------------------

假如数据库声明是这样的

::

    CREATE TABLE `dummy_yummy` (
      `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
      `uid` int(11),
      `username` varchar(20) NOT NULL,
      `subject_id` int(11) NOT NULL,
      `user_id` int(11) NOT NULL,
      `subtype` varchar(50),
      PRIMARY KEY (`id`),
      KEY `user_id` (`user_id`),
      KEY `subject_id_subtype_idx` (`subject_id`, `subtype`),
      KEY `uid` (`uid`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='';

之前我们会这样写

::

    class DummyYummy(object):
        OBJ_CACHE = 'dummyyummy-obj:%s'
        USER_INDEX_CACHE = 'dummyyummy-user:%s'
        SUBJECT_SUBTYPE_INDEX_CACHE = 'dummyyummy-subject:%s|subtype:%s'
        UID_INDEX_CACHE = 'dummyyummy-uid:%s'

        def __init__(self, id, uid, username, subject_id, user_id, subtype):
            self.id = id
            self.uid = uid
            self.username = username
            self.subject_id = subject_id
            self.user_id = user_id
            self.subtype = subtype


        @classmethod
        def create(cls, uid, username, subject_id, user_id, subtype):
            id = store.exexute('insert into dummy_yummy (`uid`, `username`, `subject_id`, `user_id`, `subtype`)'
                               'values (%s, %s, %s, %s, %s)', (uid, username, subject_id, user_id, subtype))
            store.commit()

            mc.delete(cls.SUBJECT_SUBTYPE_INDEX_CACHE % (subject_id, subtype))
            mc.delete(cls.UID_INDEX_CACHE % uid)
            mc.delete(cls.USER_INDEX_CACHE % user_id)

            ins = cls(id, uid, username, subject_id, user_id, subtype)
            mc.set(cls.OBJ_CACHE % ins.id, ind)
            return ins

        def update_subject_id(self, subject_id):
            store.execute('update dummy_yummy set subject_id=%s where id=%s', (subject_id, self.id))
            store.commit()

            mc.delete(self.SUBJECT_SUBTYPE_INDEX_CACHE % (self.subject_id, self.subtype))

            self.subject_id = subject_id

            mc.delete(self.SUBJECT_SUBTYPE_INDEX_CACHE % (subject_id, self.subtype))
            mc.delete(self.OBJ_CACHE % self.id)

        @classmethod
        def gets(cls, ids):
            mc.get_multi(ids)
            return [cls.get(id=id) for id in ids]


        @cache(USER_INDEX_CACHE % "{user_id}")
        def _gets_by_user_id(cls, user_id):
            return [id for id, in store.execute("select id from dummy_yummy where user_id = %s", user_id)]

        def gets_by_user_id(cls, user_id):
            return cls.gets(cls._gets_by_user_id(user))

        @cache(SUBJECT_SUBTYPE_INDEX_CACHE % ("{subject_id}", "{subtype}"))
        def _gets_by_subject_id_and_subtype(cls, subject_id, subtype):
            return [id for id, in store.execute("select id from dummy_yummy where subject_id = %s and subtype = %s", (subject_id, subtype))]

        def gets_by_subject_id_and_subtype(cls, subject_id, subtype):
            return cls.gets(cls._gets_by_subject_id_and_subtype(cls, subject_id, subtype))

        @cache(UID_INDEX_CACHE % "{uid}")
        def _gets_by_uid(cls, uid):
            return [id for id, in store.execute("select id from dummy_yummy where uid = %s", uid)]

        def gets_by_uid(cls, uid):
            return cls.gets(cls._gets_by_uid(cls, uid))


现在我们这样写

::

    @orz_decorate("dummy_yummy")
    class DummyYummy(object):
        uid = OrzField(as_key=OrzField.KeyType.DESC)
        username = OrzField()
        subject_id = OrzField(as_key=OrzField.KeyType.DESC)
        user_id = OrzField(as_key=OrzField.KeyType.DESC)
        subtype = OrzField(as_key=OrzField.KeyType.DESC)

用法上

::

    #old
    Dummy.gets_by_subject_id_and_subtype(subject_id, subtype):
    Dummy.gets_by_uid(uid)
    Dummy.gets_by_user_id(user_id)


    dummy_obj = Dummy.create(uid=uid, subject_id=subject_id, subtype=subtype, user_id=user_id, username=username)

    dummy_obj.update_subject_id(subject_id=subject_id)

    #new
    Dummy.gets_by(uid=uid)
    Dummy.gets_by(subject_id=subject_id, subtype=subtype)
    Dummy.gets_by(user_id=user_id)

    dummy_obj = Dummy.create(uid=uid, subject_id=subject_id, subtype=subtype, user_id=user_id, username=username)

    dummy_obj.subject_id = subject_id
    dummy_obj.save()

可以看出:

    0. 构建上高度抽象，显式声明

    1. 使用上语义一致，语法不再罗嗦


用法:
---------

1. 声明使用的表:

::

    @orz_decorate("dummy_yummy")
    class DummyYummy(object):

2. 除了ID以外，声明和数据一一对应同名的字段

::

    '''
      `uid` int(11),
      `username` varchar(20) NOT NULL,
      `subject_id` int(11) NOT NULL,
      `user_id` int(11) NOT NULL,
      `subtype` varchar(50),
    '''
    @orz_decorate("dummy_yummy")
    class DummyYummy(object):
        uid = OrzField()
        username = OrzField()
        subject_id = OrzField()
        user_id = OrzField()
        subtype = OrzField()

3. 标注需要作为查询的字段

::

    '''
      KEY `user_id` (`user_id`),
      KEY `subject_id_subtype_idx` (`subject_id`, `subtype`),
      KEY `uid` (`uid`)
    '''
    @orz_decorate("dummy_yummy")
    class DummyYummy(object):
        uid = OrzField(as_key=True)
        username = OrzField()
        subject_id = OrzField(as_key=True)
        user_id = OrzField(as_key=True)
        subtype = OrzField(as_key=True)

*Note*

    0. ID 是无需声明的，即任何一个Model都自带, 降序排列

    ::
        id = OrzField(as_key=OrzField.KeyType.DESC)

    1. 无需考虑数据库索引声明里的字段顺序


4. 查询

获取查询的集合

::
    Dummy.gets_by(uid=uid)
    Dummy.gets_by(subject_id=subject_id, subtype=subtype)
    Dummy.gets_by(user_id=user_id)
    Dummy.gets_by(id=id)

通过ID获取单个OBJ

::
    Dummy.get_by(id=id)

排序的声明和使用

::
    # user_id 升序
    # 声明
    user_id = OrzField(as_key=OrzField.KeyType.ASC)

    # 使用
    Dummy.gets_by(uid=uid, order_by='user_id')

    # user_id 降序
    # 声明
    user_id = OrzField(as_key=OrzField.KeyType.DESC)

    # 使用
    Dummy.gets_by(uid=uid, order_by='-user_id')

*Note*

    所有的声明为查询字段的Key都默认作为排序的Key，支持升序,降序以及升降序的缓存管理.

分页

::

    qrset = Dummy.gets_by(uid=uid, start=10, limit=30)


5. Create, Delete, Update(Save)
    数据的创建，删除，更新都是容易的。需要扩展三种操作的时候，基于method-combination的"before\_", "after\_"的方式来做

Update(Save):

::

    #一般情况
    dummy_obj.username = username
    dummy_obj.save()

    #before/after_save, (省略无关代码)
    class DummYummy(PropsMixin):
        data = PropsItem()
        def before_save(self):
            self.subtype = self.subtype if Data else "2222"

        def after_save(self):
            get_subject(self.subject_id).update_sth()

Create:

::
    dummy_obj = Dummy.create(uid=uid, subject_id=subject_id, subtype=subtype, user_id=user_id, username=username)

Delete:

::
    dummy_obj.delete()

*Note*

    只有before_delete, 没有after_delete

..
