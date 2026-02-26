import sqlite3

# This script inserts 10 sample reviews into the database.
# Run with `python sql.py` after you've started the MCP server or
# simply to populate the SQLite file directly.


conn = sqlite3.connect('reviews.db')
cur = conn.cursor()

print(conn.execute('SELECT COUNT(*) FROM reviews').fetchone())
# ensure table exists
cur.execute('''
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        rating INTEGER NOT NULL,
        text TEXT
    )
''')

# list of (username, rating, text)
new_reviews = [
    ("karen", 1, "Worst pizza ever, crust was burnt and sauce was bland."),
    ("leo", 4, "Really good pepperoni slice but needed more cheese."),
    ("maya", 5, "Absolutely loved the vegan option, tasted incredible!"),
    ("nate", 3, "It was okay — nothing special, but filled the hunger."),
    ("olga", 5, "The supreme pizza had every topping you could imagine!"),
    ("pete", 2, "Too greasy for me, got a stomach ache later."),
    ("quirk", 4, "Nice atmosphere and the pizza was nice and hot."),
    ("rachel", 5, "Best garlic pizza knots I've ever had."),
    ("sam", 3, "Mediocre cheese pizza, crust was a bit chewy."),
    ("tina", 5, "Loved the thin crust Margherita, so fresh and tasty."),
]

for u, r, t in new_reviews:
    cur.execute(
        'INSERT INTO reviews (username, rating, text) VALUES (?, ?, ?)',
        (u, r, t)
    )

conn.commit()
print("Added", len(new_reviews), "new reviews.")

# print total count
total = conn.execute('SELECT COUNT(*) FROM reviews').fetchone()[0]
print("Total reviews in DB:", total)

conn.close()