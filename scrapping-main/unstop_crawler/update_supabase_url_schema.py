import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

HOST = "db.rxdloipxqvjldsftitcn.supabase.co"
PORT = "5432"
DBNAME = "postgres"
USER = "postgres"
PASSWORD = os.getenv("SUPABASE_PASSWORD")

print("Connecting to Supabase...")
connection = psycopg2.connect(
    user=USER,
    password=PASSWORD,
    host=HOST,
    port=PORT,
    dbname=DBNAME
)
cursor = connection.cursor()
print("Connected!")

try:
    # Alter URL column to support longer URLs
    print("Updating url column to VARCHAR(500)...")
    cursor.execute("ALTER TABLE Unstop ALTER COLUMN url TYPE VARCHAR(500);")
    
    # Alter official_website column
    print("Updating official_website column to TEXT...")
    cursor.execute("ALTER TABLE Unstop ALTER COLUMN official_website TYPE TEXT;")
    
    connection.commit()
    print("✓ Schema updated successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    connection.rollback()
finally:
    cursor.close()
    connection.close()
