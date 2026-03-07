import os
import glob
import xml.etree.ElementTree as ET

def fix_transkribus_xmls(folder_path):
    # A PAGE XML névtér (namespace), ami az XML-ekben szerepel
    namespace = 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15'
    
    # Regisztráljuk a névteret, hogy mentéskor ne tegyen "ns0:" előtagokat az elemekhez
    ET.register_namespace('', namespace)
    
    # Megkeressük az összes XML fájlt a megadott mappában
    xml_pattern = os.path.join(folder_path, '*.xml')
    xml_files = glob.glob(xml_pattern)
    
    if not xml_files:
        print(f"Nem található XML fájl a(z) '{folder_path}' mappában.")
        return

    print(f"Összesen {len(xml_files)} XML fájl feldolgozása indul a(z) '{folder_path}' mappában...\n")

    for file_path in xml_files:
        try:
            # XML fa betöltése
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # A Metadata blokk megkeresése (névtérrel együtt kell hivatkozni rá)
            metadata = root.find(f'{{{namespace}}}Metadata')
            
            if metadata is not None:
                # A problémás TranskribusMetadata elem megkeresése
                transkribus_metadata = metadata.find(f'{{{namespace}}}TranskribusMetadata')
                
                if transkribus_metadata is not None:
                    # Elem törlése, mivel nem felel meg a XSD sémának
                    metadata.remove(transkribus_metadata)
                    
                    # A fájl mentése (felülírása) a javított fával
                    tree.write(file_path, encoding='utf-8', xml_declaration=True)
                    print(f"[JAVÍTVA] {os.path.basename(file_path)} - TranskribusMetadata eltávolítva.")
                else:
                    print(f"[OK] {os.path.basename(file_path)} - Nem igényel javítást (nincs hibás elem).")
            else:
                print(f"[FIGYELMEZTETÉS] {os.path.basename(file_path)} - Nem található Metadata blokk.")
                
        except ET.ParseError as e:
            print(f"[HIBA] {os.path.basename(file_path)} - XML értelmezési hiba: {e}")
        except Exception as e:
            print(f"[HIBA] {os.path.basename(file_path)} - Váratlan hiba: {e}")

if __name__ == "__main__":
    # Beállítjuk a javítandó célmappát
    TARGET_FOLDER = 'quarantine_xml'
    
    # Ellenőrizzük, hogy létezik-e a mappa
    if not os.path.exists(TARGET_FOLDER):
        print(f"A(z) '{TARGET_FOLDER}' mappa nem létezik a jelenlegi könyvtárban.")
    else:
        fix_transkribus_xmls(TARGET_FOLDER)
        print("\nFeldolgozás befejeződött.")