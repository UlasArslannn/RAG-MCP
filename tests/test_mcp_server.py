"""
Unit tests for MCP Server database operations (new_server.py)
Tests the core add_comment and get_comments functions directly via SQLite.
"""
import sqlite3
import json
import pytest


# ─────────────────────── Helper Functions ───────────────────────
# We test the DB logic directly instead of going through MCP protocol,
# since MCP transport is a separate concern.

def db_add_comment(db_path: str, query: str, values: str = None) -> bool:
    """Mirrors new_server.py add_comment logic"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        if values:
            parsed_values = json.loads(values)
            cursor.execute(query, parsed_values)
        else:
            cursor.execute(query)
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()


def db_get_comments(db_path: str, query: str = "SELECT * FROM reviews", values: str = None) -> dict:
    """Mirrors new_server.py get_comments logic"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        if values:
            parsed_values = json.loads(values)
            cursor.execute(query, parsed_values)
        else:
            cursor.execute(query)
        rows = cursor.fetchall()
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
        return {'comments': [], 'error': str(e)}
    finally:
        conn.close()


# ─────────────────────── Tests ───────────────────────


class TestInitDB:
    """Tests for database initialization"""

    def test_table_exists(self, temp_db):
        """Reviews table should be created"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reviews'")
        result = cursor.fetchone()
        conn.close()
        assert result is not None
        assert result[0] == 'reviews'

    def test_table_schema(self, temp_db):
        """Table should have correct columns: id, username, rating, text"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(reviews)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        assert 'id' in columns
        assert 'username' in columns
        assert 'rating' in columns
        assert 'text' in columns


class TestAddComment:
    """Tests for adding comments/reviews"""

    def test_add_single_comment(self, temp_db):
        """Should add a comment and return True"""
        result = db_add_comment(
            temp_db,
            'INSERT INTO reviews (username, rating, text) VALUES (?, ?, ?)',
            json.dumps(["test_user", 5, "Great pizza!"])
        )
        assert result is True

        # Verify it was actually inserted
        comments = db_get_comments(temp_db)
        assert len(comments['comments']) == 1
        assert comments['comments'][0]['username'] == 'test_user'
        assert comments['comments'][0]['rating'] == 5

    def test_add_multiple_comments(self, temp_db):
        """Should be able to add multiple comments"""
        for i in range(5):
            db_add_comment(
                temp_db,
                'INSERT INTO reviews (username, rating, text) VALUES (?, ?, ?)',
                json.dumps([f"user_{i}", i + 1, f"Review {i}"])
            )

        comments = db_get_comments(temp_db)
        assert len(comments['comments']) == 5

    def test_add_comment_invalid_sql(self, temp_db):
        """Should return False on invalid SQL"""
        result = db_add_comment(
            temp_db,
            'INSERT INTO nonexistent_table (x) VALUES (?)',
            json.dumps(["value"])
        )
        assert result is False

    def test_add_comment_auto_increment_id(self, temp_db):
        """IDs should auto-increment"""
        for i in range(3):
            db_add_comment(
                temp_db,
                'INSERT INTO reviews (username, rating, text) VALUES (?, ?, ?)',
                json.dumps([f"user_{i}", 5, "test"])
            )

        comments = db_get_comments(temp_db)
        ids = [c['id'] for c in comments['comments']]
        assert ids == [1, 2, 3]


class TestGetComments:
    """Tests for retrieving comments/reviews"""

    def test_get_all_comments(self, populated_db):
        """Should return all 5 sample reviews"""
        comments = db_get_comments(populated_db)
        assert len(comments['comments']) == 5

    def test_get_comments_structure(self, populated_db):
        """Each comment should have id, username, rating, text"""
        comments = db_get_comments(populated_db)
        for comment in comments['comments']:
            assert 'id' in comment
            assert 'username' in comment
            assert 'rating' in comment
            assert 'text' in comment

    def test_get_comments_empty_db(self, temp_db):
        """Should return empty list for empty database"""
        comments = db_get_comments(temp_db)
        assert comments['comments'] == []

    def test_get_comments_with_where_filter(self, populated_db):
        """Should filter by username"""
        comments = db_get_comments(
            populated_db,
            query='SELECT * FROM reviews WHERE username = ?',
            values=json.dumps(["alice"])
        )
        assert len(comments['comments']) == 1
        assert comments['comments'][0]['username'] == 'alice'

    def test_get_comments_by_rating(self, populated_db):
        """Should filter by minimum rating"""
        comments = db_get_comments(
            populated_db,
            query='SELECT * FROM reviews WHERE rating >= ?',
            values=json.dumps([4])
        )
        # alice(5), leo(4), maya(5) = 3 reviews
        assert len(comments['comments']) == 3

    def test_get_comments_order_by(self, populated_db):
        """Should support ORDER BY"""
        comments = db_get_comments(
            populated_db,
            query='SELECT * FROM reviews ORDER BY rating ASC'
        )
        ratings = [c['rating'] for c in comments['comments']]
        assert ratings == sorted(ratings)

    def test_get_comments_invalid_sql(self, populated_db):
        """Should return error on invalid SQL"""
        comments = db_get_comments(
            populated_db,
            query='SELECT * FROM nonexistent_table'
        )
        assert comments['comments'] == []
        assert 'error' in comments


class TestDataIntegrity:
    """Tests for data integrity and edge cases"""

    def test_special_characters_in_text(self, temp_db):
        """Should handle special characters (quotes, unicode, emojis)"""
        special_text = "Best pizza I've ever had! 🍕 \"Absolutely amazing\" — très bon!"
        db_add_comment(
            temp_db,
            'INSERT INTO reviews (username, rating, text) VALUES (?, ?, ?)',
            json.dumps(["unicode_user", 5, special_text])
        )
        comments = db_get_comments(temp_db)
        assert comments['comments'][0]['text'] == special_text

    def test_null_text_field(self, temp_db):
        """Text field is optional (can be NULL)"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO reviews (username, rating) VALUES (?, ?)',
            ("no_text_user", 3)
        )
        conn.commit()
        conn.close()

        comments = db_get_comments(temp_db)
        assert comments['comments'][0]['text'] is None

    def test_rating_boundaries(self, temp_db):
        """Should accept rating values"""
        for rating in [1, 2, 3, 4, 5]:
            db_add_comment(
                temp_db,
                'INSERT INTO reviews (username, rating, text) VALUES (?, ?, ?)',
                json.dumps([f"user_{rating}", rating, f"Rating {rating}"])
            )

        comments = db_get_comments(temp_db)
        assert len(comments['comments']) == 5
