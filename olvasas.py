import os
import torch
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from tqdm import tqdm  # Ez csinálja a szép folyamatjelzőt

# ==========================================
# 1. BEÁLLÍTÁSOK (Ezeket írd át a sajátodra!)
# ==========================================
model_path = "./checkpoint-5400"      # A mappád neve, amiben a letöltött modell van
input_folder = "./output_crops"     # A mappa, ahová a darabolt sorokat tetted
output_file = "eredmenyek.tsv"        # Ide mentjük az eredményt (Tabbal elválasztott fájl, Excelben jól nyitható)

# ==========================================
# 2. RENDSZER ELŐKÉSZÍTÉSE
# ==========================================
# Megnézzük, van-e videókártya a gépeden, különben marad a proci
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Használt eszköz: {device}")

print("Modell betöltése... (Ez eltarthat egy percig)")
processor = TrOCRProcessor.from_pretrained(model_path)
model = VisionEncoderDecoderModel.from_pretrained(model_path).to(device)

# ==========================================
# 3. FELDOLGOZÁS
# ==========================================
if not os.path.exists(input_folder):
    print(f"Hiba: Nem találom a mappát: {input_folder}")
else:
    # Kigyűjtjük a képfájlokat, és sorba rendezzük őket név szerint
    image_files = sorted([f for f in os.listdir(input_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
    
    if len(image_files) == 0:
        print("A mappa üres vagy nincsenek benne képek!")
    else:
        print(f"Összesen {len(image_files)} kép feldolgozása indul...\n")
        
        # Fájl megnyitása írásra
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("Fájlnév\tFelismert szöveg\n") # Fejléc
            
            # Végigmegyünk a képeken egy folyamatjelző kíséretében
            for filename in tqdm(image_files):
                img_path = os.path.join(input_folder, filename)
                
                try:
                    image = Image.open(img_path).convert("RGB")
                    
                    # Predikció
                    pixel_values = processor(images=image, return_tensors="pt").pixel_values.to(device)
                    generated_ids = model.generate(pixel_values)
                    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                    
                    # Eredmény kiírása a fájlba
                    f.write(f"{filename}\t{generated_text}\n")
                    
                except Exception as e:
                    print(f"\nHiba a(z) {filename} feldolgozásakor: {e}")

        print(f"\nKész! Az eredményeket megtalálod itt: {output_file}")