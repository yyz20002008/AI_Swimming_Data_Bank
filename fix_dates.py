import os
import glob
from supabase import create_client

sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

def _format_date(date_str):
    if not date_str or not date_str.strip() or len(date_str.strip()) != 8:
        return None
    date_str = date_str.strip()
    return f"{date_str[4:8]}-{date_str[0:2]}-{date_str[2:4]}"

def _s(s, start, end):
    return s[start:end].strip()

files = glob.glob('data/raw/**/*.cl2', recursive=True)
print(f"Found {len(files)} CL2 files to scan.")

updates = 0
for file in files:
    with open(file, 'r', encoding='latin-1') as f:
        lines = f.readlines()
        
    meet_name = None
    start_date = None
    
    for line in lines:
        if line.startswith('B1'):
            meet_name = _s(line, 11, 41)
            raw_date = _s(line, 121, 129)
            start_date = _format_date(raw_date)
            break
            
    if not meet_name:
        for line in lines:
            if line.startswith('C1'):
                meet_name = _s(line, 11, 41)
                break
                
    if meet_name and start_date:
        # Check if the meet exists with the wrong date
        res = sb.table('meets').select('id, start_date').eq('name', meet_name).execute().data
        for m in res:
            if m['start_date'] == '2024-01-01':
                sb.table('meets').update({'start_date': start_date}).eq('id', m['id']).execute()
                print(f"Updated {meet_name} -> {start_date}")
                updates += 1

print(f"Fixed {updates} meets!")
