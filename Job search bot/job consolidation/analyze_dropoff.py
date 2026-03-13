import pandas as pd
import re

df_swissdev = pd.read_csv('all_swissdevjobs.csv')
df_ict = pd.read_excel('ictjobs_scraped_data.xlsx')
df_linked = pd.read_excel('linkedin_jobs.xlsx')

with open('dropoff_utf8.txt', 'w', encoding='utf-8') as f:
    f.write(f"Raw swissdevjobs counts: {len(df_swissdev)}\n")
    f.write(f"Raw ictjobs counts: {len(df_ict)}\n")
    f.write(f"Raw linkedin counts: {len(df_linked)}\n")
    f.write(f"Total raw leads: {len(df_swissdev) + len(df_ict) + len(df_linked)}\n\n")

    # --- Reproduction of filtering logic ---
    df1 = pd.DataFrame()
    df1['Location'] = df_swissdev.apply(lambda row: ', '.join([p for p in [str(row.get('actualCity', '')), str(row.get('address', ''))] if p != 'nan' and p.strip()]), axis=1)
    df1['_desc'] = df_swissdev['name'].fillna('') + ' ' + df_swissdev.get('technologies', '').fillna('') + ' ' + df_swissdev.get('techCategory', '').fillna('')

    df2 = pd.DataFrame()
    df2['Location'] = df_ict.get('Location', pd.Series(dtype=str))
    df2['_desc'] = df_ict['Job Title'].fillna('') + ' ' + df_ict.get('Description', '').fillna('')

    df3 = pd.DataFrame()
    df3['Location'] = df_linked.get('Location', pd.Series(dtype=str))
    df3['_desc'] = df_linked['Job Title'].fillna('') + ' ' + df_linked.get('Description', '').fillna('')

    df_all = pd.concat([df1, df2, df3], ignore_index=True)

    german_locs = ['zurich', 'zürich', 'bern', 'luzern', 'lucerne', 'st. gallen', 'st gallen', 'basel', 'winterthur', 'aargau', 'zug', 'schwyz', 'thurgau', 'solothurn', 'schaffhausen', 'chur', 'aarau', 'frauenfeld', 'liestal', 'baden', 'olten', 'langenthal', 'thun', 'biel', 'bienne', 'schweiz', 'switzerland']
    french_italian_locs = ['geneva', 'genève', 'lausanne', 'vaud', 'neuchâtel', 'neuchatel', 'ticino', 'lugano', 'locarno', 'bellinzona', 'fribourg', 'valais', 'sion', 'martigny', 'vevey', 'yverdon', 'nyon', 'morges']
    tech_tools = ['dynatrace', 'splunk', 'grafana', 'jmeter', 'gatling', 'tricentis', 'tosca', 'neoload', 'octoperf', 'datadog', 'prometheus', 'opentelemetry', 'appdynamics', 'new relic', 'cloudwatch', 'azure monitor', 'k6']
    roles = ['performance engineer', 'site reliability engineer', 'sre', 'devops', 'performance tester', 'load tester', 'qa automation', 'system architect']
    exclusions = ['sales', 'marketing', 'recruiter', 'hr', 'financial', 'athlete', 'coach', 'seo']
    
    def get_matched_tech(title, desc):
        title_lower = str(title).lower() if not pd.isna(title) else ''
        text_lower = str(desc).lower() if not pd.isna(desc) else ''
        full_text = title_lower + ' ' + text_lower
        
        # 3. NOT exclusion
        for ex in exclusions:
            if re.search(r'\b' + re.escape(ex) + r'\b', title_lower): # usually checking just title is safer for excludes to prevent false positives, but let's check full text if requested.
                return ''
                
        # 1. Match Roles (OR)
        role_matched = False
        for role in roles:
            if role in full_text: # Using simple 'in' since some are multi-word, or can use regex \b
                role_matched = True
                break
                
        # 2. Match Tools (OR)
        matched_tools = []
        for tool in tech_tools:
            if re.search(r'\b' + re.escape(tool) + r'\b', full_text):
                matched_tools.append(tool)
                
        if role_matched and len(matched_tools) > 0:
            return ', '.join(set(matched_tools))
        return ''

    def is_german_swiss(loc):
        if not isinstance(loc, str): return False
        loc_lower = loc.lower()
        if any(fl in loc_lower for fl in french_italian_locs): return False
        if any(gl in loc_lower for gl in german_locs): return True
        return False

    df_all['Matched Tech'] = df_all.apply(lambda row: get_matched_tech(row.get('Job Title', ''), row.get('_desc', '')), axis=1)
    df_all['Is_Germanic'] = df_all['Location'].apply(is_german_swiss)

    f.write(f"Total leads after concatenation: {len(df_all)}\n")

    has_tech = df_all[df_all['Matched Tech'] != '']
    is_german = df_all[df_all['Is_Germanic'] == True]
    has_both = df_all[(df_all['Matched Tech'] != '') & (df_all['Is_Germanic'] == True)]

    f.write(f"Leads with matching Tech/Keywords: {len(has_tech)}\n")
    f.write(f"Leads with Germanic Location: {len(is_german)}\n")
    f.write(f"Leads with BOTH (Before deduplication): {len(has_both)}\n")

    final_df = pd.read_excel('german_swiss_qim_leads.xlsx')
    f.write(f"Final deduplicated leads (german_swiss_qim_leads.xlsx): {len(final_df)}\n")
