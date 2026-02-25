import sqlite3

def add_col():
    conn = sqlite3.connect("sysconnect.db")
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE global_config ADD COLUMN screenshot_interval INTEGER DEFAULT 20;")
        conn.commit()
        print("Column added")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

add_col()
