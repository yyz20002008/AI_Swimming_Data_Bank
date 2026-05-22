from supabase import create_client
import os

sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

swimmer = sb.table('swimmers').select('id, first_name, last_name, birth_date').eq('last_name', 'Yang').eq('first_name', 'Calvin').execute().data[0]
print('Calvin ID:', swimmer['id'])

res = sb.table('individual_results').select('id, finals_time, age, meets(start_date, name)').eq('swimmer_id', swimmer['id']).order('age', desc=False).execute().data
if res:
    print('Earliest records:')
    for r in res[:5]:
        print(f"  Age {r['age']}: {r['finals_time']}s at {r['meets']['start_date']} ({r['meets']['name']})")
else:
    print('No results found for Calvin Yang')
