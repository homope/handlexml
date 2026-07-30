# Követelmény- és funkcionalitás dokumentáció

## 1. Cél
Ez a dokumentum a `handlexml` projekt működési követelményeit és fő funkcionalitásait írja le.
A projekt célja PAGE-XML alapú HTR adatelőkészítés és OCR/HTR támogatás TrOCR és Kraken munkafolyamatokhoz.

## 2. Hatókör
A rendszer az alábbi feladatokat támogatja:
- PAGE-XML állományok előkészítése és javítása.
- Kraken-kompatibilis baseline pótlás.
- XSD alapú validáció és hibás fájlok karanténba helyezése.
- Transkribus struktúrák laposítása tanítási célra.
- Sor-kivágások (line crops) generálása PAGE-XML koordinátákból.
- TrOCR és Kraken tanító adathalmaz exportálása.
- Opcionális végponttól-végpontig pipeline futtatás (szegmentálás + olvasás + XML visszaírás).
- GUI alapú (Tkinter) futtatás több folyamathoz.

## 3. Rendszerkövetelmények

### 3.1 Hardver
- CPU: minimum 4 mag ajánlott tömeges feldolgozáshoz.
- RAM: minimum 8 GB, ajánlott 16 GB vagy több.
- GPU: NVIDIA CUDA-képes GPU erősen ajánlott TrOCR gyors futtatásához.
- Tárhely: a bemeneti képek + exportált datasetek miatt több GB szabad hely szükséges.

### 3.2 Szoftver
- Operációs rendszer: Windows (a jelenlegi workspace környezetben használt), de a szkriptek jellemzően platformfüggetlenek.
- Python: 3.9+ ajánlott.
- Külső Python csomagok:
  - `lxml`
  - `Pillow`
  - `torch`
  - `transformers`
  - `tqdm`
  - `kraken` (CLI és szegmentálás miatt)
- GUI használathoz: `tkinter` (általában alapértelmezett Python telepítés része Windows alatt).

### 3.3 Modellek és erőforrások
- TrOCR modellmappa: pl. `checkpoint-5400/`.
- Kraken szegmentáló modell: pl. `models/blla.mlmodel` vagy a futtatásban megadott `.mlmodel` fájl.
- PAGE XML XSD: `pagexml/pagecontent.xsd`.

## 4. Bemeneti és kimeneti követelmények

### 4.1 Bemenetek
- XML előkészítéshez: `.xml` fájlok könyvtára.
- Exportokhoz: XML és azonos törzsnevű képfájlok (`.jpg`, `.jpeg`, `.png`, esetenként `.tif/.tiff`).
- TrOCR crop generáláshoz: PAGE-XML fájlok `TextLine/Coords` mezőkkel és forrásképekkel.
- Pipeline futtatáshoz: képfájlok, opcionálisan meglévő XML fájlok.

### 4.2 Kimenetek
- Javított XML-ek (pl. `clean_xml/`).
- Karanténba helyezett hibás XML-ek és futási napló (`quarantine_report.txt`).
- Kraken-ready mappa (XML + képek), opcionális ZIP.
- TrOCR dataset mappa (`train/`, `val/`, `test/`) splitenként `metadata.csv`-vel, opcionális ZIP.
- Sor-kivágás képek (`output_crops/` vagy megadott könyvtár).
- Pipeline esetén oldalanként `.txt` és injektált `.xml`.

## 5. Fő funkcionalitások modulonként

### 5.1 XML előkészítés és validáció
- Fájl: `prepare_dataset.py`
  - PAGE namespace frissítése (2013 → 2019).
  - `imageFilename` szinkronizálása XML fájlnév alapján.
  - Negatív koordináták javítása (`Coords`).
  - `TextLine` elemen belül elem-sorrend javítása (`Coords` előre).
- Fájl: `patch_kraken_xml.py`
  - Hiányzó `Baseline` automatikus generálása `Coords` alapján.
- Fájl: `validate_xml.py`
  - XSD séma szerinti validáció.
- Fájl: `main.py`
  - Folyamat-vezérlés: előkészítés → baseline patch → validáció.
  - Hibás fájlok karanténba mozgatása.
  - Karantén napló írása.

### 5.2 Transkribus adatelőkészítés
- Fájl: `transkribus.py`, `transkribus2.py`
  - Többszintű Transkribus könyvtárszerkezet laposítása.
  - XML-kép párok egységes névvel történő újragenerálása.
  - `imageFilename` frissítés és (a 2-es verzióban) koordináta-javítás.

