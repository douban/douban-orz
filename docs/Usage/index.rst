Usage
-----

set up
~~~~~~

ORZ
在使用Orz关联表之前，需要确保先使用基于douban.corelib.sqlstore和douban.corelib.mc派生的store和mc对ORZ进行配置。

::

    from ORZ import setup
    setup(your_store, your_mc)

与数据表的关联
~~~~~~~~~~~~~~

假定我们有简单表声明如下：

::

    CREATE TABLE `question` (
      `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
      `subject_id` int(11) unsigned NOT NULL,
      `title` varchar(1),
      `author_id` int(11) unsigned NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='';

根据这个表我们这样定义Model:

::

    # don't forget to setup
    from ORZ import OrzBase, Orz
    class Question(OrzBase):
        __orz_table__ = "question"
        title = OrzField()
        subject_id = OrzField()
        author_id = OrzField()

从上述定义里可知

-  每个类都是OrzBase的子类
-  ``__orz_table__`` 指定对应的table
-  每个 OrzField
   实例化对象对应数据表里字段，并且该类成员名字与数据表里保持一致

字段声明，索引，索引查询缓存
^^^^^^^^^^^^^^^^^^^^^^^^^^

基本用法
''''''''

上面的数据表, 我们增加一个查询的需求--查询用户，在条目下的问题，于是表增加

::

    KEY `author_subject_idx` (`author_id`, `subject_id`)

Model字段定义改为

``python subject_id = OrzField(as_key=OrzField.KeyType.IndexOnly) author_id = OrzField(as_key=OrzField.KeyType.IndexOnly)``
这样不仅按照需求实现的查询的Cache就能被管理了，而且是``subject_id``和``author_id``两者，或者之一为维度查询的Cache都能被管理了。也就说，当需求变更索引改为

``sql KEY `author_idx` (`author_id`), KEY `subject_idx` (`subject_id`)``
或者

``sql KEY `author_idx` (`author_id`)``
的时候，Model声明的字段也是满足需求的对应查询的缓存管理

接口使用
^^^^^^^^

按照上述Question Model的定义，接着介绍CRUD

Create
''''''

::

    ModelClass.create(**field_and_its_val)

-  根据字段定义，以 keyword argruments 的形式传入。
-  在唯一性约束的表里，参数和表内数据有重复，会直接抛出
   ``MySQLdb.IntegrityError``

例子:

::

    question = Question.create(subject_id=subject.id, author_id=user.id, title="hdadfasdf")

Read
''''

::

    ModelCLS.gets_by(order_by=order_keys, start=0, limit=EPISION, **condition)

-  condition 即 SQL where key = val
-  order\_by 默认为按 id 降序排列， 详细见[排序][]
-  默认取全部数据，也可以分页。

例子:

::

    questions = Question.gets_by(subject_id=subject.id)
    questions = Question.gets_by(subject_id=subject.id, author_id=user.id)
    questions = Question.gets_by(author_id=user.id)

亦可根据ID，查询单个对象

::

    question = Question.get_by(id=1)

-  现阶段 ``get_by`` 只接受 ``id`` 的查询

Update
''''''

::

    model_instance.save()

例子:

::

    question = Question.gets_by(subject_id=1)[0]
    question.title = "hello world"
    question.subject_id = 2
    ret = quesiton.save()

-  ret 为数据库操作的返回值

-  上面这个例子中 Question 所有和 subject\_id=1 以及 subject\_id=2
   的关联mc cache都会被清除

Delete
''''''

::

    ret = model_instance.delete()

-  ret 为数据库操作的返回值

例子:

::

    question = Question.gets_by(subject_id=1)[0]
    question.delete()

组合与扩展
^^^^^^^^^^

一般情况下你并不需要去 Override Create/Save/Delete 来做扩展，
ORZ提供了一个简单的Aspect-like的方式来更好的拆分逻辑。这些扩展的方法都是Instancemethod。

Creation Aspect
'''''''''''''''

::

    def before_create(self, **extra_args):
        pass

    def after_create(self, **extra_args):
        pass

-  ``extra_args`` 是调用 ``create`` 时传入的非 ``OrzField`` 定义的参数。
-  ``before_create`` 里，直接通过 ``self.attr`` 即可访问 ``OrzField``
   定义的参数。

Save Aspect
'''''''''''

::

    def before_save(self):
        pass

    def after_save(self):
        pass

Deletion Aspect
'''''''''''''''

::

    def before_delete(self):
        pass

    def after_delete(self):
        pass

Warning
'''''''

``before_create`` 和 ``after_delete`` 的时候， instance 都是处于
``detached_state``--无法再调用``delete``, ``save`` 。

排序
^^^^

简单的排序
''''''''''

由于在定义数据库的时候，用于排序的Field都会被定义为索引(的一部分),
同时我发现我们在实际操作中一般，都只有一个方向的排序，所以基于这个语义
``OrzField`` 提供了一个便捷的方式来处理定义以便管理缓存

``python subject_id = OrzField(as_key=OrzField.KeyType.X)``
- X = DESC subject\_id 可能会作为查询条件， 同时以*只以subject\_id降序*可能会作为查询集合*单独*排序条件
- X = ASC subject\_id 可能会作为查询条件， 同时以*只以subject\_id升序*可能会作为查询集合*单独*排序条件
- X = AD subject\_id 可能会作为查询条件， 同时以*subject\_id升序或者降序*都可能会作为查询集合*单独*排序条件

例子:
``python # 假如上述例子里X为 DESC questions = Question.gets_by(author_id=user.id, order_by='-subject_id')``

复杂的排序
''''''''''

假如需要的查询是类似 ``sql`` 里 ``order by key1 desc, key2``，或者定义的
``OrzField`` 并作为查询条件，那么可以在OrzModel里定义一个 Nested Class -
``OrzMeta``

::

    class OrzMeta:
        order_combs = (('-key1', 'key2'), ('key3'，), ...)

-  order\_combs 是
   ``tuple``，``tuple``里每个元素都是一个排序组合的``tuple``。排序的字段用字符串表示，降序在字段前加"-"作为前缀。

缓存管理和SQL的一些细节
^^^^^^^^^^^^^^^^^^^^^^^

OrzField 以及 order\_combs
看起来像是Database的映射，其实是以一种显式声明的方式，作为缓存管理的一部分。

-  OrzField.KeyType.X 都是为缓存服务的。这个从本质来讲和SQL
   Index没有任何关系，但是从代码最佳实践的角度来说，频繁被访问的数据更加值得缓存，频繁被访问的查询都应该有索引支撑。(这也是ORZ安身立命的支点
   XD)。
-  KeyType.AD\|DESC\|ASC 和 order\_combs
   同样和数据库没有直接关系，只是基于这个Model排序策略的缓存管理声明
-  Orz缓存管理由于和SQL没有关系，所以你可以用ORZ缓存一个没有优化的查询。。。与之相对的，如果你使用ORZ的查询没有声明的缓存管理，那么这个查询是不会进入缓存的，但仍能获得查询集以及一个Warning。。

默认值处理
^^^^^^^^^^

SQL的默认值
'''''''''''

先看定义和Model定义

::

    `title` varchar(10) DEFAULT 'hello'
    `created_at` timestamp NOT NULL DEFAULT '2010-10-10 10:10:10',
    `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP

::

    class Question(OrzModel):
        __orz_table__="question"
        updated_at = OrzField()
        created_at = OrzField()
        title = OrzField()

那么 ``q = Question.create()`` 里 ``q.updated_at`` 等于当前时间,
``q.created_at`` 等于
``datetime(year=2010, month=10, day=10, hour=10, minute=10, sencond=10)``
, ``q.title`` 等于 ``'hello'``

更进一步

``python q = Question.create() q.title = "world" q.save()`` 那么
``q.updated_at`` 变更为调用save那个时间点

换句话说，Orz会把SQL产生的结果更新到instance上。

Orz's defaults on creation
''''''''''''''''''''''''''

除了SQL自身的默认值， ORZ也提供了创建在创建对象时候的默认值

::

    OrzField(default=default_val)

-  default\_val 可以是一个值或者一个不接受任何参数的函数。

