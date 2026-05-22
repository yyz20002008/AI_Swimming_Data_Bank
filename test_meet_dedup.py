from supabase import create_client
import os
from collections import Counter

sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

# 1. Check duplicate meets
print('Checking duplicate meets...')
meets_resp = sb.table('meets').select('name, start_date').execute().data
meet_keys = [f"{m['name']} | {m['start_date']}" for m in meets_resp]
dup_meets = [k for k, v in Counter(meet_keys).items() if v > 1]
if dup_meets:
    print(f'FOUND {len(dup_meets)} DUPLICATE MEETS:')
    for d in dup_meets[:5]:
        print('  ', d)
else:
    print(f'Checked {len(meets_resp)} meets. NO duplicates found!')

# 2. Check total individual results
print('\nChecking total individual results...')
res_count = sb.table('individual_results').select('id', count='exact').execute().count
print(f'Total results: {res_count}')

