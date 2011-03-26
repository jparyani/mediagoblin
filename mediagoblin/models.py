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

    required_fields = [
        'title', 'created',
        'media_type', 'file_store']

    default_values = {
        'created': datetime.datetime.utcnow}
    

class User(Document):
    structure = {
        'username': unicode,
        'created': datetime.datetime,
        'plugin_data': dict, # plugins can dump stuff here.
        'pw_hash': unicode,
        }

    required_fields = ['username', 'created', 'pw_hash']

    default_values = {
        'created': datetime.datetime.utcnow}


REGISTER_MODELS = [MediaEntry, User]


def register_models(connection):
    """
    Register all models in REGISTER_MODELS with this connection.
    """
    connection.register(REGISTER_MODELS)

