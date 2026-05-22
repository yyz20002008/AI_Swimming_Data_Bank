from supabase import create_client
import os

sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

print('Deleting individual_results...')
sb.table('individual_results').delete().neq('id', -1).execute()

print('Deleting meets...')
sb.table('meets').delete().neq('id', -1).execute()

print('Deleting swimmers...')
sb.table('swimmers').delete().neq('id', -1).execute()

print('Deleting teams...')
sb.table('teams').delete().neq('id', -1).execute()

print('Database cleared.')
