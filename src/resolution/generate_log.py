import pandas as pd
import os
import sys

# Ensure the root directory is in the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.resolution.entity_mapper import EntityResolver
from src.exporter import DataExporter

def generate_mapping_log():
    input_path = os.path.join("data", "output", "1_Startups.csv")
    
    if not os.path.exists(input_path):
        print(f"[-] Input file {input_path} not found. Please run startups_fetcher first.")
        return

    print("[*] Loading raw startups dataset...")
    df = pd.read_csv(input_path)
    
    # We only need to map the unique raw names
    raw_names = df['content.entityName'].dropna().unique()
    
    print(f"[*] Found {len(raw_names)} unique raw startup names. Passing through Entity Resolver...")
    
    resolver = EntityResolver()
    mapping_log = []
    
    mapped_count = 0
    for raw_name in raw_names:
        # Pass the messy scraped name through our RapidFuzz canonicalization engine
        canonical_name, is_mapped, score = resolver.resolve(str(raw_name))
        
        mapping_log.append({
            "Raw Name": raw_name,
            "Canonical Name": canonical_name if is_mapped else "UNMAPPED",
            "Confidence Score": round(score, 2),
            "Status": "MAPPED" if is_mapped else "NEW ENTITY"
        })
        
        if is_mapped:
            mapped_count += 1
            
    print(f"[+] Canonicalization complete! Mapped {mapped_count} entities to the known seed database.")
    
    print("[*] Exporting to CSV...")
    exporter = DataExporter()
    exporter.export_entity_mapping_log(mapping_log)
    print("[+] Done! '6_Entity_Mapping_Log.csv' is ready for Google Sheets.")

if __name__ == "__main__":
    generate_mapping_log()

