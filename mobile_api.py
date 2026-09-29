from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
from fastapi.responses import FileResponse
from openpyxl import Workbook
from datetime import datetime
import os
from pathlib import Path

app = FastAPI()


# ======================================
# CORS
# ======================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


DB = "engineering_store.db"

# Folder containing the printed bin barcode labels.
# This is treated as the master list of every physical bin that exists,
# since there is no separate "locations" table in the database.
BARCODE_FOLDER = Path(__file__).resolve().parent / "Engineering_Store_Barcodes"



def connect():
    return sqlite3.connect(DB)



def get_all_bins():
    """
    Returns every bin barcode that has a printed label
    (i.e. every physical bin that exists in the store),
    derived from the barcode image filenames.

    Filenames look like A_P1_L1_B1.png, which represents
    the barcode value A/P1/L1/B1
    """

    bins = []

    if BARCODE_FOLDER.exists():

        for f in BARCODE_FOLDER.glob("*.png"):

            barcode = f.stem.replace("_", "/")

            bins.append(barcode)

    return sorted(bins)




# ======================================
# SCAN BIN
# ======================================

@app.get("/scan/{barcode:path}")
def scan_bin(barcode:str):

    conn = connect()
    cur = conn.cursor()


    cur.execute("""
    SELECT
    item_name,
    quantity

    FROM stock

    WHERE location_barcode=?

    """,
    (barcode,))


    rows = cur.fetchall()

    conn.close()


    parts = barcode.split("/")


    return {

        "barcode":barcode,

        "rack":parts[0] if len(parts)>0 else "",

        "partition":parts[1] if len(parts)>1 else "",

        "level":parts[2] if len(parts)>2 else "",

        "bin":parts[3] if len(parts)>3 else "",


        "items":[

            {
                "name":r[0],
                "quantity":r[1]
            }

            for r in rows

        ]

    }






# ======================================
# BIN ITEMS DROPDOWN
# ======================================

@app.get("/bin_items/{barcode:path}")
def bin_items(barcode:str):

    conn = connect()
    cur = conn.cursor()


    cur.execute("""
    SELECT item_name

    FROM stock

    WHERE location_barcode=?

    """,
    (barcode,))


    rows = cur.fetchall()


    conn.close()


    return [
        r[0]
        for r in rows
    ]




# ======================================
# EMPTY BINS (FOR RECEIVING NEW ITEMS)
# ======================================

@app.get("/empty_bins")
def empty_bins():

    all_bins = get_all_bins()

    conn = connect()
    cur = conn.cursor()


    cur.execute("""
    SELECT DISTINCT location_barcode

    FROM stock

    WHERE quantity > 0

    """)


    occupied = {r[0] for r in cur.fetchall()}

    conn.close()


    empty = [
        b
        for b in all_bins
        if b not in occupied
    ]


    return {

        "total_bins": len(all_bins),

        "occupied_bins": len(occupied),

        "empty_bins": empty

    }




# ======================================
# ITEM STOCK
# ======================================

@app.get("/item_stock/{barcode:path}/{item}")
def item_stock(barcode:str,item:str):

    conn = connect()
    cur = conn.cursor()


    cur.execute("""
    SELECT quantity

    FROM stock

    WHERE location_barcode=?

    AND item_name=?

    """,
    (
        barcode,
        item
    ))


    row = cur.fetchone()


    conn.close()


    return {

        "quantity": row[0] if row else 0

    }







# ======================================
# SEARCH ITEM
# ======================================

@app.get("/search/{item}")
def search_item(item:str):

    conn = connect()
    cur = conn.cursor()


    cur.execute("""
    SELECT

    location_barcode,
    item_name,
    quantity

    FROM stock

    WHERE item_name LIKE ?

    """,
    (
        "%" + item + "%",
    ))



    rows = cur.fetchall()


    conn.close()


    return [

        {

        "location":r[0],

        "item":r[1],

        "quantity":r[2]

        }

        for r in rows

    ]








# ======================================
# STOCK MODEL
# ======================================

class StockRequest(BaseModel):

    location_barcode:str

    item_name:str

    quantity:int








# ======================================
# RECEIVE STOCK
# ======================================

