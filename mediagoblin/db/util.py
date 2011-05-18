import mongokit
from pymongo import DESCENDING
from mongokit import ObjectId


def connect_database(app_config):
    """Connect to the main database, take config from app_config"""
    port = app_config.get('db_port')
    if port:
        port = asint(port)
    connection = mongokit.Connection(
        app_config.get('db_host'), port)
    return connection
