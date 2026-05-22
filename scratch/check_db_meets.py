import os
from dotenv import load_dotenv
from supabase import create_client
from collections import Counter

load_dotenv()
sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

r = sb.table('meets').select('id, name, start_date, season, source_file').execute()
meets = r.data
print(f"Total meets in DB: {len(meets)}")

# Count by source_file
source_files = [m.get('source_file') for m in meets]
c_files = Counter(source_files)
print("\nMeets by source file:")
for file, count in c_files.items():
    print(f"  {file}: {count}")

# Count by season
c_seasons = Counter(m.get('season') for m in meets)
print("\nMeets by season tag in DB:")
for season, count in c_seasons.items():
    print(f"  {season}: {count}")
