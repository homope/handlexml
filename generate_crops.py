import os
import argparse
from pathlib import Path
from PIL import Image
from lxml import etree

# python generate_crops.py --source mappa_neve --output crops --padding 5

def generate_crops(source_dir, output_crops_dir, padding=5):
    source_dir = Path(source_dir)
    output_dir = Path(output_crops_dir)
    
    # Kimeneti mappa létrehozása, ha nem létezik
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"--- Képkivágások (Crops) Generálása ---")
    print(f"Forrás mappa: {source_dir} | Cél mappa: {output_dir}")

    # Végigiterálunk az összes XML fájlon
    for xml_file in source_dir.glob("*.xml"):
        try:
            tree = etree.parse(str(xml_file))
            root = tree.getroot()

            # 1. Képfájl nevének megkeresése (névtér-függetlenül)
            page_elements = root.xpath('.//*[local-name()="Page"]')
            if not page_elements:
                continue
                
            page_el = page_elements[0]
            img_filename = page_el.get('imageFilename')
            
            # Ha valamiért üres, próbáljuk az XML neve alapján
            if not img_filename:
                img_filename = xml_file.stem + ".jpg"

            img_path = source_dir / img_filename
            
            # Ellenőrizzük, hogy létezik-e a nagy JPG kép
            if not img_path.exists():
                print(f"  [HIBA] Nem található az eredeti kép: {img_path}")
                continue

            # 2. Eredeti kép megnyitása a memóriában
            try:
                image = Image.open(img_path)
            except Exception as e:
                print(f"  [HIBA] Kép megnyitása sikertelen ({img_filename}): {e}")
                continue

            print(f"Feldolgozás: {xml_file.name} -> {img_filename}")

            # 3. Szövegsorok keresése
            lines = root.xpath('.//*[local-name()="TextLine"]')
            crop_count = 0
            
            for line in lines:
                line_id = line.get('id')
                coords_el = line.xpath('.//*[local-name()="Coords"]')
                
                if not coords_el:
                    continue
                    
                points_str = coords_el[0].get('points')
                if not points_str:
                    continue

                # 4. Koordináták feldolgozása "x1,y1 x2,y2 ..."
                points = []
                for pt in points_str.split():
                    try:
                        x, y = map(int, pt.split(','))
                        points.append((x, y))
                    except ValueError:
                        continue

                if not points:
                    continue

                # 5. Bounding Box (befoglaló téglalap) kiszámítása
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                
                # Biztonsági ráhagyás (padding) hozzáadása, hogy a lelógó betűk (pl. g, j) ne vágódjanak le
                left = max(0, min(xs) - padding)
                top = max(0, min(ys) - padding)
                right = min(image.width, max(xs) + padding)
                bottom = min(image.height, max(ys) + padding)

                # 6. Kép kivágása és mentése
                if right > left and bottom > top:
                    crop_img = image.crop((left, top, right, bottom))
                    crop_filename = f"{xml_file.stem}_{line_id}.jpg"
                    crop_path = output_dir / crop_filename
                    crop_img.save(crop_path)
                    crop_count += 1

            print(f"  > {crop_count} db sor kivágva.")

        except Exception as e:
            print(f"Hiba az XML feldolgozásakor ({xml_file.name}): {e}")

    print("--- Kivágások generálása befejeződött! ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Szövegsorok kivágása PAGE-XML alapján")
    parser.add_argument("--source", default=".", help="Mappa, ahol az XML és a nagy JPG fájlok vannak (alapértelmezett: aktuális mappa)")
    parser.add_argument("--output", default="crops", help="Mappa, ahova a kivágások kerülnek (alapértelmezett: 'crops')")
    parser.add_argument("--padding", type=int, default=5, help="Ráhagyás pixelben a Bounding Box körül (alapértelmezett: 5)")
    
    args = parser.parse_args()
    generate_crops(args.source, args.output, args.padding)