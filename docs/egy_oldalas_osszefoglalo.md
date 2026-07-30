# Handlexml – egyoldalas összefoglaló

## Mi a rendszer célja?
A handlexml projekt PAGE-XML alapú HTR/OCR adatelőkészítést végez, elsősorban TrOCR és Kraken tanítási/feldolgozási folyamatok támogatására. A rendszer feladata, hogy heterogén forrásokból (nyers XML-ek, képek, Transkribus exportok) konzisztens, validálható és tanításra alkalmas adathalmazt állítson elő.

## Milyen üzemi problémát old meg?
- Egységesíti a különböző forrásból érkező PAGE-XML fájlokat.
- Javítja a tipikus strukturális hibákat (névtér, koordináták, elem-sorrend).
- Pótolja a Krakenhez szükséges baseline adatokat, ha hiányoznak.
- Kiszűri és karanténba helyezi a hibás XML-eket.
- Automatizálja a TrOCR és Kraken dataset előállítását.
- Opcionálisan végigfuttat egy teljes OCR pipeline-t (szegmentálás + felismerés + XML-be visszaírás).

## Fő funkcionalitások röviden
1. **XML javítás és validáció**
   - Namespace frissítés (2013→2019), koordinátajavítás, szerkezeti rendezés.
   - XSD validáció és karantén-naplózás.
2. **Kraken kompatibilitás**
   - Baseline generálás `TextLine/Coords` alapján.
   - Kraken-ready XML+kép export, opcionális ZIP-pel.
3. **TrOCR adatelőkészítés**
   - Sor-kivágások előállítása PAGE-XML koordinátákból.
   - `train/val/test` split és `metadata.csv` generálás.
4. **Transkribus integráció**
   - Többszintű mappastruktúra laposítása, fájlnév-konzisztencia biztosítása.
5. **GUI támogatás**
   - Egyetlen felületen indítható a 4 fő folyamat, valós idejű naplózással.

## Bemenetek és kimenetek
- **Bemenet:** XML fájlok, hozzájuk tartozó képek (`jpg/jpeg/png`, részben `tif/tiff`), modellek (`checkpoint-5400`, Kraken `.mlmodel`), XSD séma.
- **Kimenet:**
  - javított XML-ek,
  - karanténba mozgatott hibás fájlok és napló,
  - line crop képek,
  - TrOCR dataset (`train/val/test` + `metadata.csv`),
  - Kraken-ready mappa és opcionális ZIP,
  - pipeline esetén oldalanként `.txt` és injektált `.xml`.

## Technikai és működési követelmények
- Python 3.9+ (ajánlott).
- Csomagok: `lxml`, `Pillow`, `torch`, `transformers`, `tqdm`, `kraken`.
- Windows környezet támogatott (jelenlegi célkörnyezet), GPU erősen ajánlott TrOCR futtatáshoz.
- Feldolgozható (well-formed) XML és elérhető képfájl-párosítás szükséges.

## Minőségi jellemzők
- **Megbízhatóság:** batch futás hibatűrő; hibás fájlak nem állítják le a teljes folyamatot.
- **Nyomonkövethetőség:** karantén és részletes futási napló.
- **Skálázhatóság:** nagyobb XML állománykészletek kezelése.
- **Karbantarthatóság:** moduláris szkriptstruktúra, külön felelősségi körökkel.

## Ismert korlátok és kockázatok
- A namespace kezelés részben szövegcserére épül; vegyes XML-eknél manuális utóellenőrzés szükséges lehet.
- Baseline-generálás heurisztikus, így speciális oldalképekben pontatlanság előfordulhat.
- A teljes pipeline futtatása előtt modellútvonalakat és könyvtárneveket ellenőrizni kell.

## Javasolt napi használati sorrend
1. XML javítás + validáció
2. (ha kell) Transkribus laposítás
3. Crop generálás
4. TrOCR export
5. Kraken export
6. Opcionális teljes OCR pipeline (részletesen: [opcionalis_teljes_ocr_pipeline_kovetelmeny_funkcionalitas.md](opcionalis_teljes_ocr_pipeline_kovetelmeny_funkcionalitas.md))

**Eredmény:** a projekt egy gyakorlatban jól használható, moduláris HTR adatelőkészítő rendszer, amely a kézi XML-javítás jelentős részét automatizálja, és közvetlenül előállít tanításra/importra kész adatformátumokat.