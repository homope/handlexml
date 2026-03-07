import os
from pathlib import Path
from lxml import etree

def generate_baseline_from_coords(coords_string):
    """
    Kiszámítja a Baseline-t a Coords poligon alsó pontjai alapján.
    Ez egy egyszerűsített heurisztika: a doboz bal és jobb alsó sarkát köti össze.
    """
    points = [tuple(map(int, p.split(','))) for p in coords_string.split()]
    if not points:
        return ""
    
    # Keresünk egy bal és egy jobb oldali pontot, ami a legmélyebben van (legnagyobb Y)
    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    
    # Keresünk Y értékeket, amik a min_x és max_x közelében vannak
    left_points = [p for p in points if p[0] < min_x + (max_x - min_x) * 0.2]
    right_points = [p for p in points if p[0] > max_x - (max_x - min_x) * 0.2]
    
    if not left_points or not right_points:
        return ""

    left_y = max(p[1] for p in left_points)
    right_y = max(p[1] for p in right_points)

    return f"{min_x},{left_y} {max_x},{right_y}"

def patch_for_kraken(xml_path, output_path):
    tree = etree.parse(str(xml_path))
    root = tree.getroot()
    # Dinamikus névtér kinyerés
    ns_uri = root.nsmap.get(None, "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15")
    ns = {"ns": ns_uri}

    for textline in root.xpath('.//ns:TextLine', namespaces=ns):
        coords = textline.find('ns:Coords', namespaces=ns)
        baseline = textline.find('ns:Baseline', namespaces=ns)

        # Ha van Coords, de nincs Baseline, generálunk egyet
        if coords is not None and baseline is None:
            points = coords.get('points')
            if points:
                baseline_str = generate_baseline_from_coords(points)
                if baseline_str:
                    new_baseline = etree.Element(f"{{{ns_uri}}}Baseline")
                    new_baseline.set('points', baseline_str)
                    # Beillesztés a Coords után
                    coords_index = textline.index(coords)
                    textline.insert(coords_index + 1, new_baseline)

    tree.write(str(output_path), encoding='utf-8', xml_declaration=True, pretty_print=True)
    print(f"[KRAKEN PATCH] Baseline generálva: {Path(xml_path).name}")