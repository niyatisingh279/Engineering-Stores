import sqlite3


conn = sqlite3.connect(
    "engineering_store.db"
)

cursor = conn.cursor()


def add_item(
    name,
    category,
    unit,
    min_stock
):

    cursor.execute("""
    INSERT INTO items
    (
        item_name,
        category,
        unit,
        minimum_stock
    )
    VALUES(?,?,?,?)
    """,
    (
        name,
        category,
        unit,
        min_stock
    ))

    conn.commit()



add_item(
    "M8 Nut",
    "Nut Bolt",
    "Nos",
    100
)


add_item(
    "M10 Bolt",
    "Nut Bolt",
    "Nos",
    100
)


conn.close()

print("Items Added")