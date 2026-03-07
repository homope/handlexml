import os
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET

def clamp_negative_coords(pts_str):
    """Negatív koordináták korrigálása (0-ra állítás)."""
    pairs = pts_str.split()
    fixed_pairs = []
    for pair in pairs:
        if ',' in pair:
            x_str, y_str = pair.split(',')
            x = max(0, int(round(float(x_str))))
            y = max(0, int(round(float(y_str))))
            fixed_pairs.append(f"{x},{y}")
    return " ".join(fixed_pairs)

def flatten_transkribus_for_kraken(root_dir, output_dir):
    root_path = Path(root_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # PAGE XML névtér regisztrálása (2013-as verzió a fájl alapján)
    ns = {'pc': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'}
    ET.register_namespace('', ns['pc'])

    for folder in root_path.iterdir():
        if not folder.is_dir():
            continue
        
        page_dir = folder / "page"
        if not page_dir.exists():
            continue

        print(f"Feldolgozás: {folder.name}")

        for xml_file in page_dir.glob("*.xml"):
            # A fájl neve pl: '0001_image00002.xml'
            # Megkeressük a hozzá tartozó képet az eredeti néven (image00002.jpg)
            # A beküldött XML-ben az imageFilename="0001_image00002.jpg" szerepel
            
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                page_elem = root.find('.//pc:Page', ns)
                
                if page_elem is None:
                    continue

                orig_image_filename = page_elem.get('imageFilename')
                image_file = folder / orig_image_filename
                
                # Ha nem találja a mappában a '0001_...' nevű képet, megpróbálja az XML neve alapján
                if not image_file.exists():
                    # Levágjuk az elejéről a sorszámot, ha a kép csak 'image00002.jpg'
                    potential_name = orig_image_filename.split('_', 1)[-1]
                    image_file = folder / potential_name

                if image_file.exists():
                    # Új név: mappa_neve + eredeti_kép_neve (sorszám nélkül a tisztaságért)
                    clean_img_name = image_file.name
                    new_base_name = f"{folder.name}_{clean_img_name.split('.')[0]}"
                    new_xml_path = out_path / f"{new_base_name}.xml"
                    new_img_path = out_path / f"{new_base_name}{image_file.suffix}"

                    # 1. imageFilename frissítése az új névre
                    page_elem.set('imageFilename', new_img_path.name)
                    
                    # 2. Koordináták javítása (mint a prepare_dataset.py-ban)
                    for elem in root.findall('.//pc:Coords', ns):
                        if 'points' in elem.attrib:
                            elem.set('points', clamp_negative_coords(elem.get('points')))
                    
                    for elem in root.findall('.//pc:Baseline', ns):
                        if 'points' in elem.attrib:
                            elem.set('points', clamp_negative_coords(elem.get('points')))

                    # Mentés és másolás
                    tree.write(new_xml_path, encoding='UTF-8', xml_declaration=True)
                    shutil.copy2(image_file, new_img_path)
                    print(f"  [OK] -> {new_base_name}")
                else:
                    print(f"  [!] Kép nem található: {orig_image_filename} a {folder.name} mappában")

            except Exception as e:
                print(f"  [HIBA] {xml_file.name}: {e}")

if __name__ == "__main__":
    SOURCE_DIRECTORY = r"kesobb" 
    TARGET_DIRECTORY = r"Kraken_Dataset"
    
    flatten_transkribus_for_kraken(SOURCE_DIRECTORY, TARGET_DIRECTORY)