@app.post("/receive")
def receive_stock(data:StockRequest):


    if data.quantity <= 0:

        return {

            "status":"error",

            "message":"Invalid quantity"

        }



    conn = connect()
    cur = conn.cursor()



    cur.execute("""
    SELECT quantity

    FROM stock

    WHERE location_barcode=?

    AND item_name=?

    """,
    (
        data.location_barcode,
        data.item_name
    ))



    result = cur.fetchone()



    if result:


        cur.execute("""
        UPDATE stock

        SET quantity = quantity + ?

        WHERE location_barcode=?

        AND item_name=?

        """,
        (
            data.quantity,
            data.location_barcode,
            data.item_name
        ))


    else:


        cur.execute("""
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
            data.location_barcode,
            data.item_name,
            data.quantity,
            0
        ))






    cur.execute("""
    INSERT INTO transactions
    (
    location_barcode,
    item_name,
    transaction_type,
    quantity
    )

    VALUES(?,?,?,?)

    """,
    (
        data.location_barcode,
        data.item_name,
        "RECEIVE",
        data.quantity
    ))



    conn.commit()
    conn.close()



    return {

        "status":"success",

        "message":"Stock received"

    }








# ======================================
# ISSUE STOCK
# ======================================

@app.post("/issue")
def issue_stock(data:StockRequest):


    if data.quantity <= 0:

        return {

            "status":"error",

            "message":"Invalid quantity"

        }



    conn = connect()
    cur = conn.cursor()



    cur.execute("""
    SELECT quantity

    FROM stock

    WHERE location_barcode=?

    AND item_name=?

    """,
    (
        data.location_barcode,
        data.item_name
    ))



    row = cur.fetchone()



    if not row:


        conn.close()


        return {

            "status":"error",

            "message":"Stock not found"

        }





    available=row[0]



    if data.quantity > available:


        conn.close()


        return {

            "status":"error",

            "message":f"Only {available} available"

        }





    cur.execute("""
    UPDATE stock

    SET quantity = quantity - ?

    WHERE location_barcode=?

    AND item_name=?

    """,
    (
        data.quantity,
        data.location_barcode,
        data.item_name
    ))





    cur.execute("""
    INSERT INTO transactions
    (
    location_barcode,
    item_name,
    transaction_type,
    quantity

    )

    VALUES(?,?,?,?)

    """,
    (
        data.location_barcode,
        data.item_name,
        "ISSUE",
        data.quantity
    ))





    conn.commit()
    conn.close()



    return {

        "status":"success",

        "message":"Stock issued"

    }








# ======================================
# LOW STOCK NOTIFICATIONS
# ======================================

@app.get("/notifications")
def notifications():


    conn = connect()
    cur = conn.cursor()



    cur.execute("""
    SELECT

    location_barcode,
    item_name,
    quantity,
    minimum_stock


    FROM stock


    WHERE quantity <= minimum_stock

    """)



    rows = cur.fetchall()


    conn.close()



    return [

        {

        "location":r[0],

        "item":r[1],

        "quantity":r[2],

        "minimum_stock":r[3]

        }

        for r in rows

    ]








# ======================================
# STOCK HISTORY
# ======================================

@app.get("/history")
def history():


    conn = connect()
    cur = conn.cursor()



    cur.execute("""
    SELECT

    item_name,
    location_barcode,
    transaction_type,
    quantity,
    transaction_date


    FROM transactions


    ORDER BY transaction_date DESC


    LIMIT 100

    """)



    rows = cur.fetchall()


    conn.close()



    return [

        {

        "item":r[0],

        "location":r[1],

        "type":r[2],

        "quantity":r[3],

        "date":r[4]

        }

        for r in rows

    ]







# ======================================
# DASHBOARD SUMMARY
# ======================================

@app.get("/dashboard")
def dashboard():

    conn = connect()
    cur = conn.cursor()


    cur.execute("""
    SELECT COUNT(*)
    FROM stock
    """)

    total_items = cur.fetchone()[0]



    cur.execute("""
    SELECT COUNT(*)
    FROM stock

    WHERE quantity <= minimum_stock

    """)

    low_stock = cur.fetchone()[0]


    conn.close()



    return {

        "total_items":total_items,

        "low_stock":low_stock

    }
# ======================================
# EXPORT LATEST STOCK EXCEL
# ======================================

@app.get("/export_stock")
def export_stock():

    conn = connect()
    cur = conn.cursor()


    cur.execute("""
    SELECT

    location_barcode,
    item_name,
    quantity,
    minimum_stock

    FROM stock

    ORDER BY location_barcode,item_name

    """)


    rows = cur.fetchall()


    conn.close()



    filename = (
        "Engineering_Store_Stock_"
        +
        datetime.now().strftime("%d%m%Y_%H%M")
        +
        ".xlsx"
    )


    wb = Workbook()

    ws = wb.active

    ws.title="Latest Stock"



    ws.append(
        [
        "Location Barcode",
        "Item Name",
        "Quantity",
        "Minimum Stock"
        ]
    )



    for r in rows:

        ws.append(r)



    wb.save(filename)



    return FileResponse(

        filename,

        media_type=
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",

        filename=filename

    )