import os
import shutil
import argparse
from pathlib import Path
from lxml import etree
import re

def export_for_kraken(source_xml_dir, source_img_dir, output_dir, zip_output=False, allow_delete_existing=False):
    source_xml = Path(source_xml_dir)
    source_img = Path(source_img_dir)
    out_dir = Path(output_dir)

    print(f"--- Kraken Dataset Export Indítása ---")
    
    if out_dir.exists() and any(out_dir.iterdir()):
        if not allow_delete_existing:
            raise RuntimeError(
                f"A kimeneti mappa nem ures es torlesre kerulne: {out_dir}. "
                "Hasznald a --force-delete kapcsolot, vagy engedelyezd a torlest a GUI-ban."
            )
        shutil.rmtree(out_dir)
    elif out_dir.exists() and allow_delete_existing:
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    xml_files = list(source_xml.glob("*.xml"))
    processed_count = 0

    for xml_file in xml_files:
        try:
            tree = etree.parse(str(xml_file))
            root = tree.getroot()
            ns = {"ns": root.nsmap.get(None, "http://www.loc.gov/standards/alto/ns-v3#")}

            image_exts = ['.jpg', '.jpeg', '.png', '.tif', '.tiff']
            found_image = None
            for ext in image_exts:
                test_img = source_img / (xml_file.stem + ext)
                if test_img.exists():
                    found_image = test_img
                    break
            
            if not found_image:
                print(f"  [HIÁNYZIK] Nem található kép a fájlhoz: {xml_file.name}")
                continue

            page_elements = root.xpath('.//*[local-name()="Page"]')
            if page_elements:
                page_el = page_elements[0]
                page_el.set('imageFilename', found_image.name)

            for elem in root.xpath('.//*[@custom]'):
                del elem.attrib['custom']

            target_xml_path = out_dir / xml_file.name
            target_img_path = out_dir / found_image.name
            
            tree.write(str(target_xml_path), encoding='utf-8', xml_declaration=True)
            shutil.copy2(found_image, target_img_path)
            
            processed_count += 1
            if processed_count % 10 == 0:
                print(f"  Feldolgozva: {processed_count} oldal...")

        except Exception as e:
            print(f"  [HIBA] {xml_file.name}: {e}")

    print(f"\nSiker! {processed_count} kép-XML pár exportálva ide: {out_dir}")

    # ÚJ RÉSZ: ZIP generálás
    if zip_output:
        print("ZIP fájl generálása a Colab-hoz/Kaggle-höz...")
        zip_path = Path(str(out_dir) + "_ready")
        shutil.make_archive(str(zip_path), 'zip', str(out_dir))
        print(f"ZIP elkészült: {zip_path}.zip")

    print(f"Tanításhoz használd: ketos train -f page *.xml")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kraken Dataset Tisztító és Exportáló")
    parser.add_argument("--xml", required=True, help="Forrás PAGE XML mappa")
    parser.add_argument("--img", required=True, help="Forrás eredeti képek mappája")
    parser.add_argument("--output", default="kraken_ready", help="Kimeneti mappa")
    parser.add_argument("--zip", action="store_true", help="Készítsen egy ZIP fájlt a végén")
    parser.add_argument("--force-delete", action="store_true", help="Engedélyezi a meglévő kimeneti mappa törlését")
    args = parser.parse_args()
    
    export_for_kraken(args.xml, args.img, args.output, args.zip, allow_delete_existing=args.force_delete)