### 5.3 Sor-kivágások és dataset export
- Fájl: `generate_crops.py`
  - `TextLine/Coords` alapján sor-kivágások mentése képfájlokba.
  - Állítható `padding` ráhagyás.
- Fájl: `export_dataset.py`
  - TrOCR dataset export (`train/val/test`).
  - Szövegforrás: `TextLine/TextEquiv/Unicode`.
  - Üres vagy bizonytalan (`[?]`) sorok szűrése.
  - `metadata.csv` generálás splitenként.
- Fájl: `export_kraken.py`
  - Kraken tanításhoz XML+kép párok exportja egy mappába.
  - `custom` attribútumok eltávolítása.
  - Opcionális ZIP csomagolás.

### 5.4 Végponttól-végpontig HTR pipeline
- Fájl: `pipeline.py`
  - Képoldalak beolvasása.
  - Ha hiányzik XML: Kraken `blla` szegmentálás futtatása.
  - TrOCR inferencia soronként a kivágott sorképeken.
  - Felismert szöveg visszaírása XML-be (`TextEquiv/Unicode`).
  - Eredmények mentése `.txt` és `.xml` fájlokba.

### 5.5 GUI felület
- Fájl: `gui_launcher.py`
  - Tkinter felület 4 fő munkafolyamathoz:
    1. XML javítás/validáció
    2. Transkribus laposítás
    3. Kraken export
    4. TrOCR export + crop generálás
  - Folyamatok külön szálon futnak (reszponzív UI).
  - Konzol-kimenet beágyazott naplóablakban jelenik meg.
  - Nem üres célmappák törlésének felhasználói megerősítése.

## 6. Működési követelmények
- A bemeneti XML-eknek feldolgozhatónak kell lenniük (well-formed XML).
- A képfájloknak elérhetőnek kell lenniük az XML-ekhez illeszkedően.
- TrOCR pipeline futtatáskor a modellmappa legyen olvasható és kompatibilis a `transformers` verzióval.
- Kraken szegmentáláshoz a `kraken` parancs legyen elérhető a környezetben.
- XSD validációhoz a sémafájl létezzen és olvasható legyen.

## 7. Nem-funkcionális követelmények
- Megbízhatóság: hibás fájlok ne állítsák le a teljes batch futást.
- Nyomonkövethetőség: karantén és naplófájl biztosítása.
- Skálázhatóság: batch feldolgozás több száz XML állományra.
- Karbantarthatóság: moduláris felépítés (külön script funkcionális egységenként).
- Biztonságos fájlkezelés: célmappa törléséhez explicit megerősítés/opció szükséges.

## 8. Ismert korlátok
- A namespace kezelés több helyen szövegcserére épül; vegyes vagy sérült namespace esetén egyedi javítás kellhet.
- A baseline generálás heurisztikus, ezért speciális tipográfiánál pontossági korlátja lehet.
- A pipeline fájlút-konvenciója (`model` vs `models`) futtatás előtt ellenőrizendő.
- Nagy adathalmaznál a futási idő és tárhelyigény jelentős lehet.

## 9. Elfogadási kritériumok (minimum)
- A `main.py` futtatásával érvényes XML-ek a kimeneti mappába, hibásak a karanténba kerülnek.
- A `generate_crops.py` ténylegesen létrehozza a sorképeket az XML koordináták alapján.
- A `export_dataset.py` létrehozza a `train/val/test` struktúrát és a splitenkénti `metadata.csv` fájlokat.
- A `export_kraken.py` egy mappába exportálja a konzisztens XML+kép párokat.
- A `gui_launcher.py` felületről a négy fő folyamat elindítható és naplózva van.

## 10. Javasolt futtatási sorrend
1. XML javítás és validáció (`main.py` vagy GUI 1. fül).
2. (Szükség esetén) Transkribus laposítás (`transkribus.py`/GUI 2. fül).
3. Crop generálás (`generate_crops.py` vagy GUI 4. fül).
4. TrOCR dataset export (`export_dataset.py` vagy GUI 4. fül).
5. Kraken dataset export (`export_kraken.py` vagy GUI 3. fül).
6. Opcionálisan teljes OCR pipeline futtatása (`pipeline.py`).
