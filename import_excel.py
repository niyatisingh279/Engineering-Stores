import sqlite3
import openpyxl
import os
import shutil
from datetime import datetime


# =====================================================
# PATHS
# =====================================================

DB_PATH = "engineering_store.db"

EXCEL_FILE = "Engineering_stores_stock.xlsx"



print("Database:", DB_PATH)
print("Excel:", EXCEL_FILE)



# =====================================================
# BACKUP DATABASE BEFORE CHANGING IT
# =====================================================

if os.path.exists(DB_PATH):

    backup_name = (
        DB_PATH
        + ".backup_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
    )

    shutil.copy(DB_PATH, backup_name)

    print("Backup created:", backup_name)



# =====================================================
# CONNECT DATABASE
# =====================================================

conn = sqlite3.connect(DB_PATH)

cursor = conn.cursor()



# =====================================================
# OPEN EXCEL
# =====================================================

wb = openpyxl.load_workbook(
    EXCEL_FILE,
    data_only=True
)


print("\nSheets found:")

for s in wb.sheetnames:
    print("-", s)



# Take first sheet

ws = wb.active



# =====================================================
# READ HEADERS
# =====================================================

headers = {}

for cell in ws[1]:

    if cell.value:

        headers[
            str(cell.value).strip()
        ] = cell.column



print("\nHeaders detected:")

for h in headers:
    print(h)



required = [

    "Location Barcode",
    "Item Name",
    "Quantity",
    "Minimum Stock"

]


for r in required:

    if r not in headers:

        print(
            "Missing column:",
            r
        )

        exit()



# =====================================================
# READ EXCEL INTO MEMORY
# =====================================================
#
# The Excel file is treated as the single source of truth.
# Every (location, item) combination is read once, so that
# running this script any number of times always leaves the
# database with exactly what is in the Excel file - never
# duplicated, and never stale.
#
# If the same location + item appears more than once in the
# Excel file itself, the quantities are added together and
# the row is reported, instead of creating two rows in the
# database for the same bin/item.

stock_data = {}

duplicate_rows_in_excel = 0


for row in ws.iter_rows(
    min_row=2,
    values_only=True
):


    location = row[
        headers["Location Barcode"]-1
    ]


    item = row[
        headers["Item Name"]-1
    ]


    quantity = row[
        headers["Quantity"]-1
    ]


    minimum = row[
        headers["Minimum Stock"]-1
    ]



    if not location or not item:

        continue



    location = str(location).strip()

    item = str(item).strip()

    quantity = int(quantity) if quantity else 0

    minimum = int(minimum) if minimum else 0


    key = (location, item)


    if key in stock_data:

        duplicate_rows_in_excel += 1

        print(
            "Duplicate row in Excel, quantities combined:",
            location,
            "-",
            item
        )

        existing_qty, existing_min = stock_data[key]

        stock_data[key] = (
            existing_qty + quantity,
            max(existing_min, minimum)
        )

    else:

        stock_data[key] = (quantity, minimum)



# =====================================================
# REPLACE STOCK TABLE WITH EXCEL DATA
# =====================================================
#
# The whole stock table is rebuilt from the Excel file inside
# a single transaction, so the database always ends up an
# exact match of the Excel file, and a failure part-way through
# leaves the previous data untouched instead of a half-updated
# table.

try:

    cursor.execute("BEGIN")

    cursor.execute("DELETE FROM stock")

    count = 0

    for (location, item), (quantity, minimum) in stock_data.items():

        cursor.execute("""
        INSERT INTO stock
        (
            location_barcode,
            item_name,
            quantity,
            minimum_stock
        )

        VALUES(?,?,?,?)

        """,
        (
         location,
         item,
         quantity,
         minimum
         ))

        count += 1

    conn.commit()

except Exception as e:

    conn.rollback()

    print("\nImport failed, no changes were made:", e)

    conn.close()

    exit()



print(
    "\nRows written to database:",
    count
)

if duplicate_rows_in_excel:

    print(
        "Duplicate location/item rows merged from Excel:",
        duplicate_rows_in_excel
    )



# =====================================================
# VERIFY
# =====================================================

cursor.execute(
    "SELECT COUNT(*) FROM stock"
)


print(
    "Database Stock Rows:",
    cursor.fetchone()[0]
)


cursor.execute(
    "SELECT SUM(quantity) FROM stock"
)

print(
    "Database Total Quantity:",
    cursor.fetchone()[0]
)



conn.close()


print("\nImport Completed - Database now matches the Excel file exactly")
