import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import openpyxl


DB = "engineering_store.db"


# =====================================================
# DATABASE
# =====================================================

def connect():
    return sqlite3.connect(DB)



# =====================================================
# LOCATION DECODER
# =====================================================

def decode_location(barcode):

    try:
        p = barcode.split("/")

        return f"""
Rack       : {p[0]}
Partition  : {p[1]}
Level      : {p[2]}
Bin        : {p[3]}
"""

    except:
        return "Invalid Barcode"



# =====================================================
# RECEIVE STOCK
# =====================================================

def receive_stock():

    item = receive_item.get().strip()
    barcode = receive_bin.get().strip()
    qty = receive_qty.get().strip()


    if not item or not barcode or not qty:

        messagebox.showerror(
            "Error",
            "Select item, enter bin barcode and quantity"
        )

        return



    try:

        qty = int(qty)

    except:

        messagebox.showerror(
            "Error",
            "Quantity must be a number"
        )

        return



    conn = connect()

    cur = conn.cursor()



    # CHECK EXISTING STOCK

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


    result = cur.fetchone()



    if result:


        # UPDATE EXISTING STOCK

        cur.execute("""
        UPDATE stock

        SET quantity = quantity + ?

        WHERE location_barcode=?

        AND item_name=?

        """,
        (
            qty,
            barcode,
            item
        ))



    else:


        # INSERT NEW ITEM IN BIN

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
            barcode,
            item,
            qty,
            0
        ))



    # TRANSACTION HISTORY

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
        barcode,
        item,
        "RECEIVE",
        qty
    ))



    conn.commit()

    conn.close()



    messagebox.showinfo(
        "Success",
        f"{qty} quantity added\n\nItem: {item}"
    )



    # CLEAR QUANTITY ONLY

    receive_qty.set("")



# =====================================================
# ISSUE STOCK
# =====================================================

def issue_stock():

    item = issue_item.get().strip()
    barcode = issue_bin.get().strip()
    qty = issue_qty.get().strip()


    if not item or not barcode or not qty:

        messagebox.showerror(
            "Error",
            "Select item, enter bin barcode and quantity"
        )

        return


    try:
        qty = int(qty)

    except:

        messagebox.showerror(
            "Error",
            "Quantity must be a number"
        )

        return



    conn = connect()

    cur = conn.cursor()



    # CHECK AVAILABLE STOCK

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



    if not row:

        messagebox.showerror(
            "Error",
            "Stock not found"
        )

        conn.close()

        return



    available_qty = row[0]



    if qty > available_qty:

        messagebox.showerror(
            "Error",
            f"Insufficient stock\nAvailable: {available_qty}"
        )

        conn.close()

        return



    # UPDATE STOCK

    cur.execute("""
    UPDATE stock

    SET quantity = quantity - ?

    WHERE location_barcode=?

    AND item_name=?

    """,
    (
        qty,
        barcode,
        item
    ))



    # SAVE TRANSACTION HISTORY

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
        barcode,
        item,
        "ISSUE",
        qty
    ))



    conn.commit()

    conn.close()



    messagebox.showinfo(
        "Success",
        f"{qty} quantity issued\n\nItem: {item}"
    )


    # CLEAR FIELDS

    issue_qty.set("")
# =====================================================
# SEARCH ITEM
# =====================================================

def search_item():

    keyword = search_box.get().strip()


    if keyword == "":
        messagebox.showwarning(
            "Search",
            "Enter item name"
        )
        return


    conn = connect()

    cur = conn.cursor()


    cur.execute("""
    SELECT
        location_barcode,
        item_name,
        quantity,
        minimum_stock

    FROM stock

    WHERE item_name LIKE ?

    ORDER BY item_name

    """,
    (
        "%" + keyword + "%",
    ))


    rows = cur.fetchall()


    conn.close()


    search_result.delete(
        "1.0",
        tk.END
    )


    if not rows:

        search_result.insert(
            tk.END,
            "No item found"
        )

        return



    for r in rows:

        location = r[0]

        parts = location.split("/")


        rack = parts[0] if len(parts)>0 else ""
        partition = parts[1] if len(parts)>1 else ""
        level = parts[2] if len(parts)>2 else ""
        bin_no = parts[3] if len(parts)>3 else ""


        search_result.insert(
            tk.END,

f"""
Item Name        : {r[1]}

Rack             : {rack}
Partition        : {partition}
Level            : {level}
Bin              : {bin_no}

Location Barcode : {location}

Quantity         : {r[2]}

Minimum Stock    : {r[3]}

----------------------------------------

"""
        )

# =====================================================
# SCAN BIN
# =====================================================

def scan_bin():

    barcode = scan_box.get()


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


    scan_result.delete(
        "1.0",
        tk.END
    )


    scan_result.insert(
        tk.END,
        f"""
BIN:
{barcode}


"""
    )


    for r in rows:

        scan_result.insert(
            tk.END,
            f"""
Item:
{r[0]}

Quantity:
{r[1]}

----------------

"""
        )



# =====================================================
# EXPORT MOBILE EXCEL
# =====================================================

