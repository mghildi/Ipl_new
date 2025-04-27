import duckdb
import pandas as pd

# Read the IPL CSV file
df = pd.read_csv('ipl_data.csv')  # 🛠 Make sure ipl_data.csv exists in the folder

# Connect to DuckDB (creates ipl.duckdb if not exist)
connection = duckdb.connect('ipl.duckdb')

# Create a cursor
cursor = connection.cursor()

# Create a table from the CSV data
cursor.execute("""
CREATE TABLE IF NOT EXISTS ipl AS 
SELECT * FROM df
""")

# Display sample records
print("Sample data from the ipl table:")
data = cursor.execute("SELECT * FROM ipl LIMIT 5").fetchall()
for row in data:
    print(row)

# Close the connection
connection.commit()
connection.close()

print("\n✅ Database created and populated successfully with IPL data!")