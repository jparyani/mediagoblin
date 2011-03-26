from mongokit import Document, Set
import datetime


class MediaEntry(Document):
    structure = {
        'title': unicode,
        'created': datetime.datetime,
        'description': unicode,
        'media_type': unicode,
        'media_data': dict, # extra data relevant to this media_type
        'plugin_data': dict, # plugins can dump stuff here.
        'file_store': unicode,
        'tags': Set(unicode)}


class User(Document):
    structure = {
        'username': unicode,
        'created': datetime.datetime,
        'plugin_data': dict, # plugins can dump stuff here.
        'pw_hash': unicode,
        }


REGISTER_MODELS = [MediaEntry, User]

def register_models(connection):
    """
    Register all models in REGISTER_MODELS with this connection.
    """
    connection.register(REGISTER_MODELS)

