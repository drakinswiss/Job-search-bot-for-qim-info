import pandas as pd
import numpy as np
from datetime import datetime
import re

print("Loading data...")
df_swissdev = pd.read_csv('all_swissdevjobs.csv')
df_ict = pd.read_excel('ictjobs_scraped_data.xlsx')
df_linked = pd.read_excel('linkedin_jobs.xlsx')

# Standard Schema
output_cols = [
    'Company Name', 'Website', 'Job Title', 'Location (Canton/City)',
    'Matched Tech & Skills', 'Date Posted', 'Days Active', 'Contact Point',
    'Direct Job URL', 'Company size'
]

# 1. Map swissdevjobs
print("Processing swissdevjobs...")
df1 = pd.DataFrame(columns=output_cols)
df1['Company Name'] = df_swissdev['company']
df1['Website'] = df_swissdev.get('companyWebsiteLink', np.nan)
df1['Job Title'] = df_swissdev['name']

# Combine actualCity and address for location
def get_loc1(row):
    parts = [str(row.get('actualCity', '')), str(row.get('address', ''))]
    return ', '.join([p for p in parts if p != 'nan' and p.strip()])
df1['Location (Canton/City)'] = df_swissdev.apply(get_loc1, axis=1)

df1['Date Posted'] = pd.to_datetime(df_swissdev.get('activeFrom', np.nan), errors='coerce', utc=True).dt.tz_localize(None)
# Calculate Days Active
now = datetime.now()
df1['Days Active'] = (now - df1['Date Posted']).dt.days

# Contact point
def get_contact1(row):
    parts = [str(row.get('candidateContactWay', '')), str(row.get('personEmail', ''))]
    filtered = [p for p in parts if p != 'nan' and p.strip()]
    return ', '.join(filtered) if filtered else np.nan
df1['Contact Point'] = df_swissdev.apply(get_contact1, axis=1)

df1['Direct Job URL'] = df_swissdev.get('jobUrl', df_swissdev.get('redirectJobUrl'))
df1['Company size'] = df_swissdev.get('companySize', np.nan)

# Extract tech text for filtering (combine title, technologies, etc.)
df1['_desc'] = df_swissdev['name'].fillna('') + ' ' + df_swissdev.get('technologies', '').fillna('') + ' ' + df_swissdev.get('techCategory', '').fillna('')

# 2. Map ictjobs
print("Processing ictjobs...")
df2 = pd.DataFrame(columns=output_cols)
df2['Company Name'] = df_ict['Company']
df2['Website'] = df_ict.get('Company URL', np.nan)
df2['Job Title'] = df_ict['Job Title']
df2['Location (Canton/City)'] = df_ict.get('Location', np.nan)
df2['Date Posted'] = pd.to_datetime(df_ict.get('Date Posted', np.nan), errors='coerce', utc=True).dt.tz_localize(None)
df2['Days Active'] = pd.to_numeric(df_ict.get('Days Available', np.nan), errors='coerce')
df2['Direct Job URL'] = df_ict.get('Job URL', np.nan)
df2['_desc'] = df_ict['Job Title'].fillna('') + ' ' + df_ict.get('Description', '').fillna('')

# 3. Map linkedin
print("Processing linkedin...")
df3 = pd.DataFrame(columns=output_cols)
df3['Company Name'] = df_linked['Company']
df3['Job Title'] = df_linked['Job Title']
df3['Location (Canton/City)'] = df_linked.get('Location', np.nan)
df3['Date Posted'] = pd.to_datetime(df_linked.get('Date Posted', np.nan), errors='coerce', utc=True).dt.tz_localize(None)
# computing days active
df3['Days Active'] = (now - df3['Date Posted']).dt.days
df3['Contact Point'] = df_linked.get('Contact Point', np.nan)
df3['Direct Job URL'] = df_linked.get('Job URL', np.nan)
df3['_desc'] = df_linked['Job Title'].fillna('') + ' ' + df_linked.get('Description', '').fillna('')

# Combine all
print("Concatenating data...")
df_all = pd.concat([df1, df2, df3], ignore_index=True)

# Format Date Posted to string YYYY-MM-DD
df_all['Date Posted'] = df_all['Date Posted'].dt.strftime('%Y-%m-%d')

