import os
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET

def flatten_transkribus_for_kraken(root_dir, output_dir):
    """
    Átalakítja a Transkribus struktúrát Kraken tanításhoz.
    1. Iterál a mappákon.
    2. XML + JPG párokat hoz létre egyedi névvel (mappa + fájlnév).
    3. Frissíti az imageFilename attribútumot az XML-ben.
    """
    root_path = Path(root_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # PAGE XML névtér regisztrálása
    ns = {'pc': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'}
    ET.register_namespace('', ns['pc'])

    # 1. Iterálás a mappákon (pl. SZEEKL_VIII_9_a_1884-1887)
    for folder in root_path.iterdir():
        if not folder.is_dir():
            continue
        
        page_dir = folder / "page"
        if not page_dir.exists():
            continue

        print(f"Feldolgozás: {folder.name}")

        # 2. XML fájlok keresése a 'page' mappában
        for xml_file in page_dir.glob("*.xml"):
            base_name = xml_file.stem
            
            # Megkeressük a hozzá tartozó képet (jpg vagy jpeg)
            image_file = folder / f"{base_name}.jpg"
            if not image_file.exists():
                image_file = folder / f"{base_name}.jpeg"

            if image_file.exists():
                # Új fájlnév generálása: mappa_neve + eredeti_név
                new_base_name = f"{folder.name}_{base_name}"
                new_xml_path = out_path / f"{new_base_name}.xml"
                new_img_path = out_path / f"{new_base_name}{image_file.suffix}"

                # 3. XML módosítása (imageFilename frissítése)
                try:
                    tree = ET.parse(xml_file)
                    root = tree.getroot()
                    
                    # Megkeressük a Page elemet és frissítjük az attribútumot
                    page_elem = root.find('.//pc:Page', ns)
                    if page_elem is not None:
                        page_elem.set('imageFilename', new_img_path.name)
                    
                    # Mentés az új helyre
                    tree.write(new_xml_path, encoding='UTF-8', xml_declaration=True)
                    
                    # Kép másolása az új névvel
                    shutil.copy2(image_file, new_img_path)
                    
                except Exception as e:
                    print(f"  [!] Hiba a(z) {xml_file.name} feldolgozásakor: {e}")

    print(f"\nKész! Az adathalmaz itt található: {output_dir}")

if __name__ == "__main__":
    # Állítsd be az útvonalakat a saját környezetednek megfelelően!
    SOURCE_DIRECTORY = r"C:\_py\Vezetotestuleti\Transkribus" # Ahol a mappáid vannak
    TARGET_DIRECTORY = r"C:\_py\Vezetotestuleti\Kraken_Dataset"
    
    flatten_transkribus_for_kraken(SOURCE_DIRECTORY, TARGET_DIRECTORY)