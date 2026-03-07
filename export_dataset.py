import os
import csv
import random
import shutil
import argparse
from pathlib import Path
from lxml import etree

def export_trocr_dataset(
    source_xml_dir,
    source_crops_dir,
    output_dir,
    zip_output=False,
    train_ratio=0.8,
    val_ratio=0.1,
    allow_delete_existing=False,
):
    # Biztonságos mappa-összerendelés a bemeneti paraméterek alapján!
    source_xml = Path(source_xml_dir)
    source_crops = Path(source_crops_dir)
    out_dir = Path(output_dir)

    print(f"--- TrOCR Dataset Export Indítása ---")
    print(f"Forrás mappa (XML): {source_xml}")
    
    # 1. Kimeneti mappák ürítése és létrehozása
    if out_dir.exists() and any(out_dir.iterdir()):
        if not allow_delete_existing:
            raise RuntimeError(
                f"A kimeneti mappa nem ures es torlesre kerulne: {out_dir}. "
                "Hasznald a --force-delete kapcsolot, vagy engedelyezd a torlest a GUI-ban."
            )
        shutil.rmtree(out_dir)
    elif out_dir.exists() and allow_delete_existing:
        shutil.rmtree(out_dir)
    
    for split in ['train', 'val', 'test']:
        (out_dir / split).mkdir(parents=True, exist_ok=True)

    dataset_pairs = []

    # 2. XML fájlok beolvasása a mappából
    for xml_file in source_xml.glob("*.xml"):
        try:
            tree = etree.parse(str(xml_file))
            root = tree.getroot()
            
            print(f"Feldolgozás: {xml_file.name}")
            
            # JAVÍTÁS 1: A fájlnév eltérésének (imageFilename) helyi javítása
            page_elements = root.xpath('.//*[local-name()="Page"]')
            if page_elements:
                page_el = page_elements[0]
                expected_img_name = xml_file.stem + ".jpg"
                current_img_name = page_el.get('imageFilename')
                
                if current_img_name != expected_img_name:
                    page_el.set('imageFilename', expected_img_name)
                    tree.write(str(xml_file), encoding='utf-8', xml_declaration=True)
                    print(f"  [JAVÍTVA] XML imageFilename frissítve: '{current_img_name}' -> '{expected_img_name}'")

            # JAVÍTÁS 2: Névtér-független XML bejárás (Kraken + Transkribus)
            valid_lines = []
            for line in root.xpath('.//*[local-name()="TextLine"]'):
                valid_lines.append(line)

            # 3. Adatok kinyerése
            for line in valid_lines:
                line_id = line.get('id')
                unicode_el = line.xpath('.//*[local-name()="Unicode"]')
                
                if not unicode_el or not unicode_el[0].text or not unicode_el[0].text.strip():
                    continue
                    
                text = unicode_el[0].text.strip()
                
                if '[?]' in text:
                    continue

                crop_filename = f"{xml_file.stem}_{line_id}.jpg"
                crop_path = source_crops / crop_filename
                
                if crop_path.exists():
                    dataset_pairs.append({
                        'source_image': crop_path,
                        'file_name': crop_filename,
                        'text': text
                    })

        except Exception as e:
            print(f"Hiba az XML olvasásakor ({xml_file.name}): {e}")

    # 4. Adatok keverése és felosztása (Split)
    random.shuffle(dataset_pairs)
    total = len(dataset_pairs)
    
    if total == 0:
        print("Nem található megfelelő adat az exportáláshoz a megadott mappában!")
        return

    train_end = int(total * train_ratio)
    val_end = train_end + int(total * val_ratio)

    splits = {
        'train': dataset_pairs[:train_end],
        'val': dataset_pairs[train_end:val_end],
        'test': dataset_pairs[val_end:]
    }

    print(f"\nSikeresen kinyerve: Összesen {total} db sor")

    # 5. CSV fájlok generálása (metadata.csv) és képek másolása
    for split_name, pairs in splits.items():
        split_dir = out_dir / split_name
        
        # JAVÍTÁS 3: Itt történik a varázslat - metadata.csv néven mentjük!
        csv_path = split_dir / "metadata.csv" 
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['file_name', 'text']) # A Hugging Face ezt a két oszlopot keresi
            
            for item in pairs:
                shutil.copy2(item['source_image'], split_dir / item['file_name'])
                writer.writerow([item['file_name'], item['text']])
                
        print(f" - {split_name.upper()} halmaz: {len(pairs)} db kép és metadata.csv elkészült.")

    # 6. Opcionális ZIP csomagolás Colab-hoz
    if zip_output:
        print("\nZIP fájl generálása a Colab-hoz...")
        zip_path = Path(str(out_dir) + "_gt")
        shutil.make_archive(str(zip_path), 'zip', str(out_dir))
        print(f"ZIP elkészült: {zip_path}.zip")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TrOCR Dataset Exportáló")
    parser.add_argument("--source_xml", required=True, help="A tökéletesre javított XML fájlok mappája")
    parser.add_argument("--source_crops", default="output_crops", help="Képkivágások mappája")
    parser.add_argument("--output", default="dataset", help="Kimeneti mappa")
    parser.add_argument("--zip", action="store_true", help="Készítsen egy ZIP fájlt a végén")
    parser.add_argument("--force-delete", action="store_true", help="Engedélyezi a meglévő kimeneti mappa törlését")
    args = parser.parse_args()
    
    export_trocr_dataset(
        args.source_xml,
        args.source_crops,
        args.output,
        args.zip,
        allow_delete_existing=args.force_delete,
    )