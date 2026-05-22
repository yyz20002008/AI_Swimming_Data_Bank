from supabase import create_client
import os

sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])
resp = sb.table('teams').select('id, code, name').execute()

for t in resp.data:
    name = t['name']
    if name and ' ' in name:
        parts = name.split(' ', 1)
        if len(parts[0]) <= 6 and parts[0].isupper() and (parts[0] == t['code'] or parts[0].startswith('MD')):
            new_name = parts[1].strip()
            print(f'Updating {name} -> {new_name}')
            sb.table('teams').update({'name': new_name}).eq('id', t['id']).execute()
