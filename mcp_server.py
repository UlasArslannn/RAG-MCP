import sqlite3
import argparse
from mcp.server.fastmcp import FastMCP


mcp = FastMCP(name="sqlite-mcp")


def init_db():

    conn = sqlite3.connect('reviews.db')
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY,
        username TEXT not null,
        rating INTEGER not null,
        text TEXT
    )
    """)

    conn.commit()
    conn.close()

    return conn, cursor


@mcp.tool()
def add_comment(query : str) -> bool:
    """Add a comment to the database.
    
    Args:
        query (str): The SQL query to execute following this format: 
            INSERT INTO reviews (username, rating, text)
            VALUES (John Doe, 5, "This is a great restaurant")
    
    Schema:
        -username : TEXT field (required)
        -rating : INTEGER field (required)
        -text : TEXT field (required)

        -id : INTEGER field (auto-increment)



    Returns:
        bool: True if the comment was added successfully. False otherwise.

    Example:
        >>> query = '''
        ... INSERT INTO reviews (username, rating, text)
        ... VALUES ('John Doe', 5, 'This is a great restaurant')
        ... '''
        >>> add_data(query)
        True
    """
    try:
        conn, cursor = init_db()
        cursor.execute(query)
        conn.commit()
        return True
    except Exception as e:
        print(e)
        return False

    finally:
        conn.close()


@mcp.tool()
def get_comments(query : str = "SELECT * FROM reviews") -> list:
    """Get all comments from the database or spesific comments based on query.
    
    Args:
        query (str): The SQL query to execute following this format: 
            examples:

            - SELECT * FROM reviews
            - SELECT * FROM reviews WHERE rating > 3
            - SELECT * FROM reviews WHERE username = 'John Doe'
            - SELECT * FROM reviews WHERE text LIKE '%great%'
    
    Returns:
        list: List of comments.
                for default query it returns all comments and tuple format is (id, username, rating, text).


    Example:
        >>> query = '''
        ... SELECT * FROM reviews
        ... '''
        >>> get_comments(query)
        [(1, 'John Doe', 5, 'This is a great restaurant'), (2, 'Jane Doe', 4, 'This is a great restaurant')]


        >>> query = '''
        ... SELECT * FROM reviews WHERE rating > 3
        ... '''
        >>> get_comments(query)
        [(1, 'John Doe', 5, 'This is a great restaurant'), (2, 'Jane Doe', 4, 'This is a great restaurant')]


        >>> query = '''
        ... SELECT * FROM reviews WHERE username = 'John Doe'
        ... '''
        >>> get_comments(query)
        [(1, 'John Doe', 5, 'This is a great restaurant')]


        >>> query = '''
        ... SELECT * FROM reviews WHERE text LIKE '%great%'
        ... '''
        >>> get_comments(query)
        [(1, 'John Doe', 5, 'This is a great restaurant'), (2, 'Jane Doe', 4, 'This is a great restaurant')]
    """
    try:
        conn, cursor = init_db()
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        print(e)
        return []
    finally:
        conn.close()




if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--server_type", type=str, default="sse", choices=["sse", "stdio"]
    )

    args = parser.parse_args()
    mcp.run(args.server_type)

init_db()
