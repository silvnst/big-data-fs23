# BigData Project FS23
<img width="1021" alt="Bildschirmfoto 2023-05-31 um 10 24 02" src="https://github.com/dennissio/bigdata-fs23/assets/25956086/362ef6d1-5f72-44ee-a2f0-6811dbdf7913">

In Anlehnung an das CRISP-DM Modell ist die Idee des Projekts, basierend auf den verfügbaren Daten der SBB, Vorhersagen über Zugverspätungen zu machen. Dies sollte Kunden ermöglichen bessere Entscheide zu fällen, bei der Wahl ihrer Fortbewegungsmittel. Es gibt jeweils zwei Ansätze bei dem Projekt: Ansatz 1 beinhaltet nur Wetterinformationen und Feiertage, Ansatz 2 beinhaltet Wetterinformationen, Feiertage und Störungen. Diese Unterscheidung musste vorgenommen werden, weil die Twitter nur begrenzt Daten herausgibt, in der App teilweise Anfragen blockiert werden und somit keine Prediction möglich wäre.

## Vorgehen
### Geschäftsverständnis & Datenverständnis
1. Suche nach relevanten Datasets zur Analyse des Phänomens.

### Datenbereinigung
1. Verarbeitung der Daten in einem Dataset
2. Cleaning von Dataset

### Modellierung & Evaluierung
1. Erstellung von Modellierungen für Regressionsanalyse (RandomForest, XGBoost)
2. Hyperparameteroptimierung auf verschiedenen Modellen
3. Evaluierung von optimierten Modellen
4. Speicherung von finalem Modell und Dataset

### Bereitstellung (deployed mit Ansatz 1)
1. Erstellung von App mit Zugverbindungen aus der Vergangenheit
2. Anknüpfung von Schnittstellen für real-time Berechnung von Verspätungen <br>
**[zu unserer App](https://dennissio-bigdata-fs23-appapp-e3nsze.streamlit.app)**

## Daten
Historische SBB Transportdaten pro Tag (Datenextrakt durch scraping): https://opentransportdata.swiss/de/ist-daten-archiv/ <br>
Historische Wetterdaten des Bundes (manueller Export): https://gate.meteoswiss.ch/idaweb/login.do <br>
Feiertage pro Haltestelle (manueller Export): https://opendata.swiss/dataset/haltestelle-feiertage <br>
Twitter mit Störungsinformationen (Scraper: https://github.com/JustAnotherArchivist/snscrape): https://twitter.com/railinfo_sbb <br>

## Real-Time Informationen (API, Scraping)
Open Journey Planner zur Suche von Zugverbindungen (xml-Request): https://opentransportdata.swiss/de/dataset/ojp2020 <br>
Open weather data mit Wettervorhersage für 5 Tage (json-Request): https://openweathermap.org/forecast5 <br> 
Twitter mit Störungsinformationen (Scraper: https://github.com/JustAnotherArchivist/snscrape): https://twitter.com/railinfo_sbb <br>

## Ordnerstruktur
Der Ordner ist wie folgt gegliedert:

**Hauptordner**: Beinhaltet sämtliche .ipynb zur Datensammlung (scraping) und Datenvorbereitung, wobei Unterschieden wird ob Twitterdaten inkludiert sind oder nicht <br>
**App**: Beinhaltet alle benötigten Inhalte für die App <br>
  **Modell**  Beinhaltet gespeicherte Modelle für Prediction <br>
  **Daten** Beinhaltet alle relevanten Daten zur Erstellung der Modells und App <br>
  **img** Beinhaltet Bilder zur Erstellung der App <br>
  **pages** Beinhaltet weitere Inhalte für die Applikation <br>
  **helper** Beinhaltet zusätzliche Funktionen für die App (z.B. API Anfrage) <br>
  
