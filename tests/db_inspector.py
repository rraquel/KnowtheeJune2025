import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'knowthee')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD')

if not DB_PASSWORD:
    raise ValueError("Database password not found in environment variables. Please check your .env file.")

# Create database connection string
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

def inspect_database():
    """Inspect the database structure and content."""
    try:
        with engine.connect() as conn:
            print("✅ Successfully connected to the database!")
            
            # List all tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            
            print("\n📊 Tables in the database:")
            for table in tables:
                print(f"\nTable: {table}")
                
                # Get column information
                columns = conn.execute(text(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = '{table}'
                """))
                
                print("Columns:")
                for col in columns:
                    print(f"  - {col[0]}: {col[1]} ({'nullable' if col[2] == 'YES' else 'not nullable'})")
                
                # Get row count
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"Row count: {count}")
                
                # Show sample data
                if count > 0:
                    sample = conn.execute(text(f"SELECT * FROM {table} LIMIT 5")).fetchall()
                    print("\nSample data:")
                    for row in sample:
                        print(f"  {row}")
                
    except Exception as e:
        print(f"❌ Error connecting to database: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Make sure PostgreSQL is running in Docker")
        print("2. Check your .env file has the correct credentials")
        print("3. Verify the database exists")
        print("4. Check if the port is accessible")

if __name__ == "__main__":
    inspect_database() 