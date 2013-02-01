""" This module contains functions required for "sharding". 
Code is taken from http://code.google.com/appengine/articles/sharding_counters.html. See website
for details """

from google.appengine.api import memcache
from google.appengine.ext import ndb
import random

class GeneralCounterShardConfig(ndb.Model):
    """Tracks the number of shards for each named counter."""
    name = ndb.StringProperty(required=True)
    num_shards = ndb.IntegerProperty(default=10)


class GeneralCounterShard(ndb.Model):
    """Shards for each named counter"""
    name = ndb.StringProperty(required=True)
    count = ndb.IntegerProperty(default=0)


def get_count(name):
    """Retrieve the value for a given sharded counter.

    Parameters:
      name - The name of the counter
    """
    total = memcache.get(name)
    if total is None:
        total = 0
        for counter in GeneralCounterShard.query().filter(GeneralCounterShard.name == name):
            total += counter.count
        memcache.add(name, str(total), 60)
    return total


def increment(name):
    """Increment the value for a given sharded counter.

    Parameters:
      name - The name of the counter
    """
    config = GeneralCounterShardConfig.get_or_insert(name, name=name)
    def txn():
        index = random.randint(0, config.num_shards - 1)
        shard_name = name + str(index)
        counter = GeneralCounterShard.get_by_id(shard_name)
        if counter is None:
            counter = GeneralCounterShard(id=shard_name, name=name)
        counter.count += 1
        counter.put()
    ndb.transaction(lambda: txn())
    memcache.incr(name)


def increase_shards(name, num):
    """Increase the number of shards for a given sharded counter.
    Will never decrease the number of shards.

    Parameters:
      name - The name of the counter
      num - How many shards to use

    """
    config = GeneralCounterShardConfig.get_or_insert(name, name=name)
    def txn():
        if config.num_shards < num:
            config.num_shards = num
            config.put()
    ndb.transaction(lambda: txn)
