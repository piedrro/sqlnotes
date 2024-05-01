import sqlite3

# Connect to the database
conn = sqlite3.connect('example.db')
cursor = conn.cursor()

# Execute a query
cursor.execute('SELECT * FROM users')  # Assuming there is a table named 'users'

# Fetch and print the results
rows = cursor.fetchall()
for row in rows:
    print(row)  # Each 'row' is a tuple

# Close the connection
conn.close()