# Filter logic
german_locs = ['zurich', 'zürich', 'bern', 'luzern', 'lucerne', 'st. gallen', 'st gallen', 'basel', 'winterthur', 'aargau', 'zug', 'schwyz', 'thurgau', 'solothurn', 'schaffhausen', 'chur', 'aarau', 'frauenfeld', 'liestal', 'baden', 'olten', 'langenthal', 'thun', 'biel', 'bienne', 'schweiz', 'switzerland']
french_italian_locs = ['geneva', 'genève', 'lausanne', 'vaud', 'neuchâtel', 'neuchatel', 'ticino', 'lugano', 'locarno', 'bellinzona', 'fribourg', 'valais', 'sion', 'martigny', 'vevey', 'yverdon', 'nyon', 'morges']

tech_tools_base = [
    'dynatrace', 'splunk', 'grafana', 'jmeter', 'gatling', 'tricentis', 'tosca', 
    'neoload', 'octoperf', 'datadog', 'prometheus', 'opentelemetry', 'appdynamics', 
    'new relic', 'cloudwatch', 'azure monitor', 'k6', 'cloud', 'kubernetes', 'k8s', 'linux'
]

roles_base = [
    'performance engineer', 'site reliability engineer', 'sre', 'devops', 
    'performance tester', 'load tester', 'qa automation', 'system architect', 
    'system engineer', 'systems engineer',
    'systemingenieur', 'softwareentwickler', 'entwickler', 'systemarchitekt', 
    'automatisierungsingenieur', 'testingenieur', 'spezialist', 'experte'
]

exclusions_base = ['sales', 'marketing', 'recruiter', 'hr', 'financial', 'athlete', 'coach', 'seo']

def generate_variations(word_list):
    variations = set()
    for word in word_list:
        variations.add(word)
        if ' ' in word:
            variations.add(word.replace(' ', ''))
            variations.add(word.replace(' ', '-'))
    return list(variations)

tech_tools = generate_variations(tech_tools_base)
roles = generate_variations(roles_base)
exclusions = generate_variations(exclusions_base)

def get_matched_tech(title, desc):
    title_lower = str(title).lower() if not pd.isna(title) else ''
    text_lower = str(desc).lower() if not pd.isna(desc) else ''
    full_text = title_lower + ' ' + text_lower
    
    def check_match(term, text):
        if len(term) <= 4:
            return bool(re.search(r'\b' + re.escape(term) + r'\b', text))
        return term in text

    # NOT exclusion
    for ex in exclusions:
        if check_match(ex, title_lower):
            return ''
            
    # Match Roles (OR)
    role_matched = False
    for role in roles:
        if check_match(role, full_text): 
            role_matched = True
            break
            
    # Match Tools (OR)
    matched_tools = []
    for tool in tech_tools:
        if check_match(tool, full_text):
            # to avoid listing 'qaautomation' in the output, we map back to the original word or just keep the matched string
            # It's fine to output the variation matched. Or we can just output the tool.
            matched_tools.append(tool)
            
    if role_matched and len(matched_tools) > 0:
        return ', '.join(set(matched_tools))
    return ''

def is_german_swiss(loc):
    if not isinstance(loc, str):
        return False # Assume false if no loc, or True? Let's say False to be safe
    loc_lower = loc.lower()
    
    # Exclude french/italian first
    if any(fl in loc_lower for fl in french_italian_locs):
        return False
        
    # Check if there's any german location match
    if any(gl in loc_lower for gl in german_locs):
        return True
    
    return False

df_all['Matched Tech & Skills'] = df_all.apply(lambda row: get_matched_tech(row.get('Job Title', ''), row.get('_desc', '')), axis=1)
df_all['Is_Germanic'] = df_all['Location (Canton/City)'].apply(is_german_swiss)

# Filter out empty tech matches and non-germanic locations
filtered_df = df_all[(df_all['Matched Tech & Skills'] != '') & (df_all['Is_Germanic'] == True)].copy()

# Drop temp columns
filtered_df = filtered_df[output_cols]

# Deduplicate essentially based on Company and Job Title
filtered_df = filtered_df.drop_duplicates(subset=['Company Name', 'Job Title'], keep='first')

output_file = 'german_swiss_qim_leads_v4.xlsx'
filtered_df.to_excel(output_file, index=False)
print(f"Done! {len(filtered_df)} leads extracted and saved to {output_file}.")
