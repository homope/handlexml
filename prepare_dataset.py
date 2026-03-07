import os
import argparse
from pathlib import Path
from lxml import etree

def clean_coordinates(coord_string):
    """Kiszűri a negatív koordinátákat és 0-ra cseréli őket."""
    if not coord_string:
        return ""
    points = coord_string.split()
    cleaned_points = []
    for p in points:
        x, y = p.split(',')
        x = str(max(0, int(x)))
        y = str(max(0, int(y)))
        cleaned_points.append(f"{x},{y}")
    return " ".join(cleaned_points)

def prepare_xml(input_path, output_path):
    # 1. Névtér frissítés memóriában (2013 -> 2019)
    with open(input_path, 'r', encoding='utf-8') as f:
        xml_content = f.read()
    
    xml_content = xml_content.replace(
        'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15',
        'http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15'
    )

    # 2. XML feldolgozása
    root = etree.fromstring(xml_content.encode('utf-8'))
    ns = {"ns": "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"}

    # 3. Fájlnév szinkronizálás
    page_el = root.find('.//ns:Page', namespaces=ns)
    if page_el is not None:
        expected_image_name = Path(input_path).stem + ".jpg" # Feltételezett kiterjesztés
        page_el.set('imageFilename', expected_image_name)

    # 4. Negatív koordináták javítása
    for coords_el in root.xpath('.//ns:Coords', namespaces=ns):
        points = coords_el.get('points')
        if points:
            coords_el.set('points', clean_coordinates(points))

    # 5. Elemek sorrendjének kényszerítése (TextLine-on belül)
    for textline in root.xpath('.//ns:TextLine', namespaces=ns):
        coords = textline.find('ns:Coords', namespaces=ns)
        baseline = textline.find('ns:Baseline', namespaces=ns)
        
        # Ha mindkettő létezik, a Coords-nak meg kell előznie a Baseline-t
        if coords is not None and baseline is not None:
            textline.remove(coords)
            textline.insert(0, coords) # A Coords mindig az első elem legyen

    # Mentés
    tree = etree.ElementTree(root)
    tree.write(str(output_path), encoding='utf-8', xml_declaration=True, pretty_print=True)
    print(f"[KÉSZ] Felkészítve: {Path(input_path).name}")

if __name__ == "__main__":
    # Használat: python prepare_dataset.py --input data/ --output clean_data/
    pass