import sqlite3
import openpyxl
from openpyxl.styles import Font


DB = "engineering_store.db"

OUTPUT = "Engineering_Store_Stock.xlsx"


# Connect database

conn = sqlite3.connect(DB)
cursor = conn.cursor()


# Fetch stock

cursor.execute("""
SELECT
location_barcode,
item,
quantity

FROM stock

ORDER BY location_barcode
""")


rows = cursor.fetchall()


conn.close()



# Create Excel

wb = openpyxl.Workbook()

ws = wb.active

ws.title = "Stock"


# Headers

ws.append([
    "Location Barcode",
    "Item Name",
    "Quantity"
])


for cell in ws[1]:
    cell.font = Font(bold=True)



# Data

for row in rows:
    ws.append(row)



# Adjust width

for col in ws.columns:

    max_length = 0

    letter = col[0].column_letter

    for cell in col:
        if cell.value:
            max_length = max(
                max_length,
                len(str(cell.value))
            )

    ws.column_dimensions[letter].width = max_length + 5



wb.save(OUTPUT)


print("Export completed:")
print(OUTPUT)