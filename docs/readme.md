# Teljes Automata HTR Futószalag: Kraken + TrOCR PageXML Pipeline

Ez a modul egy **"End-to-End" (végponttól végpontig)** dokumentum-feldolgozó adatfolyamot valósít meg. Képes a nyers oldal-képektől indulva a sorok felismerésén át egészen a szabványos, kereshető PageXML fájlok generálásáig mindent egyetlen lépésben, automatikusan elvégezni.

## Főbb funkciók és működési elv

* **Automatikus szegmentálás (Fallback logika):** A rendszer beolvassa a bemeneti mappát. Ha egy képhez nem talál hozzá tartozó XML fájlt, a háttérben automatikusan meghívja a Kraken modellt, legenerálja a sorok koordinátáit, és létrehozza a PageXML vázat.
* **Memória-optimalizált képkivágás:** Nem szemeteli tele a merevlemezt apró, kivágott sor-képekkel. A beolvasott XML koordináták (*Bounding Box*) alapján a rendszer röptében, a memóriában vágja ki a sorokat egy beállítható pixel-ráhagyással (*padding*), és adja át az AI-nak.
* **Szövegfelismerés (TrOCR):** A memóriában lévő kép-szeleteket a finomhangolt TrOCR modellünk olvassa el, kihasználva a GPU gyorsítást.
* **Szabványos XML injektálás ("Beoltás"):** A felismert magyar szöveget a rendszer nemcsak egy nyers szövegfájlba menti, hanem intelligensen beilleszti a PageXML struktúrába. Automatikusan létrehozza a megfelelő `<TextEquiv>` és `<Unicode>` tageket a megfelelő `<TextLine>` csomóponton belül.

## Könyvtárszerkezet és bemenet

A szkript futtatása előtt a fájlokat az alábbi struktúrába kell rendezni:
```plaintext
projekt_mappa/
├── checkpoint-5400/                 # A betanított TrOCR modell mappája
├── model/
│   └── segmentation.mlmodel         # A Kraken sorfelismerő (blla) modellje
├── oldalak/                         # BEMENET: Ide jönnek a .jpg/.png képek (és az esetleges .xml-ek)
└── felismert_szovegek/              # KIMENET: Ide generálja a program az eredményt plaintext
```


## Telepítési követelmények (Dependencies)

A szkript futtatásához a következő Python csomagok szükségesek:Bashpip install torch transformers lxml Pillow tqdm kraken

## Konfiguráció és Használat

A kód elején található változókkal könnyedén testreszabható a folyamat:

A finomhangolt szövegfelismerő modell útvonala."./checkpoint-5400"kraken_model_path 

Kraken szegmentáló modell útvonala."./model/segmentation.mlmodel"data_folder

A nyers képeket és XML-eket tartalmazó bemeneti mappa."./oldalak"output_folder

A kész szövegek és XML-ek célmappája."./felismert_szovegek"

padding A sorok körüli vágási ráhagyás (margó) pixelben.

## Kimenet

A folyamat lezárulta után a kimeneti mappában minden eredeti képhez két fájl jön létre:

Egy .txt fájl: Amely a teljes oldal összefüggő, olvasható szövegét tartalmazza.

Egy .xml fájl (PageXML): Amely tartalmazza a fizikai koordinátákat és a beléjük injektált felismert szöveget is.

Ez a formátum közvetlenül importálható professzionális HTR szoftverekbe (pl. eScriptorium, Transkribus).
