<div align="center">

<img src="logo.png" alt="Logo LF — Motorsport Data Engineering" width="160">

# Motorsport Data Engineering
### by Lorenzo Ferri

*Analisi quantitativa della Formula 1 — passo gara, telemetria e strategia gomme,
letti con il metodo di un ingegnere dell'automazione.*

![Sito statico](https://img.shields.io/badge/architettura-sito%20statico-B32020)
![Dati](https://img.shields.io/badge/dati-FastF1%20(dal%202018)-1b1f24)
![Hosting](https://img.shields.io/badge/hosting-GitHub%20Pages-4a90a4)


**[➜ Apri il sito](https://inglorenzoferri.github.io/Motorsport-Data-Engineering---Lorenzo-Ferri/)**

</div>

---

## Cos'è

Un sito di analisi dati Formula 1 costruito da zero: niente aggregatori,
niente dati copiati da altri siti. Una pipeline Python interroga il
live-timing ufficiale F1 tramite la libreria [FastF1](https://docs.fastf1.dev),
precalcola i dati di ogni sessione (prove libere, qualifiche, sprint, gara)
e li pubblica come file JSON statici. Il sito li visualizza con grafici
interattivi; l'interpretazione tecnica dei dati è mia.

## Cosa mostra

| Sezione | Contenuto | Uso analitico |
|---|---|---|
| **Passo gara** | mediana e deviazione standard dei tempi sul giro per pilota, sui giri rappresentativi | confronto del ritmo reale, al netto di pit-stop e giri anomali |
| **Telemetria** | velocità, RPM, acceleratore, freno, marcia e DRS sul giro più veloce, in funzione della distanza percorsa | confronto tra piloti su punti di frenata, trazione e velocità di punta |
| **Strategia gomme** | ricostruzione stint per stint: mescola, giro di inizio/fine, durata | lettura delle strategie e del degrado |
| **Dati avanzati** | classifica di sessione, bandiere/regime di gara, tabella giri completa (settori, trappole di velocità, età gomma) | analisi libera, con export **CSV** per Excel / pandas / MATLAB |

## Architettura

Il principio: i dati di una sessione F1 sono **immutabili** una volta
conclusa la sessione. Ricalcolarli a ogni visita richiederebbe un server
sempre acceso; precalcolarli una sola volta li rende servibili come file
statici — zero server, zero costi, superficie di attacco minima.

```mermaid
flowchart LR
    A["Live timing F1"] -->|FastF1| B["Pipeline Python<br/>(GitHub Actions)"]
    B -->|JSON + CSV precalcolati| C["Repository"]
    C -->|GitHub Pages| D["Sito statico<br/>Plotly.js"]
    D --> E["Analisi e<br/>interpretazione"]
```

Per aggiungere una sessione: scheda **Actions → Genera dati sessione F1 →
Run workflow**, indicando anno, Gran Premio e sessione. Il workflow scarica
i dati, li committa e il sito si aggiorna automaticamente.

## Fonte dati e limiti dichiarati

- **Fonte**: [FastF1](https://docs.fastf1.dev), libreria open-source non
  ufficiale che espone i dati del live-timing F1. Copertura telemetria e
  posizione: **dal 2018**.
- **Cosa non esiste in nessuna fonte pubblica**: i dati di *assetto* in
  senso proprio (angoli alari, setup sospensioni, mappe motore) sono
  proprietà riservata dei team. I canali mostrati qui (velocità, RPM,
  acceleratore, freno, DRS) sono **proxy indiretti** derivati dalla
  telemetria pubblica.

## Scelte tecniche di sicurezza e privacy

- Sito **interamente statico**: nessun server applicativo esposto, nessun
  database, nessun input elaborato lato server.
- **Content-Security-Policy** rigorosa (`default-src 'self'`): il browser
  del visitatore non contatta alcuna terza parte.
- Nessun cookie, nessun tracciamento, nessuna pubblicità.

## Stack

`Python` · `FastF1` · `pandas` · `GitHub Actions` · `HTML/CSS/JS` ·
`Plotly.js` · `GitHub Pages`

## Autore

**Lorenzo Ferri** —Ingegnere dell'Automazione e
dei Sistemi di Controllo. La pagina *Chi sono* del sito racconta il resto.

## Note legali

Progetto personale, non affiliato a Formula 1. I marchi F1, FORMULA ONE,
FIA FORMULA ONE WORLD CHAMPIONSHIP e GRAND PRIX sono di proprietà di
Formula One Licensing B.V. FastF1 è un progetto non ufficiale dei
rispettivi autori.
