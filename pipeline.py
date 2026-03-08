import os
import subprocess
import torch
from pathlib import Path
from lxml import etree
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from tqdm import tqdm

# ==========================================
# 1. BEÁLLÍTÁSOK
# ==========================================
trocr_model_path = "./checkpoint-5400"                 
kraken_model_path = "./model/segmentation.mlmodel"     
data_folder = "./oldalak"                              
output_folder = "./felismert_szovegek"                 
padding = 5                                            

Path(output_folder).mkdir(parents=True, exist_ok=True)

# ==========================================
# 2. RENDSZER ÉS MODELL BETÖLTÉSE
# ==========================================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Használt eszköz: {device}")
print("TrOCR modell betöltése a memóriába...")

processor = TrOCRProcessor.from_pretrained(trocr_model_path)
model = VisionEncoderDecoderModel.from_pretrained(trocr_model_path).to(device)

# ==========================================
# 3. KÉPEK FELDOLGOZÁSA ÉS XML INJEKTÁLÁS
# ==========================================
image_extensions = {'.jpg', '.jpeg', '.png'}
image_files = sorted([p for p in Path(data_folder).iterdir() if p.suffix.lower() in image_extensions])

if not image_files:
    print(f"Hiba: Nem találtam képeket a '{data_folder}' mappában!")
else:
    print(f"Összesen {len(image_files)} oldal feldolgozása indul...\n")

    for img_path in tqdm(image_files, desc="Oldalak olvasása és XML építése"):
        xml_path = img_path.with_suffix('.xml')
        
        # --- 1. LÉPÉS: KRAKEN (Ha nincs alap XML) ---
        if not xml_path.exists() and not img_path.with_suffix('.XML').exists():
            print(f"\n[Kraken] Hiányzó XML! Szegmentálás generálása: {img_path.name} ...")
            try:
                # PageXML formátumot kérünk a Krakentől a -x vagy --pagexml opciókkal
                cmd = [
                    "kraken", "-i", str(img_path), str(xml_path), 
                    "blla", "-i", kraken_model_path
                ]
                subprocess.run(cmd, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                print(f"Hiba a Kraken futtatásakor a(z) {img_path.name} fájlnál:\n{e.stderr.decode()}")
                continue 

        # --- 2. LÉPÉS: XML BEOLVASÁSA ÉS TROCR OLVASÁS ---
        oldal_szovege = []
        try:
            tree = etree.parse(str(xml_path))
            root = tree.getroot()
            full_image = Image.open(img_path).convert("RGB")

            # Megkeressük az összes TextLine elemet
            lines = root.xpath('.//*[local-name()="TextLine"]')
            
            for line in lines:
                coords = line.xpath('.//*[local-name()="Coords"]/@points')
                if not coords:
                    continue

                # Bounding Box kiszámítása
                points = [tuple(map(int, p.split(','))) for p in coords[0].split()]
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                left, top, right, bottom = min(xs), min(ys), max(xs), max(ys)

                # Padding ráhagyás
                left = max(0, left - padding)
                top = max(0, top - padding)
                right = min(full_image.width, right + padding)
                bottom = min(full_image.height, bottom + padding)

                line_crop = full_image.crop((left, top, right, bottom))

                # TrOCR szövegfelismerés
                pixel_values = processor(images=line_crop, return_tensors="pt").pixel_values.to(device)
                generated_ids = model.generate(pixel_values)
                generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

                oldal_szovege.append(generated_text)

                # --- 3. LÉPÉS: SZÖVEG INJEKTÁLÁSA AZ XML-BE ---
                # Névtér (namespace) kinyerése a hibátlan XML struktúrához
                ns = line.nsmap.get(line.prefix) or line.nsmap.get(None)
                ns_prefix = f"{{{ns}}}" if ns else ""

                # Megnézzük, van-e már <TextEquiv> a <TextLine>-ban
                text_equiv = line.find(f"{ns_prefix}TextEquiv")
                if text_equiv is None:
                    text_equiv = etree.SubElement(line, f"{ns_prefix}TextEquiv")

                # Megnézzük, van-e <Unicode> a <TextEquiv>-ben
                unicode_el = text_equiv.find(f"{ns_prefix}Unicode")
                if unicode_el is None:
                    unicode_el = etree.SubElement(text_equiv, f"{ns_prefix}Unicode")

                # Beírjuk a felismert szöveget
                unicode_el.text = generated_text

            # --- 4. LÉPÉS: MENTÉS ---
            # 4/A: Mentés tiszta TXT-be
            output_txt_path = Path(output_folder) / f"{img_path.stem}.txt"
            with open(output_txt_path, "w", encoding="utf-8") as f:
                f.write("\n".join(oldal_szovege))

            # 4/B: Mentés INJEKTÁLT XML-be
            output_xml_path = Path(output_folder) / f"{img_path.stem}.xml"
            # Gyönyörű formázással és XML fejlélccel mentjük el
            tree.write(str(output_xml_path), encoding="utf-8", xml_declaration=True, pretty_print=True)

        except Exception as e:
            print(f"\nHiba a(z) {img_path.name} olvasásakor: {e}")

    print(f"\nZseniális! A folyamat lezárult. Keresd a .txt és .xml fájlokat itt: {Path(output_folder).absolute()}")