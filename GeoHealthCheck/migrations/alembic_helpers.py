# From: http://www.derstappen-it.de/tech-blog/sqlalchemie-alembic-check-if-table-has-column
# Extended with  get_table_names() and tables_exist() by JvdB
#
from alembic import op
from sqlalchemy import engine_from_config
from sqlalchemy.engine import reflection


# Check if table has column
def table_has_column(table, column):
    config = op.get_context().config
    engine = engine_from_config(
        config.get_section(config.config_ini_section), prefix='sqlalchemy.')
    insp = reflection.Inspector.from_engine(engine)
    has_column = False
    for col in insp.get_columns(table):
        if column not in col['name']:
            continue
        has_column = True
    return has_column


# Get list of table names from database
def get_table_names():
    config = op.get_context().config
    engine = engine_from_config(
        config.get_section(config.config_ini_section), prefix='sqlalchemy.')
    insp = reflection.Inspector.from_engine(engine)
    return insp.get_table_names()


# Check if list of table names in database
def tables_exist(tables):
    table_names = get_table_names()
    matches = 0
    for table in tables:
        if table in table_names:
            matches += 1

    return matches == len(tables)


