from supabase import create_client
import os
from collections import Counter

sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

print('--- DATA VERIFICATION ---')

# Check for duplicate USS IDs (excluding null)
print('\nChecking duplicate USS IDs...')
swimmers = sb.table('swimmers').select('uss_id').execute().data
uss_ids = [s['uss_id'] for s in swimmers if s['uss_id']]
dups = [k for k, v in Counter(uss_ids).items() if v > 1]
if dups:
    print(f'Found {len(dups)} duplicate USS IDs!')
else:
    print('No duplicate USS IDs found. (Deduplication SUCCESS)')

# Check for teams with name starting with MD
teams_resp = sb.table('teams').select('code, name').like('name', 'MD%').execute()
if teams_resp.data:
    print(f'\nFound {len(teams_resp.data)} teams still starting with MD in name (likely bugs):')
    for t in teams_resp.data[:5]:
        print(f"  {t['code']}: {t['name']}")
else:
    print('\nNo team names starting with MD prefix found (fixed!).')

# Check if ages are populated
null_age_count = sb.table('individual_results').select('id', count='exact').is_('age', 'null').execute().count
total_results = sb.table('individual_results').select('id', count='exact').execute().count
print(f'\nAge check: {null_age_count} / {total_results} results have NULL age.')

# Check materialized views
mv_count = sb.table('mv_swimmer_best_times').select('swimmer_id', count='exact').execute().count
print(f'\nmv_swimmer_best_times rows: {mv_count}')
