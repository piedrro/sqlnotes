from sqlalchemy import create_engine, Table, Column, Integer, MetaData, String, select, insert
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import inspect, update, and_
# https://towardsdatascience.com/sqlalchemy-python-tutorial-79a577141a91

Base = declarative_base()

class SQLiteWrapper:
    def __init__(self, db_file):
        """ Initialize the database connection using SQLAlchemy. """
        self.db_file = db_file
        self.engine = create_engine(f'sqlite:///{self.db_file}')
        self.Session = sessionmaker(bind=self.engine)
        self.metadata = MetaData(self.engine)
        self.tables = {}
        self.reflect_tables()

    def reflect_tables(self):
        """ Reflects the tables from the database into the metadata and stores them in self.tables. """
        try:
            self.metadata.reflect(self.engine)
            self.tables = {table_name: table for table_name, table in self.metadata.tables.items()}
            print("Tables loaded:", self.tables.keys())
        except SQLAlchemyError as e:
            print("Failed to reflect tables:", e)

    def get_table(self, table_name):
        """ Check if a table exists in the database and return it, otherwise return None."""
    
        inspector = inspect(self.engine)
        if table_name in inspector.get_table_names():
            return self.tables.get(table_name)
        else:
            return None


    def create_table_from_dict(self, table_name, data_dict):
        """ Automatically create a table based on the dictionary keys and inferred types using SQLAlchemy. """
        if table_name in self.metadata.tables:
            print(f"Table '{table_name}' already exists.")
            return

        columns = [Column('id', Integer, primary_key=True, autoincrement=True)]
        for key, value in data_dict.items():
            col_type = self.infer_sqlite_type(value)
            columns.append(Column(key, col_type))
        
        # Create the table
        self.tables[table_name] = Table(table_name, self.metadata, *columns)
        self.metadata.create_all()

    def infer_sqlite_type(self, value):
        """ Infer the SQLAlchemy type for a given Python value. """
        if isinstance(value, int):
            return Integer
        elif isinstance(value, float):
            return Float
        elif isinstance(value, str):
            return String
        elif isinstance(value, bytes):
            return LargeBinary
        else:
            return String  # Default catch-all as String

    def add_dict_row(self, table_name, data_dict):
        """ Insert a new row into the table from a dictionary. """
        table = self.tables.get(table_name)
        if not table:
            raise ValueError(f"Table {table_name} does not exist.")
        ins = insert(table).values(**data_dict)
        with self.engine.begin() as conn:  # automatically commit or rollback
            conn.execute(ins)

    def add_multiple_rows(self, table_name, dict_list):
        """ Insert multiple rows into the table efficiently using SQLAlchemy. """
        table = self.tables.get(table_name)
        if not table:
            raise ValueError(f"Table {table_name} does not exist.")
        ins = insert(table)
        with self.engine.begin() as conn:
            conn.execute(ins, dict_list)
            print(f"Inserted {len(dict_list)} rows into {table_name}")

    def fetch_data(self, table_name, columns='*', where_clause=None):
        """ Fetch data from the table using SQLAlchemy. """
        table = self.tables.get(table_name)
        if not table:
            raise ValueError(f"Table {table_name} does not exist.")
        
        query = select([table.c[col] for col in columns.split(', ') if col in table.c])
        if where_clause:
            query = query.where(text(where_clause))
        
        with self.engine.connect() as conn:
            result = conn.execute(query)
            return result.fetchall()

    def add_dataframe(self, table_name, dataframe):
        """ Insert a DataFrame into the database using to_sql method from Pandas. """
        try:
            dataframe.to_sql(table_name, self.engine, if_exists='append', index=False)
            print(f"Dataframe inserted into {table_name} successfully.")
        except Exception as e:
            print(e)

    def close_connection(self):
        """ Close the database connection if needed. """
        # With SQLAlchemy, connections are typically managed as context-managers, so explicit closes are often unnecessary.

    def update_row(self, table_name, identifiers, new_data):
        """
        Update specific columns of a row in the specified table.
        
        Args:
        table_name (str): The name of the table.
        identifiers (dict): Dictionary with column names and values to identify the row.
        new_data (dict): Dictionary with column names and values to update.
        """
        table = self.tables.get(table_name)
        if not table:
            raise ValueError(f"Table {table_name} does not exist.")
        
        # Build the WHERE clause based on identifiers
        conditions = [table.c[key] == value for key, value in identifiers.items()]
        condition = and_(*conditions)  # Combine all conditions with AND

        # Build the update statement
        update_stmt = update(table).where(condition).values(**new_data)
        
        with self.engine.begin() as conn:  # Use a transaction
            result = conn.execute(update_stmt)
            print(f"Updated {result.rowcount} rows in {table_name}")



# Example usage of the class
db = SQLiteWrapper('mydatabase.db')
example_data = {
    'name': 'Example Project',
    'begin_date': '2023-01-01',
    'end_date': '2024-01-01',
    'budget': 100000
}
db.create_table_from_dict('projects', example_data)
db.add_dict_row('projects', example_data)
data = db.fetch_data('projects')
print(data)


db = SQLiteWrapper('mydatabase.db')
identifiers = {'id': 1}  # Single ID for simplicity
new_data = {'name': 'Updated Project', 'budget': 200000}
db.update_row('projects', identifiers, new_data)