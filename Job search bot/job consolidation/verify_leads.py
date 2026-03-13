import pandas as pd
df = pd.read_excel('german_swiss_qim_leads.xlsx')
with open('verification.txt', 'w', encoding='utf-8') as f:
    f.write(f"Total Leads: {len(df)}\n")
    f.write(f"Columns: {', '.join(df.columns)}\n\n")
    for idx, row in df.head(5).iterrows():
        f.write(f"--- Lead {idx+1} ---\n")
        f.write(f"Company: {row['Company Name']}\n")
        f.write(f"Job Title: {row['Job Title']}\n")
        f.write(f"Location: {row['Location (Canton/City)']}\n")
        f.write(f"Skills: {row['Matched Tech & Skills']}\n")
        f.write(f"Date Posted: {row['Date Posted']}\n")
        f.write(f"Days Active: {row['Days Active']}\n")
        f.write(f"Direct Job URL: {row['Direct Job URL']}\n\n")
