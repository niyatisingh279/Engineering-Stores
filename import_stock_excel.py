import sqlite3
import openpyxl


DB="engineering_store.db"

EXCEL="Engineering_Store_Stock.xlsx"


conn=sqlite3.connect(DB)

cursor=conn.cursor()



wb=openpyxl.load_workbook(EXCEL)

ws=wb.active



count=0


for row in ws.iter_rows(min_row=2,values_only=True):

    barcode=row[0]
    item=row[1]
    qty=row[2]


    if not barcode:
        continue


    cursor.execute("""
    INSERT INTO stock
    (
    location_barcode,
    item_name,
    quantity
    )
    VALUES(?,?,?)
    """,
    (
    barcode,
    item,
    qty
    ))


    count+=1



conn.commit()

conn.close()


print(
    "Imported:",
    count,
    "records"
)