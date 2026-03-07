import os
import lxml.etree as ET

def fix_and_validate_xml(xml_path, xsd_path, output_path):
    # 1. Séma betöltése
    with open(xsd_path, 'rb') as f:
        schema_root = ET.XML(f.read())
    schema = ET.XMLSchema(schema_root)

    # 2. XML fájl betöltése
    parser = ET.XMLParser(remove_blank_text=True)
    try:
        tree = ET.parse(xml_path, parser)
    except Exception as e:
        print(f"Hiba az XML olvasásakor ({xml_path}): {e}")
        return
    
    root = tree.getroot()

    # Névtér (namespace) azonosítása az XML-ből
    nsmap = root.nsmap
    default_ns = nsmap.get(None) or "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"
    ns = {'pc': default_ns}

    # 3. Sémahibák javítása (TranskribusMetadata konvertálása)
    metadata = root.find('pc:Metadata', ns)
    if metadata is not None:
        transkribus_meta = metadata.find('pc:TranskribusMetadata', ns)
        
        if transkribus_meta is not None:
            # Szabványos <UserDefined> blokk keresése vagy létrehozása
            user_defined = metadata.find('pc:UserDefined', ns)
            if user_defined is None:
                user_defined = ET.Element(f"{{{default_ns}}}UserDefined")
                # A helyes XSD sorrend miatt a LastChange után érdemes beszúrni, 
                # de a fájl végére fűzés is működik, ha nincs utána más (pl. MetadataItem)
                metadata.append(user_defined)

            # Az attribútumok átmentése szabványos UserAttribute elemekként
            for attr_name, attr_value in transkribus_meta.attrib.items():
                user_attr = ET.SubElement(user_defined, f"{{{default_ns}}}UserAttribute")
                user_attr.set('name', f"transkribus_{attr_name}")
                user_attr.set('value', attr_value)
                user_attr.set('type', 'xsd:string')

            # A nem támogatott eredeti elem eltávolítása
            metadata.remove(transkribus_meta)

    # 4. Validálás a javítás után
    is_valid = schema.validate(tree)
    if not is_valid:
        print(f"❌ Validációs hibák maradtak a fájlban: {xml_path}")
        for error in schema.error_log:
            print(f"   Sor {error.line}: {error.message}")
    else:
        print(f"✅ Sikeres javítás és validálás: {xml_path}")

    # 5. Javított XML mentése
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    tree.write(output_path, encoding='utf-8', xml_declaration=True, pretty_print=True)

# Futtatás a példafájlokon
if __name__ == "__main__":
    xsd_file = "pagecontent.xsd"
    
    # Kicserélendő a saját fájlneveidre / elérési utakra
    files_to_fix = [
        "SZEEKL_VIII_9_a_1900-1904_1_0006_SZEEKL_VIII_9_a_1900-1904_006.xml",
        "SZEEKL_VIII_9_a_1900-1904_1_0010_SZEEKL_VIII_9_a_1900-1904_010.xml",
        "SZEEKL_VIII_9_a_1900-1904_1_0014_SZEEKL_VIII_9_a_1900-1904_014.xml"
    ]

    for xml_file in files_to_fix:
        if os.path.exists(xml_file):
            # A javított fájlok egy "fixed_xmls" mappába kerülnek
            output_file = os.path.join("fixed_xmls", xml_file)
            fix_and_validate_xml(xml_file, xsd_file, output_file)
        else:
            print(f"Nem található a fájl: {xml_file}")