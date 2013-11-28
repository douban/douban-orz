import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "stub"))

from douban.mc import mc_from_config
from douban.mc.wrapper import LocalCached
from douban.sqlstore import store_from_config

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

MEMCACHED = {
    'servers' : [],
    'disabled' : False,
}

mc = LocalCached(mc_from_config(MEMCACHED))
store = store_from_config(DATABASE)
mc.clear()

initted = False
