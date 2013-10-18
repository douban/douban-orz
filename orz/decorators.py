# -*- coding:utf-8 -*-
from os.path import dirname, join
import sys
sys.path.append(join(dirname(__file__), ".."))

from .cache_mgr import cached_wrapper


def _deco(func):
    def __(table_name, *a, **kw):
        def _(cls):
            return func(cls, table_name, *a, **kw)
        return _
    return __

orz_decorate = _deco(cached_wrapper)

if __name__ == '__main__':
    pass
    # @cached_orm_decorate('complete_video')
    # class A(object):
    #     subject_id = OrzField()
    #     ep_num = OrzField()
    #     default_src = OrzField()

    # a = A.create(subject_id=10, ep_num=1, default_src=1)

