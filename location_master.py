import sqlite3


conn = sqlite3.connect(
    "engineering_store.db"
)

cursor = conn.cursor()


def add_location(
    barcode,
    rack,
    partition,
    level,
    bin_no
):

    cursor.execute("""
    INSERT INTO locations
    (
        location_barcode,
        rack,
        partition,
        level,
        bin
    )
    VALUES(?,?,?,?,?)
    """,
    (
        barcode,
        rack,
        partition,
        level,
        bin_no
    ))

    conn.commit()


# Example locations

add_location(
    "A/P1/L1/B1",
    "A",
    "P1",
    "L1",
    "B1"
)


add_location(
    "A/P1/L1/B2",
    "A",
    "P1",
    "L1",
    "B2"
)


conn.close()

print("Locations Added")