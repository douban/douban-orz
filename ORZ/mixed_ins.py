# -*- coding:utf8 -*-

def create(cls, **kwargs):
    ins = cls.objects.create(kwargs)
    return ins


def delete(self):
    self.objects.delete(self)
    # statement = 'delete from %s where id = %%s' % table_name
    # store.execute(statement, self.id)
    # store.commit()
    # self.objects.flush_cache(self, set(chain(*extra.get('keys', []))))


def save(self):
    self.objects.save(self)


def getstate(self):
    ret = {'dict': self.__dict__.copy(), 'db_fields': {}}

    for i in self.db_fields:
        ret['db_fields'][i] = getattr(self, i)

    return ret


def setstate(self, state):
    self.__dict__.update(state['dict'])
    self._initted = False
    for i in self.db_fields:
        setattr(self, i, state['db_fields'][i])
    self._initted = True


def init(self, to_create=True, *a, **kw):
    self.to_create = to_create
    self._initted = False
    self.dirty_fields = set()
    for i in self.db_fields:
        prev_val = kw.pop(i)
        val = self.id_casting(prev_val) if (i=='id' or i.endswith('_id')) and prev_val is not None else prev_val
        setattr(self, i, val)
    self._initted = True
