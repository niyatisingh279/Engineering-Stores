import sqlite3


DB_PATH = "engineering_store.db"


conn = sqlite3.connect(DB_PATH)

cursor = conn.cursor()



# ==========================================================
# STOCK TABLE
# ==========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS stock
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    location_barcode TEXT,

    item_name TEXT,

    quantity INTEGER,

    minimum_stock INTEGER
)
""")



# ==========================================================
# TRANSACTION HISTORY
# ==========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    location_barcode TEXT,

    item_name TEXT,

    transaction_type TEXT,

    quantity INTEGER,

    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")


conn.commit()

conn.close()


print("Engineering Store Database Created")