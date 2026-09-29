import sqlite3


conn = sqlite3.connect(
    "engineering_store.db"
)

cursor = conn.cursor()


item="M8 Nut"


cursor.execute("""
SELECT
items.item_name,
locations.rack,
locations.partition,
locations.level,
locations.bin,
stock.quantity

FROM stock

JOIN items
ON stock.item_id=items.id

JOIN locations
ON stock.location_barcode=
locations.location_barcode

WHERE items.item_name=?

""",
(item,))


result=cursor.fetchall()


for r in result:

    print("""
Item:
{}

Location:
Rack {}
Partition {}
Level {}
Bin {}

Stock:
{}
"""
.format(
r[0],
r[1],
r[2],
r[3],
r[4],
r[5]
))


conn.close()