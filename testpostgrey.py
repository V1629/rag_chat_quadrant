import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
 
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
print(f'Testing connection to: {DATABASE_URL}')
 
try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text('SELECT version();'))
        version = result.fetchone()[0]
        print(f'✅ Connection successful!')
        print(f'PostgreSQL version: {version[:50]}...')
except Exception as e:
    print(f'❌ Connection failed: {e}')