#!/usr/bin/env python3
"""
Script to generate folder structure for iller from ptt_il_ilce_mahalle.json

Klasör adları scrape_ptt_address2.py çıktısındaki il_slug / ilce_slug ile üretilir
(eski JSON için il_adi / ilce_adi sanitize edilir).

Oluşturulan yapı:
- PTT/iller/iller.json (tüm iller; ilceler.json ile aynı kayıt biçimi: id, ad, isteğe bağlı slug)
- PTT/iller/{il_slug}/ilceler.json
- PTT/iller/{il_slug}/{ilce_slug}/mahalleler.json
"""

import json
from pathlib import Path


def sanitize_filename(name):
    """Sanitize filename to remove invalid characters"""
    # Replace invalid characters with underscore
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name.strip()


def il_folder_name(il):
    """PTT JSON il_slug; yoksa geriye dönük uyumluluk için il_adi sanitize."""
    slug = (il.get("il_slug") or "").strip()
    return slug if slug else sanitize_filename(il["il_adi"])


def ilce_folder_name(ilce):
    """PTT JSON ilce_slug; yoksa ilce_adi sanitize."""
    slug = (ilce.get("ilce_slug") or "").strip()
    return slug if slug else sanitize_filename(ilce["ilce_adi"])


def generate_iller_structure():
    """Generate folder structure from ptt_il_ilce_mahalle.json"""

    # Paths
    base_dir = Path(__file__).parent.parent.parent
    input_file = base_dir / "PTT" / "ptt_il_ilce_mahalle.json"
    iller_dir = base_dir / "PTT" / "iller"
    
    # Read the main JSON file
    print(f"Reading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Create iller directory if it doesn't exist
    iller_dir.mkdir(parents=True, exist_ok=True)

    # Tüm iller: ilceler.json ile aynı yapı (id, ad, varsa slug)
    iller_data = []
    for il in data:
        entry = {
            "il_id": il["il_id"],
            "il_adi": il["il_adi"],
        }
        if il.get("il_slug"):
            entry["il_slug"] = il["il_slug"]
        iller_data.append(entry)

    iller_file = iller_dir / "iller.json"
    with open(iller_file, "w", encoding="utf-8") as f:
        json.dump(iller_data, f, ensure_ascii=False, indent=4)
    print(f"Wrote {len(iller_data)} provinces to {iller_file}")

    # Process each il
    for il in data:
        il_adi = il["il_adi"]
        ilceler = il["ilceler"]
        il_slug = il_folder_name(il)
        il_dir = iller_dir / il_slug

        # Create il directory
        il_dir.mkdir(parents=True, exist_ok=True)
        print(f"Processing {il_adi} ({il_slug})...")

        # Create ilceler.json
        ilceler_data = []
        for ilce in ilceler:
            entry = {
                "ilce_id": ilce["ilce_id"],
                "ilce_adi": ilce["ilce_adi"],
            }
            if ilce.get("ilce_slug"):
                entry["ilce_slug"] = ilce["ilce_slug"]
            ilceler_data.append(entry)
        
        ilceler_file = il_dir / "ilceler.json"
        with open(ilceler_file, 'w', encoding='utf-8') as f:
            json.dump(ilceler_data, f, ensure_ascii=False, indent=4)
        
        # Process each ilce
        for ilce in ilceler:
            mahalleler = ilce.get("mahalleler", [])
            ilce_slug = ilce_folder_name(ilce)
            ilce_dir = il_dir / ilce_slug
            
            # Create ilce directory
            ilce_dir.mkdir(parents=True, exist_ok=True)
            
            # Create mahalleler.json
            mahalleler_file = ilce_dir / "mahalleler.json"
            with open(mahalleler_file, 'w', encoding='utf-8') as f:
                json.dump(mahalleler, f, ensure_ascii=False, indent=4)
        
        print(f"  Created {len(ilceler_data)} ilceler and their mahalleler")
    
    print(f"\nSuccessfully generated folder structure in {iller_dir}")


if __name__ == "__main__":
    generate_iller_structure()

