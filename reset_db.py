from supabase import create_client
import os

sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

# Delete all meets (cascades to individual_results)
meets = sb.table('meets').select('id').execute()
for m in meets.data:
    sb.table('meets').delete().eq('id', m['id']).execute()

# Delete all swimmers
swimmers = sb.table('swimmers').select('id').execute()
for s in swimmers.data:
    sb.table('swimmers').delete().eq('id', s['id']).execute()

# Delete all teams
teams = sb.table('teams').select('id').execute()
for t in teams.data:
    sb.table('teams').delete().eq('id', t['id']).execute()

print('Database cleared.')
