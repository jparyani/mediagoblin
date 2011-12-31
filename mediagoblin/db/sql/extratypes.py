from sqlalchemy.types import TypeDecorator, Unicode


class PathTupleWithSlashes(TypeDecorator):
    "Represents a Tuple of strings as a slash separated string."

    impl = Unicode

    def process_bind_param(self, value, dialect):
        if value is not None:
            assert len(value), "Does not support empty lists"
            value = '/'.join(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = tuple(value.split('/'))
        return value
