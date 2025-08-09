from app_minimal import get_db_connection

try:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = c.fetchall()
    print("Database connection successful!")
    print("Tables:", tables)
    conn.close()
except Exception as e:
    print("Database connection failed:", e)
