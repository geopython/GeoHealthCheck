# From: http://www.derstappen-it.de/tech-blog/sqlalchemie-alembic-check-if-table-has-column
# Extended with  get_table_names() and tables_exist() by JvdB
#
from alembic import op
from sqlalchemy import engine_from_config
from sqlalchemy.engine import reflection


# Get the SQLAlchemy Inspector from Engine
def get_inspector():
    config = op.get_context().config
    engine = engine_from_config(
        config.get_section(config.config_ini_section), prefix='sqlalchemy.')
    return reflection.Inspector.from_engine(engine)


# Get list of column names from table
def get_column_names(table):
    # get_columns: list of dicts with (column) 'name' entries
    columns = get_inspector().get_columns(table)
    return [column['name'] for column in columns]


# Check if table has column
def table_has_column(table, column_name):
    return column_name in get_column_names(table)


# Get list of table names from database
def get_table_names():
    return get_inspector().get_table_names()


# Check if list of table names in database
def tables_exist(tables):
    table_names = get_table_names()
    for table in tables:
        if table not in table_names:
            return False

    return True


# Get list of index names from table
def get_index_names(table):
    # get_indexes: list of dicts with (index) 'name' entries
    indexes = get_inspector().get_indexes(table)
    return [index['name'] for index in indexes]


# Check if table has named index
def table_has_index(table, index_name):
    return index_name in get_index_names(table)


# Create index on a table if not exists
def create_index(index_name, table, columns, unique=False):
    if table_has_index(table, index_name):
        return

    # Index does not exist: create
    op.create_index(op.f(index_name), table, columns, unique=unique)
