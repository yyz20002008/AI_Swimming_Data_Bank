import os
from supabase import create_client
sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])
meets = sb.table('meets').select('id, name, start_date').limit(10).execute()
print('Meets table start_dates:')
for m in meets.data:
    print(f"{m['name']}: {m['start_date']}")
