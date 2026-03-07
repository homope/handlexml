import os
from pathlib import Path
from lxml import etree

def validate_page_xml(xml_path, xsd_path):
    try:
        # 1. XSD Séma betöltése
        with open(xsd_path, 'rb') as f:
            schema_root = etree.XML(f.read())
        schema = etree.XMLSchema(schema_root)
        
        # 2. Névtér memóriabeli konverziója
        with open(xml_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        xml_content = xml_content.replace(
            'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15',
            'http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15'
        )
        
        xml_doc = etree.fromstring(xml_content.encode('utf-8'))

        # 3. Validáció
        schema.assertValid(xml_doc)
        print(f"✅ [VALID] {Path(xml_path).name}: Hibátlan szerkezet.")
        return True, [] # Sikeres esetben üres hibalista

    except etree.DocumentInvalid as e:
        print(f"❌ [ÉRVÉNYTELEN] {Path(xml_path).name}")
        # Hibaüzenetek összegyűjtése listába
        errors = [f"Sor {error.line}: {error.message}" for error in schema.error_log]
        for err in errors:
            print(f"  -> {err}")
        return False, errors
        
    except Exception as e:
        error_msg = f"A fájl beolvasása sikertelen: {e}"
        print(f"⚠️ [HIBA] {Path(xml_path).name}: {error_msg}")
        return False, [error_msg]