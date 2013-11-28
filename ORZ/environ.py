orz_mc = None
orz_sqlstore = None

def setup(sqlstore, mc):
    global orz_mc, orz_sqlstore

    orz_mc = mc
    orz_sqlstore = sqlstore
