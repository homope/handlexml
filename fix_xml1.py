import os
import glob
import datetime
from lxml import etree

# A séma névtere
NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"
NS_MAP = {"pc": NS}

def fix_xml_file(filepath):
    # Fájl beolvasása (szóközök megtartásával)
    parser = etree.XMLParser(remove_blank_text=False)
    try:
        tree = etree.parse(filepath, parser)
    except Exception as e:
        print(f"Hiba a fájl beolvasásakor: {filepath} - {e}")
        return

    root = tree.getroot()
    modified = False

    # 1. Processing eltávolítása és LastChange pótlása a Metadata-ban
    metadata = root.find(".//pc:Metadata", namespaces=NS_MAP)
    if metadata is not None:
        processing = metadata.find("pc:Processing", namespaces=NS_MAP)
        if processing is not None:
            metadata.remove(processing)
            modified = True
        
        last_change = metadata.find("pc:LastChange", namespaces=NS_MAP)
        if last_change is None:
            created = metadata.find("pc:Created", namespaces=NS_MAP)
            last_change_elem = etree.Element(f"{{{NS}}}LastChange")
            
            # Ha van Created tag, átvesszük annak az idejét, különben aktuális idő
            if created is not None and created.text:
                last_change_elem.text = created.text
            else:
                last_change_elem.text = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
            
            # Beszúrás a megfelelő helyre (Creator, Created után)
            if created is not None:
                created.addnext(last_change_elem)
            else:
                metadata.insert(0, last_change_elem)
            modified = True

    # 2. TextRegion type="Main" cseréje type="paragraph"-ra
    for text_region in root.findall(".//pc:TextRegion", namespaces=NS_MAP):
        if text_region.get("type") == "Main":
            text_region.set("type", "paragraph")
            modified = True

    # 3. TableRegion type attribútumának eltávolítása
    for table_region in root.findall(".//pc:TableRegion", namespaces=NS_MAP):
        if "type" in table_region.attrib:
            del table_region.attrib["type"]
            modified = True

    # 4. TableRegion rossz helyen (TextRegion belsejében) -> Mozgatás a Page elembe
    page = root.find(".//pc:Page", namespaces=NS_MAP)
    if page is not None:
        for text_region in root.findall(".//pc:TextRegion", namespaces=NS_MAP):
            for table_region in text_region.findall("pc:TableRegion", namespaces=NS_MAP):
                text_region.remove(table_region)
                page.append(table_region)
                modified = True

    # 5. TextLine elemek sorrendjének javítása (XSD sequence alapján)
    correct_order = [
        f"{{{NS}}}AlternativeImage",
        f"{{{NS}}}Coords",
        f"{{{NS}}}Baseline",
        f"{{{NS}}}Word",
        f"{{{NS}}}TextEquiv",
        f"{{{NS}}}TextStyle",
        f"{{{NS}}}UserDefined",
        f"{{{NS}}}Labels"
    ]
    
    for text_line in root.findall(".//pc:TextLine", namespaces=NS_MAP):
        children = list(text_line)
        if not children:
            continue
        
        current_tags = [child.tag for child in children]
        
        try:
            # Csak azokat rendezzük, amik benne vannak a várt listában, a többit a végén hagyjuk
            sorted_children = sorted(children, key=lambda x: correct_order.index(x.tag) if x.tag in correct_order else 999)
            
            # Ha a sorrend eltér az elvárttól, újra felépítjük a gyermekelemeket
            if current_tags != [child.tag for child in sorted_children]:
                for child in sorted_children:
                    text_line.remove(child)
                    text_line.append(child)
                modified = True
        except ValueError:
            pass

    # Ha történt módosítás, mentsük el a fájlt
    if modified:
        tree.write(filepath, encoding="utf-8", xml_declaration=True, pretty_print=False)
        print(f"Javítva: {os.path.basename(filepath)}")

def main():
    quarantine_dir = "quarantine_xml"
    if not os.path.exists(quarantine_dir):
        print(f"A '{quarantine_dir}' mappa nem található az aktuális könyvtárban.")
        return

    # Összes XML fájl lekérése a mappából
    xml_files = glob.glob(os.path.join(quarantine_dir, "*.xml"))
    if not xml_files:
        print("Nem találhatók XML fájlok a mappában.")
        return
        
    for filepath in xml_files:
        fix_xml_file(filepath)
    
    print("A feldolgozás befejeződött.")

if __name__ == "__main__":
    main()