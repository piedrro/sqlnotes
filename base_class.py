import sqlite3
from sqlite3 import Error
import pandas as pd
from sqlalchemy import create_engine

class SQLiteWrapper:
    def __init__(self, db_file):
        """ Initialize the database connection. """
        self.db_file = db_file
        self.conn = None
        self.engine = create_engine(f'sqlite:///{self.db_file}')  # SQLAlchemy engine
        self.connect_to_db()

    def connect_to_db(self):
        """ Create a database connection to a SQLite database. """
        try:
            self.conn = sqlite3.connect(self.db_file)
            print(f"SQLite connection is established: {self.db_file}")
        except Error as e:
            print(e)

    def create_table(self, create_table_sql):
        """ Create a table from the create_table_sql statement. """
        try:
            c = self.conn.cursor()
            c.execute(create_table_sql)
        except Error as e:
            print(e)

    def get_table_columns(self, table_name):
        """ Retrieve column names from the specified table. """
        try:
            c = self.conn.cursor()
            c.execute(f"PRAGMA table_info({table_name})")
            return [column[1] for column in c.fetchall()]
        except Error as e:
            print(e)

    def infer_sqlite_type(self, value):
        """ Infer the SQLite type for a given Python value. """
        if isinstance(value, int):
            return 'INTEGER'
        elif isinstance(value, float):
            return 'REAL'
        elif isinstance(value, str):
            return 'TEXT'
        elif isinstance(value, bytes):
            return 'BLOB'
        else:
            return 'TEXT'  # Default catch-all as TEXT

    def create_table_from_dict(self, table_name, data_dict):
        """ Automatically create a table based on the dictionary keys and inferred types. """
        columns = []
        for key, value in data_dict.items():
            sql_type = self.infer_sqlite_type(value)
            columns.append(f"{key} {sql_type}")
        columns_str = ', '.join(columns)
        sql_create_table = f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, {columns_str})"
        try:
            c = self.conn.cursor()
            c.execute(sql_create_table)
        except Error as e:
            print(e)

    def add_dict_row(self, table_name, data_dict):
        """ Insert a new row into the table from a dictionary after cleaning it. """
        columns = self.get_table_columns(table_name)
        # Filter dict to contain only keys that match the table columns
        filtered_data = {key: data_dict[key] for key in data_dict if key in columns}
        columns_str = ', '.join(filtered_data.keys())
        placeholders = ', '.join('?' * len(filtered_data))
        sql = f'INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})'
        try:
            c = self.conn.cursor()
            c.execute(sql, tuple(filtered_data.values()))
            self.conn.commit()
            return c.lastrowid
        except Error as e:
            print(e)

    def add_multiple_rows(self, table_name, dict_list):

        """ Insert multiple rows into the table efficiently. """
        if not dict_list:
            return
        
        keys = dict_list[0].keys()
        columns = ', '.join(keys)
        placeholders = ', '.join('?' * len(keys))
        sql = f'INSERT INTO {table_name} ({columns}) VALUES ({placeholders})'
        
        try:
            c = self.conn.cursor()
            c.execute('BEGIN')  # Begin transaction
            for data_dict in dict_list:
                c.execute(sql, tuple(data_dict[key] for key in keys))
            self.conn.commit()  # Commit all at once
            print(f"Inserted {len(dict_list)} rows into {table_name}")
        except Error as e:
            print(e)
            self.conn.rollback()  # Rollback if there is any error

    def fetch_data(self, table_name, columns='*', where_clause=None):
        """ Fetch data from the table, with optional WHERE clause. """
        sql = f'SELECT {columns} FROM {table_name}'
        if where_clause:
            sql += f' WHERE {where_clause}'
        try:
            c = self.conn.cursor()
            c.execute(sql)
            return c.fetchall()  # Return all rows of the query result
        except Error as e:
            print(e)

    def add_dataframe(self, table_name, dataframe):
        """ Insert a DataFrame into the database using to_sql method from Pandas. """
        try:
            dataframe.to_sql(table_name, self.engine, if_exists='append', index=False)
            print(f"Dataframe inserted into {table_name} successfully.")
        except Exception as e:
            print(e)

    def close_connection(self):
        """ Close the database connection. """
        if self.conn:
            self.conn.close()
            print("Connection closed.")

# Usage example

# Define the database
db = SQLiteWrapper('mydatabase.db')

# Define data as a dictionary
project_data = {
    'name': 'Cool Project',
    'begin_date': '2021-01-01',
    'end_date': '2022-01-01',
    'budget': 50000.00
}

# Automatically create a table based on dictionary data
db.create_table_from_dict('projects', project_data)

# Insert data
project_id = db.add_dict_row('projects', project_data)

# Close connection
db.close_connection()
