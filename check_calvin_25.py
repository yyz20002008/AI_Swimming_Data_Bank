import os
from supabase import create_client

sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

# Find Calvin Yang
swimmers = sb.table('swimmers').select('id, first_name, last_name, birth_date').ilike('first_name', '%Calvin%').ilike('last_name', '%Yang%').execute()
if not swimmers.data:
    print('Calvin Yang not found!')
    exit()

swimmer = swimmers.data[0]
print(f"Found: {swimmer['first_name']} {swimmer['last_name']} (DOB: {swimmer['birth_date']})")

# Fetch all his results that are 25 Distance
results = sb.table('individual_results') \
    .select('finals_time, age, meet_id, event_id, events(distance, stroke)') \
    .eq('swimmer_id', swimmer['id']) \
    .execute()

print(f"Total results: {len(results.data)}")

# Filter for 25s
res_25 = [r for r in results.data if r['events']['distance'] == 25]
print(f"Total 25s: {len(res_25)}")

if len(res_25) > 0:
    meet_ids = list(set([r['meet_id'] for r in res_25]))
    meets = sb.table('meets').select('id, name, start_date').in_('id', meet_ids).execute()
    meet_map = {m['id']: m for m in meets.data}
    
    print("\n25 Events Details:")
    for r in res_25:
        m = meet_map.get(r['meet_id'], {})
        print(f"Date: {m.get('start_date')}, Meet: {m.get('name')}, Event: 25 {r['events']['stroke']}, Time: {r['finals_time']}")

