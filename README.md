# Keyword Scraper V1 by BoCry69

Ein schneller, asynchroner Keyword‑Scraper mit klarer, übersichtlicher Oberfläche, 5 aktivierbaren Such‑Engines, A–Z/0–9‑Expansion sowie integriertem Proxy‑Manager (Import, Test, Geschwindigkeit, Timeout).

---

## Badges
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![GUI](https://img.shields.io/badge/GUI-PySide6-41CD52?logo=qt&logoColor=white)
![Async](https://img.shields.io/badge/Async-aiohttp-005571)
![License](https://img.shields.io/badge/License-MIT-informational)

<img width="912" height="790" alt="Bildschirmfoto 2025-09-09 um 14 13 57" src="https://github.com/user-attachments/assets/73b04021-2d96-4388-9179-7addaca72973" />
---

## Inhalt
- Überblick
- Funktionen
- Installation
- Start
- Verwendung
- Tipps für mehr Ergebnisse
- Projektstruktur
- Konfiguration
- Lizenz
- Support

---

## Überblick
Keyword Scraper V1 by BoCry69 kombiniert hohe Ergebnisabdeckung mit schlanker UI. Mehrere Engines, A–Z/0–9‑Expansion und Multi‑Client‑Abfragen liefern viele Keyword‑Varianten. Der Proxy‑Manager prüft Proxies parallel und nutzt automatisch nur funktionierende.

---

## Funktionen
- Engines (einzeln aktivierbar):
  - Google (Multi‑Client, A–Z/0–9‑Expansion)
  - Bing (mit Expansion)
  - DuckDuckGo
  - YouTube
  - Amazon‑Style (produktfokussierte Vorschläge)
- Ergebnis‑Boost:
  - A–Z/0–9‑Expansion pro Keyword
  - Multi‑Client für Google (chrome, firefox, safari, toolbar)
- Proxy‑Manager:
  - Import aus Textfeld oder Datei
  - Paralleler Test (fast/medium/slow)
  - Einstellbares Timeout (Sekunden)
  - Nutzung ausschließlich funktionierender Proxies
- Performance:
  - Asynchron (aiohttp)
  - Konfigurierbare Parallelität/Threads
  - Kurze Zufalls‑Delays gegen Rate‑Limits
- UI:
  - Ein Seite, klare Gruppen (Scraper links, Proxy rechts, Ergebnisse unten)
  - Export (TXT/CSV)

---

## Installation
Voraussetzungen:
- Python 3.10 oder neuer
- Windows/macOS/Linux

Virtuelles Environment (empfohlen):
- Windows
