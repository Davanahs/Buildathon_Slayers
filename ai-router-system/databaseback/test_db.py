import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def test_database():
    db_url = os.getenv("DATABASE_URL")

    print("Loaded DATABASE_URL:", "YES" if db_url else "NO")

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        print("✅ Database connected successfully")

        cur.execute("SELECT current_database();")
        print("Connected DB:", cur.fetchone()[0])

        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cur.fetchall()

        print("\n📌 Tables:")
        for table in tables:
            print("-", table[0])

        cur.close()
        conn.close()

    except Exception as e:
        print("\n❌ Database test failed")
        print("Error:", e)


if __name__ == "__main__":
    test_database()