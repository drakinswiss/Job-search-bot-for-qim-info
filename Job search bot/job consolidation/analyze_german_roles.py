import pandas as pd
import re

print("Loading data for German role analysis...")
df_swissdev = pd.read_csv('all_swissdevjobs.csv')
df_ict = pd.read_excel('ictjobs_scraped_data.xlsx')
df_linked = pd.read_excel('linkedin_jobs.xlsx')

# Combine all descriptions and titles
titles = []
descriptions = []

# Swissdev
titles.extend(df_swissdev['name'].dropna().tolist())
descriptions.extend(df_swissdev['technologies'].dropna().tolist())
descriptions.extend(df_swissdev['techCategory'].dropna().tolist())

# ICT
titles.extend(df_ict['Job Title'].dropna().tolist())
descriptions.extend(df_ict['Description'].dropna().tolist())

# LinkedIn
titles.extend(df_linked['Job Title'].dropna().tolist())
descriptions.extend(df_linked['Description'].dropna().tolist())

all_text = []
for t, d in zip(titles, descriptions):
    all_text.append(str(t).lower() + ' ' + str(d).lower())

tech_tools = ['dynatrace', 'splunk', 'grafana', 'jmeter', 'gatling', 'tricentis', 'tosca', 'neoload', 'octoperf', 'datadog', 'prometheus', 'opentelemetry', 'appdynamics', 'new relic', 'cloudwatch', 'azure monitor', 'k6']

# Find titles of jobs that mention the tools, but where the title MIGHT be in German
german_keywords = []

with open('german_role_analysis.txt', 'w', encoding='utf-8') as f:
    f.write("--- Job titles containing target tools (to spot German roles) ---\n")
    for idx, (title, full_text) in enumerate(zip(titles, all_text)):
        # If it has a tool
        if any(re.search(r'\b' + re.escape(tool) + r'\b', full_text) for tool in tech_tools):
            f.write(f"- {str(title).strip()}\n")

    f.write("\n\n--- Common technical German words found in tech job descriptions ---\n")
    # This is a basic analysis. We'll manually review the generated file for German equivalents
    f.write("Looking for things like: Entwickler, Ingenieur, Architekt, Systemadministrator, Tester, Qualitätssicherung, Leistung, Zuverlässigkeit...\n")
