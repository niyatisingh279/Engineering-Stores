import sqlite3


conn = sqlite3.connect(
    "engineering_store.db"
)

cursor = conn.cursor()



def receive_stock(
    item_name,
    location,
    qty
):

    cursor.execute("""
    SELECT id
    FROM items
    WHERE item_name=?
    """,
    (item_name,))


    item = cursor.fetchone()


    if not item:
        print("Item not found")
        return


    item_id = item[0]


    cursor.execute("""
    SELECT quantity
    FROM stock
    WHERE item_id=?
    AND location_barcode=?
    """,
    (
        item_id,
        location
    ))


    existing = cursor.fetchone()


    if existing:

        cursor.execute("""
        UPDATE stock
        SET quantity=quantity+?
        WHERE item_id=?
        AND location_barcode=?
        """,
        (
            qty,
            item_id,
            location
        ))

    else:

        cursor.execute("""
        INSERT INTO stock
        VALUES
        (NULL,?,?,?)
        """,
        (
            location,
            item_id,
            qty
        ))



    cursor.execute("""
    INSERT INTO transactions
    (
        item_id,
        location_barcode,
        transaction_type,
        quantity
    )
    VALUES(?,?,?,?)
    """,
    (
        item_id,
        location,
        "RECEIVE",
        qty
    ))


    conn.commit()



def issue_stock(
    item_name,
    location,
    qty
):

    cursor.execute("""
    SELECT id
    FROM items
    WHERE item_name=?
    """,
    (item_name,))


    item_id = cursor.fetchone()[0]


    cursor.execute("""
    UPDATE stock
    SET quantity=quantity-?
    WHERE item_id=?
    AND location_barcode=?
    """,
    (
        qty,
        item_id,
        location
    ))


    cursor.execute("""
    INSERT INTO transactions
    (
        item_id,
        location_barcode,
        transaction_type,
        quantity
    )
    VALUES(?,?,?,?)
    """,
    (
        item_id,
        location,
        "ISSUE",
        qty
    ))


    conn.commit()



# Testing

receive_stock(
    "M8 Nut",
    "A/P1/L1/B1",
    1000
)


issue_stock(
    "M8 Nut",
    "A/P1/L1/B1",
    50
)



conn.close()