"""Run the customer and transaction analysis using Python and SQLite.

Run from this folder: python run_analysis.py
The script creates an outputs/ folder containing CSV reports.
"""
import csv
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
DB_PATH = BASE_DIR / "customer_transactions.db"


def load_csv(connection, table_name, csv_path):
    with csv_path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        columns = reader.fieldnames
        if not columns:
            raise ValueError(f"No columns found in {csv_path.name}")
        column_sql = ", ".join(f'"{column}" TEXT' for column in columns)
        connection.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ({column_sql})')
        connection.execute(f'DELETE FROM "{table_name}"')
        placeholders = ", ".join("?" for _ in columns)
        rows = [[row[column] for column in columns] for row in reader]
        connection.executemany(
            f'INSERT INTO "{table_name}" VALUES ({placeholders})', rows
        )
        print(f"Loaded {len(rows)} rows into {table_name}")


def export_query(connection, filename, query):
    rows = connection.execute(query).fetchall()
    headers = [item[0] for item in connection.execute(query).description]
    with (OUTPUT_DIR / filename).open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"Saved outputs/{filename} ({len(rows)} rows)")


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        load_csv(connection, "customers", BASE_DIR / "customers.csv")
        load_csv(connection, "transactions", BASE_DIR / "transactions.csv")

        print("\nDATA CHECK")
        customer_count = connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        transaction_count = connection.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        orphan_count = connection.execute("""
            SELECT COUNT(*) FROM transactions t
            LEFT JOIN customers c ON c.customer_id = t.customer_id
            WHERE c.customer_id IS NULL
        """).fetchone()[0]
        print(f"Customers: {customer_count}")
        print(f"Transactions: {transaction_count}")
        print(f"Transactions without a matching customer: {orphan_count}")

        print("\nTRANSACTION SUMMARY")
        summary = """
            SELECT status, COUNT(*) AS transaction_count,
                   SUM(CAST(amount_inr AS REAL)) AS total_amount_inr
            FROM transactions GROUP BY status ORDER BY status
        """
        for row in connection.execute(summary):
            print(f"{row[0]}: {row[1]} transactions | INR {row[2]:,.2f}")
        export_query(connection, "transaction_summary.csv", summary)

        customer_spend = """
            SELECT c.customer_name, c.city,
                   COUNT(t.transaction_id) AS completed_transactions,
                   SUM(CAST(t.amount_inr AS REAL)) AS completed_spend_inr
            FROM customers c JOIN transactions t ON t.customer_id = c.customer_id
            WHERE t.status = 'Completed'
            GROUP BY c.customer_id, c.customer_name, c.city
            ORDER BY completed_spend_inr DESC
        """
        print("\nCOMPLETED SPEND BY CUSTOMER")
        for row in connection.execute(customer_spend):
            print(f"{row[0]} ({row[1]}): {row[2]} transactions | INR {row[3]:,.2f}")
        export_query(connection, "customer_spend.csv", customer_spend)

        channel_query = """
            SELECT channel, COUNT(*) AS total_transactions,
                   SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed_transactions,
                   ROUND(100.0 * SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) / COUNT(*), 1) AS completion_rate_pct
            FROM transactions GROUP BY channel ORDER BY completion_rate_pct DESC
        """
        print("\nPAYMENT CHANNEL PERFORMANCE")
        for row in connection.execute(channel_query):
            print(f"{row[0]}: {row[2]}/{row[1]} completed | {row[3]}% completion")
        export_query(connection, "channel_performance.csv", channel_query)

        monthly_query = """
            SELECT substr(transaction_date, 1, 7) AS month,
                   COUNT(*) AS total_transactions,
                   SUM(CAST(amount_inr AS REAL)) AS total_amount_inr
            FROM transactions GROUP BY month ORDER BY month
        """
        print("\nMONTHLY TRANSACTION TREND")
        for row in connection.execute(monthly_query):
            print(f"{row[0]}: {row[1]} transactions | INR {row[2]:,.2f}")
        export_query(connection, "monthly_trend.csv", monthly_query)

        above_average_query = """
            WITH customer_totals AS (
                SELECT customer_id, SUM(CAST(amount_inr AS REAL)) AS completed_spend
                FROM transactions WHERE status = 'Completed' GROUP BY customer_id
            )
            SELECT c.customer_name, ROUND(ct.completed_spend, 2) AS completed_spend_inr
            FROM customer_totals ct JOIN customers c ON c.customer_id = ct.customer_id
            WHERE ct.completed_spend > (SELECT AVG(completed_spend) FROM customer_totals)
            ORDER BY completed_spend DESC
        """
        print("\nCUSTOMERS ABOVE AVERAGE COMPLETED SPEND")
        for row in connection.execute(above_average_query):
            print(f"{row[0]}: INR {row[1]:,.2f}")

    print(f"\nDone. CSV reports are in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