def export_excel():

    conn = connect()
    cur = conn.cursor()


    cur.execute("""
    SELECT
    location_barcode,
    item_name,
    quantity

    FROM stock
    """)


    rows = cur.fetchall()

    conn.close()



    wb = openpyxl.Workbook()

    ws = wb.active

    ws.append(
        [
        "Location Barcode",
        "Item Name",
        "Quantity"
        ]
    )


    for r in rows:
        ws.append(r)



    wb.save(
        "Engineering_Store_Mobile.xlsx"
    )


    messagebox.showinfo(
        "Export",
        "Mobile Excel Created"
    )



# =====================================================
# UI
# =====================================================

root=tk.Tk()

root.title(
"Engineering Store Management"
)

root.geometry(
"1000x700"
)


style=ttk.Style()

style.configure(
"TButton",
font=("Arial",12)
)


title=tk.Label(
root,
text="Engineering Store Management",
font=("Arial",20,"bold")
)

title.pack(
pady=15
)



tabs=ttk.Notebook(root)

tabs.pack(
expand=True,
fill="both"
)



# ================= RECEIVE TAB =================


# ================= RECEIVE TAB =================


receive_tab=tk.Frame(tabs)

tabs.add(
    receive_tab,
    text="Receive Stock"
)


receive_item=tk.StringVar()
receive_bin=tk.StringVar()
receive_qty=tk.StringVar()



# LOAD ITEMS AFTER BIN ENTRY

def load_receive_items(*args):

    barcode = receive_bin.get().strip()

    if barcode == "":
        return


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


    items = []

    for r in rows:
        items.append(r[0])


    receive_dropdown["values"] = items


    if items:
        receive_dropdown.current(0)



# ITEM NAME DROPDOWN

tk.Label(
    receive_tab,
    text="Item Name",
    font=("Arial",12)
).pack()


receive_dropdown = ttk.Combobox(
    receive_tab,
    textvariable=receive_item,
    width=37,
    state="normal"
)

receive_dropdown.pack(
    pady=5
)



# BIN BARCODE

tk.Label(
    receive_tab,
    text="Bin Barcode",
    font=("Arial",12)
).pack()


tk.Entry(
    receive_tab,
    textvariable=receive_bin,
    width=40
).pack(
    pady=5
)



# QUANTITY

tk.Label(
    receive_tab,
    text="Quantity",
    font=("Arial",12)
).pack()


tk.Entry(
    receive_tab,
    textvariable=receive_qty,
    width=40
).pack(
    pady=5
)



# WHEN BIN BARCODE CHANGES LOAD ITEMS

receive_bin.trace(
    "w",
    lambda *args: load_receive_items()
)


# BUTTON

tk.Button(
    receive_tab,
    text="ADD STOCK",
    command=receive_stock
).pack(
    pady=20
)

def load_issue_items(event=None):

    barcode = issue_bin.get().strip()

    if barcode == "":
        return


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


    items = []

    for r in rows:
        items.append(r[0])


    issue_items_dropdown["values"] = items


    if items:
        issue_items_dropdown.current(0)

# ================= ISSUE TAB =================


issue_tab=tk.Frame(tabs)

tabs.add(
issue_tab,
text="Issue Stock"
)


issue_item=tk.StringVar()
issue_bin=tk.StringVar()
issue_qty=tk.StringVar()
issue_bin.trace(
    "w",
    lambda *args: load_issue_items()
)


# ITEM NAME DROPDOWN

tk.Label(
    issue_tab,
    text="Item Name"
).pack()


issue_items_dropdown = ttk.Combobox(
    issue_tab,
    textvariable=issue_item,
    width=37,
    state="readonly"
)

issue_items_dropdown.pack(
    pady=5
)



# BIN BARCODE

tk.Label(
    issue_tab,
    text="Bin Barcode"
).pack()


tk.Entry(
    issue_tab,
    textvariable=issue_bin,
    width=40
).pack(
    pady=5
)



# QUANTITY

tk.Label(
    issue_tab,
    text="Quantity"
).pack()


tk.Entry(
    issue_tab,
    textvariable=issue_qty,
    width=40
).pack(
    pady=5
)



tk.Button(
issue_tab,
text="ISSUE STOCK",
command=issue_stock
).pack(pady=20)



# ================= SEARCH TAB =================


search_tab=tk.Frame(tabs)

tabs.add(
search_tab,
text="Search Item"
)


search_box=tk.Entry(
search_tab,
width=40
)

search_box.pack(pady=10)


tk.Button(
search_tab,
text="SEARCH",
command=search_item
).pack()


search_result=tk.Text(
search_tab,
height=25,
width=70
)

search_result.pack(
pady=20
)



# ================= SCAN TAB =================


scan_tab=tk.Frame(tabs)

tabs.add(
scan_tab,
text="Scan Bin"
)


scan_box=tk.Entry(
scan_tab,
width=40
)

scan_box.pack(pady=10)


tk.Button(
scan_tab,
text="SHOW CONTENTS",
command=scan_bin
).pack()


scan_result=tk.Text(
scan_tab,
height=25,
width=70
)

scan_result.pack(
pady=20
)



# ================= EXPORT =================


export_tab=tk.Frame(tabs)

tabs.add(
export_tab,
text="Mobile Export"
)


tk.Button(
export_tab,
text="EXPORT MOBILE EXCEL",
font=("Arial",14),
command=export_excel
).pack(
pady=50
)



root.mainloop()