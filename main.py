import os
import argparse
import shutil
from datetime import datetime
from pathlib import Path

from prepare_dataset import prepare_xml
from patch_kraken_xml import patch_for_kraken
from validate_xml import validate_page_xml

def process_dataset(input_dir, output_dir, xsd_path, quarantine_dir):
    in_path = Path(input_dir)
    out_path = Path(output_dir)
    xsd_file = Path(xsd_path)
    quarantine_path = Path(quarantine_dir)
    
    # Naplófájl útvonala a karantén mappán belül
    log_file_path = quarantine_path / "quarantine_report.txt"

    print(f"=== HTR XML Előkészítő Keretrendszer (Naplózással) ===")
    print(f"Forrás mappa:   {in_path}")
    print(f"Cél mappa:      {out_path}")
    print(f"Karantén mappa: {quarantine_path}")
    print(f"XSD Séma:       {xsd_file}")
    print("======================================================\n")

    if not xsd_file.exists():
        print(f"[KRITIKUS HIBA] Nem található a sémafájl: {xsd_file}")
        return

    out_path.mkdir(parents=True, exist_ok=True)
    quarantine_path.mkdir(parents=True, exist_ok=True)

    xml_files = list(in_path.glob("*.xml"))
    if not xml_files:
        print(f"Nem találhatók XML fájlok a(z) {in_path} mappában.")
        return

    print(f"Összesen {len(xml_files)} XML fájl feldolgozása indul...\n")

    success_count = 0
    warning_count = 0
    error_count = 0

    # Naplófájl megnyitása írásra (minden futásnál újat kezdünk)
    with open(log_file_path, "w", encoding="utf-8") as log_file:
        log_file.write(f"--- Karantén Napló ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---\n\n")

        for xml_file in xml_files:
            target_file = out_path / xml_file.name
            print(f"--- Feldolgozás: {xml_file.name} ---")

            try:
                # 1-2. Tisztítás és Kraken Baseline generálás
                prepare_xml(str(xml_file), str(target_file))
                patch_for_kraken(str(target_file), str(target_file))

                # 3. Validáció
                is_valid, errors = validate_page_xml(str(target_file), str(xsd_file))

                if is_valid:
                    success_count += 1
                else:
                    warning_count += 1
                    print(f"  [!] Validációs hiba! Fájl áthelyezése a karanténba: {xml_file.name}")
                    
                    # Hiba naplózása a txt fájlba
                    log_file.write(f"[ÉRVÉNYTELEN SÉMA] Fájl: {xml_file.name}\n")
                    for err in errors:
                        log_file.write(f"  - {err}\n")
                    log_file.write("\n")
                    
                    # Fájl mozgatása a karanténba
                    shutil.move(str(target_file), str(quarantine_path / xml_file.name))

            except Exception as e:
                error_count += 1
                print(f"  [X] Végzetes hiba ({xml_file.name}): {e}")
                
                # Kritikus hiba naplózása
                log_file.write(f"[FELDOLGOZÁSI HIBA] Fájl: {xml_file.name}\n")
                log_file.write(f"  - {e}\n\n")
                
                if target_file.exists():
                    shutil.move(str(target_file), str(quarantine_path / xml_file.name))

        log_file.write(f"--- Futtatás vége. Összesen {warning_count + error_count} fájl került karanténba. ---\n")

    print(f"\n=== FELDOLGOZÁS VÉGE ===")
    print(f"Összes fájl:        {len(xml_files)}")
    print(f"Hibátlan (Valid):   {success_count} -> {out_path.absolute()}")
    print(f"Karanténba került:  {warning_count + error_count} -> {quarantine_path.absolute()}")
    if (warning_count + error_count) > 0:
        print(f"Részletes hibanapló: {log_file_path.absolute()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Univerzális XML Pipeline HTR Tanításhoz")
    parser.add_argument("-i", "--input", required=True, help="Forrás XML mappa (pl. raw_xml/)")
    parser.add_argument("-o", "--output", default="clean_xml", help="Kimeneti mappa a javított fájloknak")
    parser.add_argument("-q", "--quarantine", default="quarantine_xml", help="Mappa a hibás fájloknak")
    parser.add_argument("-x", "--xsd", default="pagexml/pagecontent.xsd", help="A PAGE XML XSD séma útvonala")
    
    args = parser.parse_args()
    
    process_dataset(args.input, args.output, args.xsd, args.quarantine)