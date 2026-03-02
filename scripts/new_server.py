import sqlite3
import argparse
import json
import os
from mcp.server.fastmcp import FastMCP

# reviews.db'nin yolunu belirle: Docker'da DB_PATH env var, lokalde script konumuna göre
DB_PATH = os.getenv('DB_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reviews.db'))

mcp = FastMCP('reviews-db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            rating INTEGER NOT NULL,
            text TEXT
        )
    ''')
    conn.commit()
    return conn, cursor

@mcp.tool()
def add_comment(query: str, values: str = None) -> bool:
    """Add a new review/comment to the reviews table using a SQL INSERT query.

    Args:
        query (str): SQL INSERT query following this format:
            INSERT INTO reviews (username, rating, text) VALUES (?, ?, ?)
        values (str): JSON string of values to insert, e.g., '["ulas", 5, "Great pizza"]'
        
    Schema:
        - username: Text field (required)
        - rating: Integer field (required, 1-5)
        - text: Text field (optional)
        Note: 'id' field is auto-generated
    
    Returns:
        bool: True if comment was added successfully, False otherwise
    
    Example:
        >>> add_comment(
        ...     query='INSERT INTO reviews (username, rating, text) VALUES (?, ?, ?)',
        ...     values='["ulas", 5, "Pizzas were great"]'
        ... )
        True
    """
    conn, cursor = init_db()
    try:
        if values:
            # Parse JSON string to list
            parsed_values = json.loads(values)
            cursor.execute(query, parsed_values)
        else:
            cursor.execute(query)
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error adding comment: {e}")
        return False
    finally:
        conn.close()

@mcp.tool()
def get_comments(query: str = "SELECT * FROM reviews", values: str = None) -> dict:
    """Read reviews/comments from the reviews table using a SQL SELECT query.

    Args:
        query (str, optional): SQL SELECT query. Defaults to "SELECT * FROM reviews".
            Examples:
            - "SELECT * FROM reviews"
            - "SELECT * FROM reviews WHERE username = ?"
            - "SELECT * FROM reviews WHERE rating > ?"
            - "SELECT * FROM reviews ORDER BY rating DESC"
        values (str): JSON string of parameter values for WHERE clause, e.g., '["ulas"]' or '[5]'
    
    Returns:
        dict: Dictionary with 'comments' key containing list of comment dictionaries.
              Each comment has: id, username, rating, text
    
    Example:
        >>> # Get all comments
        >>> get_comments()
        {'comments': [{'id': 1, 'username': 'ulas', 'rating': 5, 'text': 'Great!'}]}
        
        >>> # Get comments by username
        >>> get_comments(
        ...     query='SELECT * FROM reviews WHERE username = ?',
        ...     values='["ulas"]'
        ... )
    """
    conn, cursor = init_db()
    try:
        if values:
            # Parse JSON string to list
            parsed_values = json.loads(values)
            cursor.execute(query, parsed_values)
        else:
            cursor.execute(query)
        
        rows = cursor.fetchall()
        
        # Convert rows to list of dictionaries
        comments = []
        for row in rows:
            comment = {
                'id': row[0],
                'username': row[1],
                'rating': row[2],
                'text': row[3]
            }
            comments.append(comment)
        
        return {'comments': comments}
    except sqlite3.Error as e:
        print(f"Error reading comments: {e}")
        return {'comments': [], 'error': str(e)}
    finally:
        conn.close()



if __name__ == "__main__":
    # Start the server
    print("🚀 Starting reviews database server... ")

    # Debug Mode
    #  uv run mcp dev new_server.py

    # Production Mode
    # python new_server.py --server_type=sse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--server_type", type=str, default="sse", choices=["sse", "stdio"]
    )

    args = parser.parse_args()
    mcp.run(args.server_type)



# # Example usage
# if __name__ == "__main__":
#     # Example INSERT query
#     insert_query = """
#     INSERT INTO reviews (username, rating, text)
#     VALUES (?, ?, ?)
#     """
#     values = json.dumps(["ulas", 5, "Pizzas were great"])
    
#     # Add comment
#     if add_comment(insert_query, values):
#         print("Comment added successfully")
    
#     # Read all comments
#     results = get_comments()
#     print("\nAll reviews:")
#     for comment in results['comments']:
#         print(comment)
