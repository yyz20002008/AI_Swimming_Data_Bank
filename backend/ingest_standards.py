import os
import urllib.request
import csv
from io import StringIO
from supabase import create_client

sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

# 1. Fetch Events Map
evts = sb.table('events').select('id, distance, stroke').execute().data
stroke_map = {
    'fr': 'Freestyle',
    'bk': 'Backstroke',
    'br': 'Breaststroke',
    'fl': 'Butterfly',
    'im': 'Individual Medley'
}

def get_event_id(dist, strk):
    mapped_stroke = stroke_map.get(strk.lower())
    for e in evts:
        if e['distance'] == int(dist) and e['stroke'] == mapped_stroke:
            return e['id']
    return None

# 2. Download CSV
print("Downloading USA Swimming Standards CSV...")
url = "https://raw.githubusercontent.com/davidpacecode/usa_swimming_motivational_time_standards/main/usa_swimming_motivational_standards.csv"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response:
    content = response.read().decode('utf-8')

# 3. Parse and Upload
print("Parsing and uploading...")
reader = csv.DictReader(StringIO(content))

batch = []
for row in reader:
    if row['standard_type'] != 'single_age':
        continue
    
    dist = row['distance']
    strk = row['stroke']
    event_id = get_event_id(dist, strk)
    
    if not event_id:
        continue
        
    gender = 'M' if row['gender'] == 'boys' else 'F'
    course = row['course'].upper()
    age = int(row['age'])
    
    def parse_time(val):
        return float(val) if val and val.strip() else None
        
    b = parse_time(row['b'])
    if not b: continue # skip if no standards
    
    batch.append({
        'event_id': event_id,
        'gender': gender,
        'course': course,
        'age': age,
        'b_time': b,
        'bb_time': parse_time(row['bb']),
        'a_time': parse_time(row['a']),
        'aa_time': parse_time(row['aa']),
        'aaa_time': parse_time(row['aaa']),
        'aaaa_time': parse_time(row['aaaa'])
    })

print(f"Prepared {len(batch)} records. Pushing to Supabase...")

# We have to clear the table first or just upsert.
# Since we might run this multiple times, let's delete all first.
sb.table('usa_swimming_standards').delete().neq('age', 0).execute()

# Insert in chunks of 500
for i in range(0, len(batch), 500):
    chunk = batch[i:i+500]
    sb.table('usa_swimming_standards').insert(chunk).execute()
    print(f"Inserted {len(chunk)} records...")

print("Done!")
