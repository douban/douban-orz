from operator import itemgetter
from itertools import chain
from copy import deepcopy


class SqlExecutor(object):
    def __init__(self, table_name, primary_field_name, db_fields, sqlstore):
        self.sqlstore = sqlstore
        self.conditions = {}
        self.primary_field_name = primary_field_name
        self.db_fields = db_fields
        self.table_name = table_name
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

    def update_row(self, primary_field, field_data, transational=False):
        set_sql, v = self._sql_statement('SET',
                                      [("%s=%%s" % kv[0], kv[1]) for kv in field_data.items()],
                                      ',')
        statement = "update %s %s where %s = %s" % (self.table_name, set_sql, self.primary_field_name, primary_field)
        ret = self.sqlstore.execute(statement, tuple(v))
        if not transational:
            self.sqlstore.commit()
        return ret

    def delete(self, primary_field, transational=False):
        statement = 'delete from %s where %s = %%s' % (self.table_name, self.primary_field_name)
        ret = self.sqlstore.execute(statement, primary_field)
        self.sqlstore.commit()
        if not transational:
            self.sqlstore.commit()
        return ret

    def _transform_order_keys(self, keys):
        def __(key):
            if key.startswith('-'):
                key = (key[1:], 'desc')
            else:
                key = (key, 'asc')
            return key
        return [__(key) for key in keys]

    def get_ids(self, conditions, start_limit, order_keys=tuple()):
        limit_sql, v3 = self._sql_statement('limit', zip(["%s", "%s"], start_limit))
        if not order_keys:
            order_sql = ''
        else:
            order_sql = 'order by %s' % ",".join("%s %s" % (k, v) for k, v in self._transform_order_keys(order_keys))
        where_sql, v1 = self._sql_statement('where',
                                        [("%s=%%s" % k, v) for k, v in conditions.iteritems()],
                                        ' and ')

        statement = "select %s from %s %s %s %s" % \
                        (self.primary_field_name, self.table_name, where_sql, order_sql, limit_sql)
        ids = map(itemgetter(0), self.sqlstore.execute(statement, tuple(chain(v1, v3))))
        return ids

    def get(self, primary_field):
            #BIG TODO for non exist obj
        fields = [self.primary_field_name] + list(self.db_fields)
        statement = "select %s from %s where %s=%%s" % (",".join(fields), self.table_name, self.primary_field_name, )
        ret = self.sqlstore.execute(statement, primary_field)
        if not ret:
            return None
        return dict(zip(fields+['to_create'], list(ret[0])+[False]))

    def _sql_statement(self, keyword, fields, concat_by=','):
        if len(fields) == 0:
            return "", ()
        prefix, values = zip(*fields)
        return keyword + " " + (concat_by.join(prefix)), values

    def calc_count(self, conditions):
        sql, vals = self._sql_statement('where',
                                  [("%s=%%s" % k, v) for k, v in conditions.iteritems()],
                                  ' and ')
        statement = "select count(1) from %s %s" %  (self.table_name, sql)
        ret = self.sqlstore.execute(statement, vals)
        return ret[0][0]

