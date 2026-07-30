# Opcionális teljes OCR pipeline – követelmény és funkcionalitás

## 1. Cél
Ez a dokumentum a `pipeline.py` által megvalósított opcionális, végponttól-végpontig OCR/HTR feldolgozás követelményeit és működését rögzíti.

## 2. Funkcionális leírás
A pipeline oldalanként az alábbi lépéseket hajtja végre:
1. Képfájlok beolvasása a bemeneti mappából (`.jpg`, `.jpeg`, `.png`).
2. XML társállomány keresése azonos törzsnéven.
3. Ha XML hiányzik: Kraken `blla` szegmentálás futtatása és PAGE-XML generálás.
4. XML beolvasása és `TextLine` sorok kinyerése.
5. Soronként bounding box számítás a `Coords/points` alapján, állítható `padding` ráhagyással.
6. TrOCR inferencia a kivágott sor-képeken.
7. Felismert szöveg injektálása XML-be `TextEquiv/Unicode` mezőkbe.
8. Kimenet mentése oldalanként:
   - teljes oldalszöveg: `.txt`
   - injektált PAGE-XML: `.xml`

## 3. Konfigurációs paraméterek
A `pipeline.py` elején állítható kulcsparaméterek:
- `trocr_model_path`: TrOCR modell mappa útvonala (pl. `./checkpoint-5400`).
- `kraken_model_path`: Kraken szegmentáló modell útvonala (pl. `./model/segmentation.mlmodel`).
- `data_folder`: bemeneti képek (és opcionális XML-ek) mappája.
- `output_folder`: kimeneti `.txt` és `.xml` fájlok célmappája.
- `padding`: pixel ráhagyás a sor-kivágásokhoz.

## 4. Követelmények

### 4.1 Kötelező bemenetek
- Bemeneti mappa legalább egy támogatott képformátummal.
- TrOCR modellfájlok a megadott modellmappában.
- Kraken modellfájl, ha XML automatikus generálás szükséges.

### 4.2 Környezeti követelmények
- Python 3.9+.
- Telepített csomagok: `torch`, `transformers`, `lxml`, `Pillow`, `tqdm`.
- Elérhető `kraken` CLI a rendszerben.
- GPU opcionális, de erősen ajánlott teljesítmény miatt.

### 4.3 Adatminőségi követelmények
- A `Coords/points` mezők numerikus koordinátákat tartalmazzanak.
- A képek olvashatók legyenek és összerendelhetők legyenek az XML-ekkel.

## 5. Kimeneti szerződés
- Minden sikeresen feldolgozott oldalhoz keletkezik:
  - `<oldalnév>.txt`
  - `<oldalnév>.xml`
- A kimeneti XML megőrzi a PAGE struktúrát, és bővül a `TextEquiv/Unicode` szöveggel.

## 6. Hibatűrés és viselkedés
- Hiányzó képek vagy hibás oldalak nem feltétlenül állítják le a teljes futást; a pipeline oldalanként próbál haladni.
- Kraken futási hiba esetén az adott oldal átugrásra kerül.
- XML parse vagy képfeldolgozási hiba esetén az adott oldal hibával naplózódik.

## 7. Ismert korlátok
- A szegmentálás és a felismerés minősége erősen függ a modellek minőségétől.
- A `kraken_model_path` alapértelmezett értéke mappanév-eltérést okozhat (`model` vs `models`) a workspace-ben, ezért futtatás előtt ellenőrizendő.
- A `TextLine` koordináták pontatlansága a TrOCR eredmény minőségét közvetlenül rontja.

## 8. Minimális elfogadási kritériumok
- A pipeline legalább egy bemeneti képet sikeresen feldolgoz.
- A kimeneti mappában keletkezik `.txt` és `.xml` pár.
- A kimeneti XML legalább egy `TextLine` elemnél tartalmaz `TextEquiv/Unicode` értéket.

## 9. Rövid futtatási ellenőrzőlista
1. Modellútvonalak ellenőrzése (`trocr_model_path`, `kraken_model_path`).
2. Bemeneti mappa ellenőrzése (`data_folder`).
3. Kimeneti mappa jogosultság ellenőrzése (`output_folder`).
4. `kraken` CLI elérhetőség ellenőrzése.
5. Pipeline futtatás és kimenet mintavételes ellenőrzése.