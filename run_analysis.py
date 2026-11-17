"""Load the sample CSV files into a local SQLite database.

Run: python run_analysis.py
Uses only Python's standard library.
"""
import csv
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "customer_transactions.db"

def load_csv(connection, table_name, csv_path):
    with csv_path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        columns = reader.fieldnames
        if not columns:
            raise ValueError(f"No columns found in {csv_path.name}")

        # Create a simple text-based staging table; analytical queries cast
        # numeric fields where needed.
        column_sql = ", ".join(f'"{column}" TEXT' for column in columns)
        connection.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ({column_sql})')
        connection.execute(f'DELETE FROM "{table_name}"')

        placeholders = ", ".join("?" for _ in columns)
        insert_sql = f'INSERT INTO "{table_name}" VALUES ({placeholders})'
        rows = [[row[column] for column in columns] for row in reader]
        connection.executemany(insert_sql, rows)
        print(f"Loaded {len(rows)} rows into {table_name}")

def main():
    with sqlite3.connect(DB_PATH) as connection:
        load_csv(connection, "customers", BASE_DIR / "customers.csv")
        load_csv(connection, "transactions", BASE_DIR / "transactions.csv")

        # Basic integrity checks
        customer_count = connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        transaction_count = connection.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        orphan_count = connection.execute("""
            SELECT COUNT(*) FROM transactions t
            LEFT JOIN customers c ON c.customer_id = t.customer_id
            WHERE c.customer_id IS NULL
        """).fetchone()[0]

        print("\nDATA CHECK")
        print(f"Customers: {customer_count}")
        print(f"Transactions: {transaction_count}")
        print(f"Transactions without a matching customer: {orphan_count}")

        print("\nTRANSACTION SUMMARY")
        for row in connection.execute("""
            SELECT status, COUNT(*) AS transaction_count,
                   SUM(CAST(amount_inr AS REAL)) AS total_amount_inr
            FROM transactions
            GROUP BY status
            ORDER BY status
        """):
            print(f"{row[0]}: {row[1]} transactions | INR {row[2]:,.2f}")

        print("\nCOMPLETED SPEND BY CUSTOMER")
        for row in connection.execute("""
            SELECT c.customer_name, c.city,
                   COUNT(t.transaction_id) AS completed_transactions,
                   SUM(CAST(t.amount_inr AS REAL)) AS completed_spend
            FROM customers c
            JOIN transactions t ON t.customer_id = c.customer_id
            WHERE t.status = 'Completed'
            GROUP BY c.customer_id, c.customer_name, c.city
            ORDER BY completed_spend DESC
        """):
            print(f"{row[0]} ({row[1]}): {row[2]} transactions | INR {row[3]:,.2f}")

if __name__ == "__main__":
    main()
