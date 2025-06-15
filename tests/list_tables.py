from sqlalchemy import create_engine, text, inspect
import pandas as pd

# Use the same connection from db_connection.py
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/knowthee"
engine = create_engine(DATABASE_URL)

# Method 1: Using SQL Query
print("Method 1: Using SQL Query")
with engine.connect() as conn:
    # Get tables with their row counts
    query = text("""
        SELECT 
            table_name,
            (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count,
            pg_stat_get_live_tuples(quote_ident(table_name)::regclass) as row_count
        FROM information_schema.tables t
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    result = conn.execute(query)
    
    print("\nTables with their statistics:")
    print("------------------------------")
    for row in result:
        print(f"Table: {row.table_name}")
        print(f"Columns: {row.column_count}")
        print(f"Approximate rows: {row.row_count}")
        print("------------------------------")

# Method 2: Using SQLAlchemy Inspector
print("\nMethod 2: Using SQLAlchemy Inspector")
inspector = inspect(engine)
tables = inspector.get_table_names()

for table in tables:
    # Get column information
    columns = inspector.get_columns(table)
    print(f"\nTable: {table}")
    print("Columns:")
    for col in columns:
        print(f"- {col['name']} ({col['type']})")
    
    # Get primary key information
    pk = inspector.get_pk_constraint(table)
    if pk['constrained_columns']:
        print(f"Primary Key: {', '.join(pk['constrained_columns'])}")
    
    # Get foreign key information
    fks = inspector.get_foreign_keys(table)
    if fks:
        print("Foreign Keys:")
        for fk in fks:
            print(f"- {', '.join(fk['constrained_columns'])} -> {fk['referred_table']}.{', '.join(fk['referred_columns'])}")

# Method 3: Preview first few rows of each table
print("\nMethod 3: Preview of table contents")
for table in tables:
    print(f"\nPreview of {table}:")
    print("-" * (len(table) + 11))
    try:
        query = text(f"SELECT * FROM {table} LIMIT 3")
        df = pd.read_sql(query, engine)
        print(df)
    except Exception as e:
        print(f"Could not preview table: {str(e)}") 