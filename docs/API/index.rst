Full API
============

Transaction
^^^^^^^^^^^

ORZ封装了一个便捷的事务处理

::

    with start_transaction(orz_instance, OrzModelCLS) as transactional_orz_instance, transactional_orz_cls:
        transactional_orz_instance.save()
        transactional_orz_cls.create(**kwargs)

-  在这个transaction的context里，抛出``IntegrityError``或者``OrzForceRollBack``都会Rollback
-  另外，由于现在实现上的问题， 其实orz\_instance,
   OrzModelCLS也是发生修改了的。。。


OrzField
''''''''

OrzField(as\_key=OrzField.KeyType.NOT\_INDEX, default=handler, output\_filter=lambda x:x)


as\_key
    有4种默认值

    -  KeyType.NOT\_INDEX: 默认值。顾名思义
    -  KeyType.DESC: 该字段可能会作为查询条件，
       同时以*只以subject\_id降序*可能会作为查询集合*单独*排序条件
    -  KeyType.ASC: 该字段可能会作为查询条件，
       同时以*只以subject\_id升序*可能会作为查询集合*单独*排序条件
    -  KeyType.AD: 该字段可能会作为查询条件，
       同时以*subject\_id升序或者降序*都可能会作为查询集合*单独*排序条件
    -  KeyType.ONLY\_INDEX: 该字段仅仅可能会作为查询条件

default
    值或者一个没有参数函数

output\_filter
    把字段从MC或者DB里取出以后，再转一次。。

OrzMeta
'''''''

::

    class OrzMeta:
        order_combs = (,)
        id2str = False
        cache_ver = ''

order\_combs
    排序条件的组合

id2str
    Shire里都有个不成文的Convention，都会把id或者\_id结尾的字段转换为字符串

cache\_ver
    缓存的版本

