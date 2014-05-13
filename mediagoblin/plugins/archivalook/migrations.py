from mediagoblin.db.migration_tools import RegisterMigration, inspect_table
from sqlalchemy import MetaData, Table, Column, Integer
MIGRATIONS = {}

@RegisterMigration(1, MIGRATIONS)
def add_order_column(db):
    metadata = MetaData(bind=db.bind)

    featured_media = inspect_table(metadata, "archivalook__featured_media")
    col = Column("order", Integer, default=0)

    col.create(featured_media)

    db.commit()
