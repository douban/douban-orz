from operator import itemgetter
from itertools import chain
from copy import deepcopy


class SqlExecutor(object):
    def __init__(self, mgr, table_name, db_fields, sqlstore):
        self.sqlstore = sqlstore
        self.mgr = mgr
        self.conditions = {}
        self.db_fields = db_fields
        self.table_name = table_name
        self.start_limit = ()
        self.order_key = (('id', 'desc'),)
        self.org_order_key = ('-id', )
        #self.dirty_fields = set()

    def create(self, field_data, transational=False):
        set_sql, v = self._sql_statement('SET',
                                      [("%s=%%s" % kv[0], kv[1]) for kv in field_data.items()],
                                      ',')
        statement = "insert into %s %s" % (self.table_name, set_sql)
        _id = self.sqlstore.execute(statement, v)
        if not transational:
            self.sqlstore.commit()
        return _id

    def update_row(self, id, field_data, transational=False):
        set_sql, v = self._sql_statement('SET',
                                      [("%s=%%s" % kv[0], kv[1]) for kv in field_data.items()],
                                      ',')
        statement = "update %s %s where id = %s" % (self.table_name, set_sql, id)
        ret = self.sqlstore.execute(statement, tuple(v))
        if not transational:
            self.sqlstore.commit()
        return ret

    def delete(self, id, transational=False):
        statement = 'delete from %s where id = %%s' % self.table_name
        ret = self.sqlstore.execute(statement, id)
        if not transational:
            self.sqlstore.commit()
        return ret

    def _clone(self):
        cloned = self.__class__(self.mgr, self.table_name, self.db_fields, self.sqlstore)
        cloned.conditions.update(self.conditions)
        cloned.start_limit = self.start_limit
        return cloned

    def filter(self, **kwargs):
        new = self._clone()
        new.conditions.update(kwargs)
        return new

    def get_order_by(self):
        return self.org_order_key

    def order_by(self, keys):
        self.org_order_key = keys
        def transform(key):
            if key.startswith('-'):
                key = (key[1:], 'desc')
            else:
                key = (key, 'asc')
            return key
        self.order_key = map(transform, keys)
        return self

    def get_ids(self):
        limit_sql, v3 = self._sql_statement('limit', zip(["%s", "%s"], self.start_limit))
        order_sql = "" if not self.order_key else ('order by %s' % ",".join("%s %s" % (k, v) for k, v in self.order_key))
        where_sql, v1 = self._sql_statement('where',
                                        [("%s=%%s" % k, v) for k, v in self.conditions.iteritems()],
                                        ' and ')

        statement = "select id from %s %s %s %s" % \
                        (self.table_name, where_sql, order_sql, limit_sql)
        ids = map(itemgetter(0), self.sqlstore.execute(statement, tuple(chain(v1, v3))))
        return ids

    def __getitem__(self, key):
        if key.stop is None:
            raise KeyError("the stop can't be None")
        start = 0 if key.start is None else key.start
        limit = key.stop - start
        self.start_limit = (start, limit)
        return self

    def limit(self, start, limit):
        self.start_limit = (start, limit)
        return self

    def get(self, id):
            #BIG TODO for non exist obj
        fields = ['id'] + list(self.db_fields)
        statement = "select %s from %s where id=%%s" % (",".join(fields), self.table_name)
        ret = self.sqlstore.execute(statement, id)
        if not ret:
            return None
        return dict(zip(fields+['to_create'], list(ret[0])+[False]))

    def _sql_statement(self, keyword, fields, concat_by=','):
        if len(fields) == 0:
            return "", ()
        prefix, values = zip(*fields)
        return keyword + " " + (concat_by.join(prefix)), values

    def calc_count(self):
        sql, vals = self._sql_statement('where',
                                  [("%s=%%s" % k, v) for k, v in self.conditions.iteritems()],
                                  ' and ')
        statement = "select count(1) from %s %s" %  (self.table_name, sql)
        ret = self.sqlstore.execute(statement, vals)
        return ret[0][0]

    def fetch(self, flush):
        return self.mgr.fetch(self, flush)

    def count(self):
        return self.mgr.count(self)


    # def flush_cache(self, obj, fields):
    #     if fields:
    #         mc.delete(self.ck_pattern_for_one_obj % obj.id)
    #         dirty = filter(lambda x: any([f in x for f in fields]), self.mcks)
    #         cks = map(self._get_ck_patterns_for_ids,
    #                        [dict((k, getattr(obj, k)) for k in keys) for keys in dirty])
    #         cks = map(self._get_ck_patterns_for_ids,
    #                        [dict((k, getattr(obj, 'hidden____org_' + k)) for k in keys) for keys in dirty])

    #         mc.delete_multi(cks)

    # def _get_ck_patterns_for_ids(self, condition):
    #     cond_str = ''.join(['%s=%s' % (k, condition[k]) for k in sorted(condition.keys())])
    #     return self.ck_pattern_for_ids % (cond_str.replace(" ", ""))
