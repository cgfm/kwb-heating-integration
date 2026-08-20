# KWB Modbus Register — Nachschlagewerk

**Software-Version:** v25.7.1 (DE) · **Quelle:** `custom_components/kwb_heating/config/versions/v25.7.1/de/`  
**Generiert:** Tabellen aus den JSON-Definitionen der Integration; das **Glossar** wurde zusätzlich aus öffentlichen KWB-Quellen ergänzt (siehe Quellenliste am Ende des Glossars).  
**Hinweis:** Die *Erklärungs*-Spalte ist bei nicht selbsterklärenden Begriffen leer (`—`) bzw. im Glossar separat markiert. KWB liefert in den Modbus-Tabellen nur das *Name*-Feld als Beschreibung; alles, was darüber hinausgeht, ist im Glossar mit Konfidenz-Stufe (✓ verifiziert / ~ wahrscheinlich / ? nicht belegt) markiert. **Spekulationen ohne Quelle sind als solche gekennzeichnet.**

## Inhaltsverzeichnis

- [Lesehilfe](#lesehilfe)
- [Glossar (offene Begriffe)](#glossar-offene-begriffe)
- [Universal-Register](#universal-register)
- [Heizkreise (HK)](#heizkreise-hk)
- [Pufferspeicher (PUF)](#pufferspeicher-puf)
- [Brauchwasserspeicher (BWS)](#brauchwasserspeicher-bws)
- [Zweitwärmequellen (ZWQ)](#zweitwarmequellen-zwq)
- [Zirkulation (ZIR)](#zirkulation-zir)
- [Solar (SOL)](#solar-sol)
- [Kesselfolgeschaltung (KFS)](#kesselfolgeschaltung-kfs)
- [Wärmemengenzähler (WMZ)](#warmemengenzahler-wmz)
- [Übergabestation (ÜGS)](#ubergabestation-ugs)
- [Geräte-spezifische Register](#gerate-spezifische-register)
- [Wertetabellen](#wertetabellen)
- [Anhang A — Vollständige Adressliste](#anhang-a--vollstandige-adressliste)

## Lesehilfe

**Spalten der Hauptabschnitte:**

| Spalte | Bedeutung |
|---|---|
| **Name** | Anzeigename laut KWB Modbus-Tabelle. |
| **Parameter** | Interner KWB-Parameterpfad (z. B. `KSM.kesselstatus_anzeige`). |
| **Adresse(n)** | Modbus-Startadresse. Mehrere Slots werden als Bereich `start…ende (×Anzahl, ΔSchrittweite)` angegeben. |
| **Typ** | Datentyp (`u16`, `s16`, `u32`, `s32`) plus Modbus-Funktionscode-Klasse: `Holding` (FC03/06/16, schreibbar) oder `Input` (FC04, nur lesend). |
| **Optionen / Wertebereich** | Wertetabelle mit allen erlaubten Werten, oder Einheit (z. B. `1/10°C`), oder `min`/`max`. |
| **User** | Berechtigung im Benutzer-Level: `r`=lesen, `rw`=lesen+schreiben, `–`=nicht zugänglich. |
| **Expert** | Berechtigung im Experten-Level. |
| **Erklärung** | Selbsterklärende Begriffe sind leer. Nicht-selbsterklärende Begriffe stehen im **Glossar** und sind hier mit `→ Glossar` markiert. |

**Modbus-Funktionscodes:** `04` = Input Register (nur lesend), `03` = Holding Register (lesend + schreibbar via FC06/FC16). Ein Register mit `expert_level=readwrite` und `data_type=03` ist also schreibbar — auf Userlevel sind die meisten dieser Register schreibgeschützt.

**Slot-Indizes:** Heizkreise verwenden zweistufige Indizes (`HK 1.1`, `HK 1.2`, `HK 2.1`, …), die anderen Equipments einstufige (`PUF 0`, `BWS 1`, `ÜGS 1`, …).

## Glossar (offene Begriffe)

Begriffe, die im Repo nicht weiter dokumentiert sind. Erklärungen wurden aus den Wertetabellen / dem Code abgeleitet **und durch Recherche in öffentlichen KWB-Quellen ergänzt** (siehe Quellenliste unten). Konfidenz-Stufen:

- **✓ verifiziert** — Bedeutung in offizieller KWB-Quelle oder gut belegter Community-Doku gefunden.
- **~ wahrscheinlich** — plausible Ableitung aus Kontext, branchenüblicher Bedeutung oder indirekten Belegen.
- **? nicht belegt** — keine zitierfähige Quelle gefunden; die offizielle KWB `ModbusInfo-de-Vxx.x.xlsx` (mit SD-Karte ausgeliefert oder via `office@kwb.net` anforderbar) enthält die definitiven Kurzbeschreibungen.

### Komponenten / Module

| Begriff | Bedeutung | Konfidenz |
|---|---|:-:|
| **BGE** | **Bediengerät Exclusiv** — Touch-Bedienteil der KWB-Comfort-4-Steuerung. Modbus-Register `BGE Seriennummer` / `BGE Software-Version` beziehen sich auf das Bedienpanel, nicht auf den Kessel. [1] | ✓ |
| **WMM** | **Wärmemanagement-Modul** — autonome Sub-Steuereinheit für 2 Heizkreise; eingesetzt, wenn der Kessel räumlich entfernt vom Verteiler steht. *Nicht* „Wärmemengenmodul". [2][3] | ✓ |
| **WMM Rolle** | Welche Rolle das WMM in der Anlage übernimmt: `0=Autonom, 1=KFS, 2=Powerfire 1 150-300kW, 3=EasyAir Plus, 4=Powerfire 2 400-500kW`. | ✓ |
| **KFS** | **Kesselfolgeschaltung** — Kaskade von bis zu 8 Kesseln (Comfort-3 und Comfort-4 mischbar). [4] | ✓ |
| **EAP** | **EasyAir Plus** — Luft/Wasser-Wärmepumpen-Monoblock von KWB; `eap_zustand_t` ist der Geräte-Zustand. [5] | ✓ |
| **Clee** | KWB-eigenes **Energiemanagementsystem** (eigene Marke / Hardware). Steuert PV-Eigenverbrauch, Heizstab, Wärmepumpe und Kessel; Anbindung an Wechselrichter (Fronius, Huawei, SMA, Kostal). „Clee Status" = Statusrückmeldung des Clee-Geräts. [6][7] | ✓ |
| **FBR** | **Fernbedienung Raum(einheit)** — Wand-Bedienelement im Wohnraum pro Heizkreis (analog oder digital). [3] | ✓ |
| **MFA** | Vermutlich **Multifunktions-Aktor**: Schaltausgang in den C4-Anschlussplänen (Solar-/Zubringerpumpe, Zirkulation, PV-Überschuss-Anforderung). Abkürzung in öffentlichen KWB-PDFs nicht namentlich aufgelöst. | ~ |
| **KFK** | Wahrscheinlich **Kessel-Folge-Kaskade** (Untermenge von KFS). `kfk_kesselstatus_t` ist plausibel der Kessel-Status innerhalb der Kaskade. [4] | ~ |
| **KSM** | Parameter-Präfix `KSM.*` für anlagenweite Alarme/Störungen. Auflösung der Abkürzung in öffentlichen Quellen nicht zitierfähig gefunden. | ? |
| **AK** | Parameter-Präfix `AK.*` und `ak_*_t`-Wertetabellen. Vermutlich anlagenweite Konfigurations-/Sollwerte (z. B. `ak_externe_vorgabe`, `ak_kesselprogramm`). Nicht in öffentlicher KWB-Doku auflösbar. | ? |
| **SAN Code** | Seriennummern-Codeziffer (vermutet). KWB Comfort Online kennt Service-Codes (z. B. 100=Teilzugriff, 235=Fachmann), ein „SAN-Code" ist aber nicht öffentlich dokumentiert. | ? |
| **FAS** | Branchenüblich „Fernfühler / Anlegesensor"; im KWB-Kontext nicht zitierfähig belegt. | ? |

### Komponenten-Kürzel (Abschnitts-Präfixe)

| Kürzel | Bedeutung | Konfidenz |
|---|---|:-:|
| **HK** | Heizkreis | ✓ |
| **PUF** | Pufferspeicher | ✓ |
| **BWS** / **BOI** | Brauchwasserspeicher (Boiler) | ✓ |
| **ZWQ** | Zweitwärmequelle (z. B. Wärmepumpe parallel) | ~ |
| **ZIR** | Zirkulationspumpe (Warmwasser-Zirkulation) | ~ |
| **SOL** | Solar / Solarthermie | ~ |
| **WMZ** | Wärmemengenzähler | ~ |
| **ÜGS** | Übergabestation | ~ |

### Funktionen / Register

| Begriff | Bedeutung | Konfidenz |
|---|---|:-:|
| **Externe Vorgabe** | Solloptionen für **Kesselsolltemperatur** oder **Kesselleistung** über Digitaleingang/Modbus. Werte: `0=Aus, 1=Temperatur, 2=Leistung, 3=Modbus, 4=Modbus` (3/4 wahrscheinlich getrennt für Modbus-Temperatur und Modbus-Leistung). KWB-Hinweis: nur aktivieren, wenn beide Sollwerte tatsächlich vorgegeben werden. [3] | ✓ |
| **Modbus Lifetick** | Heartbeat-Zähler, der vom Master regelmäßig beschrieben werden muss, damit der Kessel die Modbus-Verbindung als „lebend" erkennt. | ✓ |
| **Modbus Lifetick … ignorieren** | Wenn aktiv, wird das Fehlen des Lifeticks für die jeweilige Komponente (Kessel, Heizkreise, Solar, ZWQ, …) **nicht** als Fehler gewertet. | ✓ |
| **Modbus Commit Lifetick** | Vermutlich Echo-/Bestätigungs-Heartbeat des Kessels zur Modbus-Master-Seite (Quittung der Übernahme). Keine zitierfähige öffentliche KWB-Definition gefunden. | ~ |
| **Modbus Überhitzung** | Modbus-Eingang zur Meldung externer Überhitzung (z. B. Master signalisiert: Puffer überhitzt → bitte abregeln). KWB-Erklärung nicht öffentlich belegt. | ~ |
| **Modbus Überstromnutzung** | Sehr wahrscheinlich **PV-Überschussstrom-Nutzung** (Power-to-Heat: Heizstab/Wärmepumpe nimmt PV-Überschuss auf, oft via Clee-Energiemanagement). KWB bietet dafür „PV Heat" und Clee-Anbindung an. [8] | ~ |
| **Modbus Kesselanforderung** | Modbus-Schreibregister, mit dem ein externes System eine Kesselanforderung setzen kann. | ✓ |
| **Modbus Anforderung** | Analog zu „Modbus Kesselanforderung", aber auf Heizkreis-/Verbraucherebene (`HK.modbus_anforderung`, `PUF.heizstab_modbus_anforderung`, …). | ✓ |
| **Alarme beheben** | Schreibbares Register: Setzen quittiert ausstehende Alarme von extern. | ✓ |
| **Anlage OK** | Boolean: Anlage hat weder Alarm noch Störung (`KSM.anlage_kein_alarm_keine_stoerung`). | ✓ |
| **Summenstörung** | Sammelmeldung: irgendein Alarm oder Störung im System aktiv. | ✓ |
| **Summenstörung mit Kesselabschaltung** | Sammelmeldung; die Störung führt zusätzlich zur Außerbetriebnahme des Kessels. | ✓ |
| **Glutbett** | Glühende Brennstoff-Schicht auf dem Schubrost (Multifire/Combifire). Glutbettfühler mit Min-/Max- und Zünd-Schwellen; zu niedriger Wert ⇒ zu wenig Brennstoff im Brennraum, keine Volllast. [9] | ✓ |

### Quellen

1. KWB Comfort-Online-Hilfe (Fehlercodes 20.07/20.08 nennen explizit „BGE-Software-Version" / „BGE-Seriennummer"): https://comfort-online.com/Content/info/help_de.html
2. KWB Comfort 4 Wärmemanagement-Modul (Produktbeschreibung): https://www.wolf-online-shop.de/KWB-Comfort-4-Waermemanagement-Modul-fuer-2-Heizkreise::363401.html
3. Community-Doku „KWB Easyfire via Modbus" (zitiert offizielle KWB-Modbus-Schnittstellenbeschreibung): https://book.amrhein.info/books/kwb-easyfire-via-modbus
4. KWB Technik & Planung — Modul H Kaskaden-Lösungen (04/2025, EN): https://www.kwb.net/fileadmin/media/EN/Technik_Planung_Anleitungen_PDF/KWB_T_P_EN_04_2025_Modul_H_KWB_Cascade_solutions.pdf
5. KWB EasyAir Plus Wärmepumpe (Produktseite): https://www.kwb.net/de-at/heizungen/waermepumpen/kwb-easyair-plus
6. Clee-Energy (KWB-Energiemanagement): https://www.clee-energy.net/
7. Clee Bedienungsanleitung (DE): https://www.kwb.net/fileadmin/clee/Clee_Bedienungsanleitung_DE.pdf
8. KWB Power-to-Heat / PV-Eigenstromnutzung: https://www.kwb.net/de-at/heizwissen/service-komfort/power-to-heat/
9. Forum-Diskussion „KWB Multifire 100 Hackschnitzel ohne Leistung" mit Beschreibung des Glutbettfühlers: https://www.landwirt.com/Forum/400533/KWB-Multifire-100-Hackschnitzel-ohne-Leistung.html
10. KWB Technik & Planung — Modul I Regelung (04/2025, AT): https://www.kwb.net/fileadmin/media/AT/Technik___Planung/KWB_T_P_04_2025_AT_Modul_I_KWB_Regelung.pdf

> **Definitiv klären lassen:** Für die mit `?`/`~` markierten Begriffe enthält die offizielle KWB-Datei `ModbusInfo-de-Vxx.x.xlsx` (mit dem Boiler auf SD-Karte ausgeliefert oder per Mail von `office@kwb.net` mit Software-Version anforderbar) pro Register eine verbindliche Kurzbeschreibung.

## Universal-Register

*22 eindeutige Registertypen.*

| Name | Parameter | Adresse(n) | Typ | Optionen / Wertebereich | User | Expert | Erklärung |
|---|---|---|---|---|:---:|:---:|---|
| Software (major) | `SYSTEM.sw_version.major` | 8192 | u16 / Input (FC04) | — | r | r |  |
| Software (minor) | `SYSTEM.sw_version.minor` | 8193 | u16 / Input (FC04) | — | r | r |  |
| Software (patch) | `SYSTEM.sw_version.patch` | 8194 | u16 / Input (FC04) | — | r | r |  |
| Revision | `SYSTEM.sw_revision` | 8195 | u32, 2 Reg. / Input (FC04) | — | r | r |  |
| Anlage OK | `KSM.anlage_kein_alarm_keine_stoerung` | 8204 | s16 / Input (FC04) | Einheit: `system_yes_no_t` | r | r | → Glossar |
| Summenstörung | `KSM.summen_alarm_oder_stoerung` | 8205 | s16 / Input (FC04) | Einheit: `system_yes_no_t` | r | r | → Glossar |
| Anzahl Alarme | `SYSTEM.alarme_total` | 8252 | u32, 2 Reg. / Input (FC04) | — | r | r |  |
| Anzahl offene Alarme | `SYSTEM.alarme_offen` | 8254 | u32, 2 Reg. / Input (FC04) | — | r | r |  |
| Summenstörung mit Kesselabschaltung | `KSM.anlage_stoerung_mit_abschaltung` | 10022 | s16 / Input (FC04) | Einheit: `system_yes_no_t` | r | r | → Glossar |
| Kesseltyp | `SYSTEM.gui_kessel_typ` | 10024 | s16 / Input (FC04) | `system_gui_kessel_typ_t` → 0=-, 1=KWB Easyfire, 2=KWB CF 2, 3=KWB Combifire, 4=KWB Multifire, … (+6) | r | r |  |
| WMM Rolle | `SYSTEM.wmm_rolle` | 10025 | s16 / Input (FC04) | `wmm_rolle_t` → 0=Autonom, 1=KFS, 2=Powerfire 1 150-300kW, 3=EasyAir Plus, 4=Powerfire 2 400-500kW | r | r | → Glossar |
| BGE | `SYSTEM.bge_serial_number` | 10228 | u32, 2 Reg. / Input (FC04) | — | r | r | → Glossar |
| Alarme beheben | `SYSTEM.alarme_beheben_von_extern` | 24582 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | rw | rw | → Glossar |
| Modbus Lifetick Kessel ignorieren | `SYSTEM.modbus_lifetick_ignore_kessel` | 25159 | s16 / Holding (FC03/06/16) | Einheit: `system_yes_no_t` | r | rw | → Glossar |
| Modbus Lifetick Heizkreise ignorieren | `SYSTEM.modbus_lifetick_ignore_hk` | 25160 | s16 / Holding (FC03/06/16) | Einheit: `system_yes_no_t` | r | rw | → Glossar |
| Modbus Lifetick Solaranlagen ignorieren | `SYSTEM.modbus_lifetick_ignore_solar` | 25161 | s16 / Holding (FC03/06/16) | Einheit: `system_yes_no_t` | r | rw | → Glossar |
| Modbus Lifetick Zweitwärmequellen ignorieren (Wärmepumpe oder Kessel) | `SYSTEM.modbus_lifetick_ignore_zwq` | 25162 | s16 / Holding (FC03/06/16) | Einheit: `system_yes_no_t` | r | rw | → Glossar |
| Modbus Lifetick Zusatzwärmequellen ignorieren | `SYSTEM.modbus_lifetick_ignore_zuswq` | 25163 | s16 / Holding (FC03/06/16) | Einheit: `system_yes_no_t` | r | rw | → Glossar |
| Modbus Lifetick Überschussstromkontakt (MFA) ignorieren | `SYSTEM.modbus_lifetick_ignor_uestrommfa` | 25164 | s16 / Holding (FC03/06/16) | Einheit: `system_yes_no_t` | r | rw | → Glossar |
| SAN Code | `SYSTEM.kessel_seriennummer_san_code` | 25165 | s16 / Holding (FC03/06/16) | `kesselseriennummer_san_code_t` → 0=..., 1=000-, 2=02SAN, 3=03SAN, 4=04SAN, … (+46) | r | r | → Glossar |
| Seriennummer | `SYSTEM.kessel_seriennummer` | 25166 | u32, 2 Reg. / Holding (FC03/06/16) | — | r | r |  |
| Modbus Lifetick Wärmepumpe ignorieren | `SYSTEM.modbus_lifetick_ignore_wp` | 25304 | s16 / Holding (FC03/06/16) | Einheit: `system_yes_no_t` | r | rw | → Glossar |

## Heizkreise (HK)

*17 eindeutige Registertypen.*

| Name | Parameter | Adresse(n) | Typ | Optionen / Wertebereich | User | Expert | Erklärung |
|---|---|---|---|---|:---:|:---:|---|
| Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | 8260…8314 (×28, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | 8261…8315 (×28, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | 8328…8355 (×28) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | 8365…8419 (×28, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | 8366…8420 (×28, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Außentemperatur (value) | `HK.i_aussen_temperatur.value` | 8435…8489 (×28, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Außentemperatur (status) | `HK.i_aussen_temperatur.status` | 8436…8490 (×28, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Pumpe | `HK.o_pumpe` | 8503…8530 (×28) | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Raumtemperatur Soll | `HK.raum_temperatur_soll` | 8538…8565 (×28) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Status | `HK.status` | 8573…8600 (×28) | s16 / Input (FC04) | `hk_status_t` → 0=Absenk, 1=Komfort, 2=Frostschutz, 3=Urlaub, 4=Aus, … (+10) | r | r |  |
| Programm wählen | `HK.programm` | 24589…24616 (×28) | s16 / Holding (FC03/06/16) | `hk_programm_t` → 0=Automatik, 1=Frostschutz, 2=Aus, 3=Komfort, 4=Absenk | rw | rw |  |
| Komforttemperatur | `HK.raum_temperatur_soll_tag` | 24624…24651 (×28) | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | rw | rw |  |
| Absenktemperatur | `HK.raum_temperatur_soll_nacht` | 24659…24686 (×28) | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | rw | rw |  |
| Modbus Anforderung | `HK.modbus_anforderung` | 24859…24886 (×28) | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | rw | → Glossar |
| Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | 24894…24921 (×28) | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| HK Sollvorgabe | `KSM.hk_modbus_temperatur_auswahl` | 24936 | s16 / Holding (FC03/06/16) | `hk_modbus_temperatur_auswahl_t` → 0=Vorlauftemp. Soll, 1=Raumtemp. Soll | r | rw |  |
| Modbus Programm | `HK.modbus_programm` | 24939…24966 (×28) | s16 / Holding (FC03/06/16) | `hk_modbus_programm_t` → 0=Frostschutz, 1=Absenk  auto, 2=Komfort auto, 3=Absenk, 4=Komfort | r | rw |  |

## Pufferspeicher (PUF)

*23 eindeutige Registertypen.*

| Name | Parameter | Adresse(n) | Typ | Optionen / Wertebereich | User | Expert | Erklärung |
|---|---|---|---|---|:---:|:---:|---|
| Temperatur 1 (value) | `PUF.i_ist_temperatur_1.value` | 8708…8736 (×15, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Temperatur 1 (status) | `PUF.i_ist_temperatur_1.status` | 8709…8737 (×15, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Temperatur 2 (value) | `PUF.i_ist_temperatur_2.value` | 8742…8770 (×15, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Temperatur 2 (status) | `PUF.i_ist_temperatur_2.status` | 8743…8771 (×15, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Temperatur 3 (value) | `PUF.i_ist_temperatur_3.value` | 8776…8804 (×15, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Temperatur 3 (status) | `PUF.i_ist_temperatur_3.status` | 8777…8805 (×15, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Temperatur 4 (value) | `PUF.i_ist_temperatur_4.value` | 8810…8838 (×15, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Temperatur 4 (status) | `PUF.i_ist_temperatur_4.status` | 8811…8839 (×15, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Temperatur 5 (value) | `PUF.i_ist_temperatur_5.value` | 8844…8872 (×15, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Temperatur 5 (status) | `PUF.i_ist_temperatur_5.status` | 8845…8873 (×15, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Pumpe | `PUF.o_pumpe` | 8878…8892 (×15) | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Anforderung | `PUF.anforderung` | 8895…8909 (×15) | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Umschaltventil | `PUF.o_umschaltventil` | 8912…8926 (×15) | s16 / Input (FC04) | `puffer_o_umschaltventil_t` → 0=Nicht vorhanden, 1=Oben, 2=Unten | r | r |  |
| Verbraucher Soll | `GRP.verbraucher_anf_temperatur` | 9971…9985 (×15) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Anforderung Heizstab | `PUF.o_heizstab_anforderung` | 10058…10072 (×15) | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Temperatur bei Heizstab (value) | `PUF.i_temp_heizstab_bei_sensorwahl.value` | 10075…10103 (×15, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Temperatur bei Heizstab (status) | `PUF.i_temp_heizstab_bei_sensorwahl.status` | 10076…10104 (×15, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Programm wählen | `PUF.programm` | 24760…24774 (×15) | s16 / Holding (FC03/06/16) | `puffer_programm_t` → 0=Zeit, 1=Temperatur, 2=Aus, 3=Zeit+, 4=Sommer | rw | rw |  |
| Temperatur Min/Max (min) | `PUF.temperatur_grenzen.min` | 24777…24805 (×15, Δ2) | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | rw | rw |  |
| Temperatur Min/Max (max) | `PUF.temperatur_grenzen.max` | 24778…24806 (×15, Δ2) | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | rw | rw |  |
| Brauchwassertemp. min. | `PUF.brauchwassertemp_min` | 24811…24825 (×15) | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | rw | rw |  |
| Max. Temperatur Heizstab | `PUF.heizstab_temperatur_max` | 25057…25071 (×15) | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Anforderung Heizstab | `PUF.heizstab_modbus_anforderung` | 25074…25088 (×15) | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | rw | → Glossar |

## Brauchwasserspeicher (BWS)

*24 eindeutige Registertypen.*

| Name | Parameter | Adresse(n) | Typ | Optionen / Wertebereich | User | Expert | Erklärung |
|---|---|---|---|---|:---:|:---:|---|
| Temperatur Ist (value) | `BOI.i_ist_temperatur.value` | 8608…8634 (×14, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Temperatur Ist (status) | `BOI.i_ist_temperatur.status` | 8609…8635 (×14, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Ladepumpe | `BOI.o_pumpe` | 8641…8654 (×14) | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Anforderung | `BOI.anforderung` | 8658…8671 (×14) | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Temperatur Soll | `BOI.soll_temperatur` | 8675…8688 (×14) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Status | `BOI.status` | 8692…8705 (×14) | s16 / Input (FC04) | `boiler_status_t` → 0=Störung, 1=Aus, 2=Legionellenschutz, 3=Urlaub, 4=Einmalladung, … (+12) | r | r |  |
| Temperatur 2 (value) | `BOI.i_ist_temperatur_2.value` | 9433…9459 (×14, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Temperatur 2 (status) | `BOI.i_ist_temperatur_2.status` | 9434…9460 (×14, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Anforderung Heizstab | `BOI.o_heizstab_anforderung` | 10110…10123 (×14) | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Temperatur bei Heizstab (value) | `BOI.i_temp_heizstab_bei_sensorwahl.value` | 10128…10154 (×14, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Temperatur bei Heizstab (status) | `BOI.i_temp_heizstab_bei_sensorwahl.status` | 10129…10155 (×14, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Anforderung Wärmepumpe | `BOI.o_waermepumpe_anforderung` | 10161…10174 (×14) | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Speichertemp. Wärmepumpe (value) | `BOI.i_temp_waermepumpe_bei_senswahl.value` | 10179…10205 (×14, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Speichertemp. Wärmepumpe (status) | `BOI.i_temp_waermepumpe_bei_senswahl.status` | 10180…10206 (×14, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Status Wärmepumpe | `BOI.waermepumpe_status` | 10212…10225 (×14) | s16 / Input (FC04) | `zus_wq_wp_status_t` → 0=Aus, 1=Betrieb, 2=Mindestlaufzeit, 3=Mindeststehzeit | r | r |  |
| Programm wählen | `BOI.programm` | 24693…24706 (×14) | s16 / Holding (FC03/06/16) | `boiler_programm_t` → 0=Zeit, 1=Temp., 2=Aus | rw | rw |  |
| Temperatur Min/Max (min) | `BOI.temperatur_grenzen.min` | 24711…24737 (×14, Δ2) | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | rw | rw |  |
| Temperatur Min/Max (max) | `BOI.temperatur_grenzen.max` | 24712…24738 (×14, Δ2) | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | rw | rw |  |
| Brauchwasser 1x erhitzen | `BOI.schnellladung` | 24744…24757 (×14) | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | rw | rw |  |
| Max. Temperatur Heizstab | `BOI.heizstab_temperatur_max` | 25092…25105 (×14) | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Anforderung Heizstab | `BOI.heizstab_modbus_anforderung` | 25109…25122 (×14) | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | rw | → Glossar |
| Max. Temperatur Wärmepumpe | `BOI.waermepumpe_temperatur_max` | 25126…25139 (×14) | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Anf. Wärmepumpe | `BOI.waermepumpe_modbus_anforderung` | 25143…25156 (×14) | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | rw |  |
| Quelle | `BOI.quelle` | 25353…25366 (×14) | s16 / Holding (FC03/06/16) | `boiler_quelle_t` → 0=Wärmepumpe 1, 1=Puffer, 2=WP1 oder Puffer | r | r |  |

## Zweitwärmequellen (ZWQ)

*10 eindeutige Registertypen.*

| Name | Parameter | Adresse(n) | Typ | Optionen / Wertebereich | User | Expert | Erklärung |
|---|---|---|---|---|:---:|:---:|---|
| Kesselpumpe | `ZK.o_pumpe` | 8981…8994 (×14) | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Temperatur (value) | `ZK.i_temperatur.value` | 8998…9024 (×14, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Temperatur (status) | `ZK.i_temperatur.status` | 8999…9025 (×14, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Anforderung | `ZK.o_anforderung` | 9029…9042 (×14) | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Status | `ZK.status` | 9991…10004 (×14) | s16 / Input (FC04) | `zk_status_t` → 0=Aus, 1=Betrieb, 2=Überhitzung, 3=Verzögerung, 4=Störung, … (+3) | r | r |  |
| Störung | `ZK.i_stoerung` | 10007…10020 (×14) | s16 / Input (FC04) | Einheit: `system_yes_no_t` | r | r |  |
| Puffertemperatur (value) | `ZK.i_puffertemp_bei_sensor_auswahl.value` | 10028…10054 (×14, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Puffertemperatur (status) | `ZK.i_puffertemp_bei_sensor_auswahl.status` | 10029…10055 (×14, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Modbus Anforderung | `ZK.modbus_anforderung` | 25024…25037 (×14) | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | rw | → Glossar |
| Puffertemperatur Max. | `ZK.puffertemperatur_max` | 25042…25055 (×14) | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | r |  |

## Zirkulation (ZIR)

*4 eindeutige Registertypen.*

| Name | Parameter | Adresse(n) | Typ | Optionen / Wertebereich | User | Expert | Erklärung |
|---|---|---|---|---|:---:|:---:|---|
| Temperatur (value) | `ZIRK.i_temperatur.value` | 8929…8957 (×15, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Temperatur (status) | `ZIRK.i_temperatur.status` | 8930…8958 (×15, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Pumpe | `ZIRK.o_pumpe` | 8963…8977 (×15) | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Programm wählen | `ZIRK.programm` | 24828…24842 (×15) | s16 / Holding (FC03/06/16) | `zirk_programm_t` → 0=Aus, 1=Automatik, 2=Dauerbetrieb | rw | rw |  |

## Solar (SOL)

*27 eindeutige Registertypen.*

| Name | Parameter | Adresse(n) | Typ | Optionen / Wertebereich | User | Expert | Erklärung |
|---|---|---|---|---|:---:|:---:|---|
| Status | `SOL.status` | 9049…9062 (×14) | s16 / Input (FC04) | `solar_status_t` → 0=Aus, 1=Handbetrieb, 2=Laden Speicher 1, 3=Laden Speicher 2, 4=Störung, … (+4) | r | r |  |
| Statusursache | `SOL.status_ursache` | 9064…9077 (×14) | s16 / Input (FC04) | `solar_status_ursache_t` → 0=Programm Aus, 1=Handbetrieb, 2=Kollektortemperatur ausreichend, 3=Temperaturdifferenz Kollektor / Speicher 1 zu gering, 4=Maximaltemperatur Speicher 1 überschritten, … (+10) | r | r |  |
| Kollektortemperatur (value) | `SOL.i_kollektor_temperatur.value` | 9080…9106 (×14, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Kollektortemperatur (status) | `SOL.i_kollektor_temperatur.status` | 9081…9107 (×14, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Temperatur Speicher 1 (value) | `SOL.i_ist_temperatur_speicher_1.value` | 9110…9136 (×14, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Temperatur Speicher 1 (status) | `SOL.i_ist_temperatur_speicher_1.status` | 9111…9137 (×14, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Temperatur Speicher 2 (value) | `SOL.i_ist_temperatur_speicher_2.value` | 9140…9166 (×14, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Temperatur Speicher 2 (status) | `SOL.i_ist_temperatur_speicher_2.status` | 9141…9167 (×14, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Pumpe 1 | `SOL.o_pumpe_1` | 9169…9479 (×28, unregelm.) | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Pumpe 2 | `SOL.o_pumpe_2` | 9184…9494 (×28, unregelm.) | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Umschaltventil | `SOL.o_umschaltventil` | 9199…9212 (×14) | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Wärmeleistung | `SOL.waermeleistung` | 9215…9241 (×14, Δ2) | u32, 2 Reg. / Input (FC04) | Einheit: `1/1000kW` | r | r |  |
| Wärmemenge Tag | `SOL.waermemenge_tag` | 9245…9271 (×14, Δ2) | u32, 2 Reg. / Input (FC04) | Einheit: `1/1000kWh` | r | r |  |
| Wärmemenge gesamt | `SOL.waermemenge_gesamt_kwh` | 9275…9301 (×14, Δ2) | u32, 2 Reg. / Input (FC04) | Einheit: `1/1000kWh` | r | r |  |
| Kollektor Vorlauftemperatur (value) | `SOL.i_vorlauf_temperatur.value` | 9305…9331 (×14, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Kollektor Vorlauftemperatur (status) | `SOL.i_vorlauf_temperatur.status` | 9306…9332 (×14, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Kollektor Rücklauftemperatur (value) | `SOL.i_kollektor_ruecklauf_temperatur.value` | 9335…9361 (×14, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Kollektor Rücklauftemperatur (status) | `SOL.i_kollektor_ruecklauf_temperatur.status` | 9336…9362 (×14, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Durchfluss (value) | `SOL.i_kollektor_durchfluss.value` | 9365…9391 (×14, Δ2) | s16 / Input (FC04) | Einheit: `1/100l/min` | r | r |  |
| Durchfluss (status) | `SOL.i_kollektor_durchfluss.status` | 9366…9392 (×14, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Vorlauftemperatur Sekundär (value) | `SOL.i_vorlauf_temperatur_sekundaer.value` | 9882…9908 (×14, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Vorlauftemperatur Sekundär (status) | `SOL.i_vorlauf_temperatur_sekundaer.status` | 9883…9909 (×14, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Rücklauftemperatur Sekundär (value) | `SOL.i_ruecklauf_temperatur_sekundaer.value` | 9912…9938 (×14, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Rücklauftemperatur Sekundär (status) | `SOL.i_ruecklauf_temperatur_sekundaer.status` | 9913…9939 (×14, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Rücklauftemperatur Primär (value) | `SOL.i_ruecklauf_temperatur_primaer.value` | 9942…9968 (×14, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Rücklauftemperatur Primär (status) | `SOL.i_ruecklauf_temperatur_primaer.status` | 9943…9969 (×14, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Modbus Vorlauftemp. Soll | `SOL.modbus_vorlauf_temperatur_soll` | 25009…25022 (×14) | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |

## Kesselfolgeschaltung (KFS)

*31 eindeutige Registertypen.*

| Name | Parameter | Adresse(n) | Typ | Optionen / Wertebereich | User | Expert | Erklärung |
|---|---|---|---|---|:---:|:---:|---|
| Mittlere Puffertemp. | `KFS.mittlere_puffertemperatur` | 9394 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Pufferfüllgrad | `KFS.puffer_fuellgrad` | 9395 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Netzvorlauf (value) | `KFS.netz_vorlauf.value` | 9396 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Netzvorlauf (status) | `KFS.netz_vorlauf.status` | 9397 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Netzrücklauf (value) | `KFS.netz_ruecklauf.value` | 9398 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Netzrücklauf (status) | `KFS.netz_ruecklauf.status` | 9399 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Anf. Spitzenlastkessel | `KFS.o_anforderung_spitzenlastkessel` | 9400 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Anforderung | `KFK.o_anforderung` | 9402…9409 (×8) | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Störung | `KFK.i_stoerung` | 9422…9429 (×8) | s16 / Input (FC04) | Einheit: `system_yes_no_t` | r | r |  |
| Anlagen | `KFS.anzahl_kessel` | 9499 | u8 / Input (FC04) | — | r | r |  |
| Anlagen angefordert | `KFS.anzahl_angeforderte_kessel` | 9500 | s16 / Input (FC04) | `kfs_angeforderte_kessel_t` → 1=1, 2=2, 3=3, 4=4, 5=5, 6=6, 7=7, 8=8 | r | r |  |
| Puffersolltemperatur | `KFS.puffer_solltemperatur_anzeige` | 9501 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Puffer Temperatur 1 (value) | `KFS.puffer_temperatur_1.value` | 9502 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Puffer Temperatur 1 (status) | `KFS.puffer_temperatur_1.status` | 9503 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Puffer Temperatur 2 (value) | `KFS.puffer_temperatur_2.value` | 9504 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Puffer Temperatur 2 (status) | `KFS.puffer_temperatur_2.status` | 9505 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Puffer Temperatur 3 (value) | `KFS.puffer_temperatur_3.value` | 9506 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Puffer Temperatur 3 (status) | `KFS.puffer_temperatur_3.status` | 9507 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Puffer Temperatur 4 (value) | `KFS.puffer_temperatur_4.value` | 9508 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Puffer Temperatur 4 (status) | `KFS.puffer_temperatur_4.status` | 9509 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Puffer Temperatur 5 (value) | `KFS.puffer_temperatur_5.value` | 9510 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Puffer Temperatur 5 (status) | `KFS.puffer_temperatur_5.status` | 9511 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Außentemperatur gemittelt (value) | `KFS.i_aussen_temperatur_mittelwert.value` | 9512 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Außentemperatur gemittelt (status) | `KFS.i_aussen_temperatur_mittelwert.status` | 9513 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Störkontakt Dauer | `KFS.o_stoerung_dauer` | 9514 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Mittlere Durchladetemp. | `KFS.mittlere_durchladetemperatur` | 9515 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Pufferdurchladegrad | `KFS.puffer_durchladegrad` | 9516 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Puffersolltemperatur Winter | `KFS.puffer_solltemperatur_winter` | 24848 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | rw | rw |  |
| Kesselfolgeschaltung | `KFS.anlage_ein` | 24929 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | rw | rw |  |
| Aktives Profil | `KFS.active_profile` | 24930 | s16 / Holding (FC03/06/16) | `kfs_profile_t` → 0=Winter, 1=Sommer | rw | rw |  |
| Puffersolltemperatur Sommer | `KFS.puffer_solltemperatur_sommer` | 24931 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | rw | rw |  |

## Wärmemengenzähler (WMZ)

*6 eindeutige Registertypen.*

| Name | Parameter | Adresse(n) | Typ | Optionen / Wertebereich | User | Expert | Erklärung |
|---|---|---|---|---|:---:|:---:|---|
| Leistung | `MBUS.leistung` | 9517…9587 (×36, Δ2) | s32, 2 Reg. / Input (FC04) | Einheit: `1/1000kW` | r | r |  |
| Vorlauf | `MBUS.vorlauftemp` | 9589…9624 (×36) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Rücklauf | `MBUS.ruecklauftemp` | 9625…9660 (×36) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Energie | `MBUS.energie` | 9661…9731 (×36, Δ2) | u32, 2 Reg. / Input (FC04) | Einheit: `kWh` | r | r |  |
| Volumen akt. | `MBUS.vol_akt` | 9733…9803 (×36, Δ2) | s32, 2 Reg. / Input (FC04) | Einheit: `l/h` | r | r |  |
| Volumen ges. | `MBUS.vol_ges` | 9805…9875 (×36, Δ2) | s32, 2 Reg. / Input (FC04) | Einheit: `1/1000m³` | r | r |  |

## Übergabestation (ÜGS)

*12 eindeutige Registertypen.*

| Name | Parameter | Adresse(n) | Typ | Optionen / Wertebereich | User | Expert | Erklärung |
|---|---|---|---|---|:---:|:---:|---|
| Status | `UEBERGABE.uegs_status` | 10463…10476 (×14) | s16 / Input (FC04) | `uebergabestation_status_t` → 0=Aus, 1=Vorlauf, 2=Betrieb, 3=Rücklauftemp. Begrenzung, 4=Nachlauf, 5=Notlauf | r | r |  |
| Vorlauftemperatur Sekundär (value) | `UEBERGABE.vorlauftemp_sekundaer_ist.value` | 10479…10505 (×14, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Vorlauftemperatur Sekundär (status) | `UEBERGABE.vorlauftemp_sekundaer_ist.status` | 10480…10506 (×14, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Vorlauftemperatur Soll | `UEBERGABE.vorlauftemp_sekundaer_soll` | 10508…10521 (×14) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Vorlauftemperatur Primär (value) | `UEBERGABE.vorlauftemp_primaer_ist.value` | 10524…10550 (×14, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Vorlauftemperatur Primär (status) | `UEBERGABE.vorlauftemp_primaer_ist.status` | 10525…10551 (×14, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Rücklauftemperatur Primär (value) | `UEBERGABE.ruecklauftemp_primaer_ist.value` | 10554…10580 (×14, Δ2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Rücklauftemperatur Primär (status) | `UEBERGABE.ruecklauftemp_primaer_ist.status` | 10555…10581 (×14, Δ2) | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Ventil | `UEBERGABE.o_ventil` | 10583…10596 (×14) | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Temperaturerhöhung | `UEBERGABE.temperatur_anhebung` | 25306…25319 (×14) | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Rücklauftemp. Begrenzung | `UEBERGABE.ruecklauftemp_begrenzung` | 25321…25334 (×14) | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | rw |  |
| Grenztemperatur | `UEBERGABE.grenz_temp` | 25336…25349 (×14) | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |

## Geräte-spezifische Register

Diese Register sind nur für den jeweils ausgewählten Kesseltyp aktiv.

## KWB Easyfire

*59 eindeutige Registertypen.*

| Name | Parameter | Adresse(n) | Typ | Optionen / Wertebereich | User | Expert | Erklärung |
|---|---|---|---|---|:---:|:---:|---|
| Kesseltemperatur Ist (value) | `KSM.i_kesseltemp_ist.value` | 8197 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Kesseltemperatur Ist (status) | `KSM.i_kesseltemp_ist.status` | 8198 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Kesseltemperatur Soll | `KSM.kesseltemp_soll` | 8199 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Kesselpumpe | `KSM.DO_Kesselpumpe` | 8200 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Kesselpumpe % | `KSM.kesselpumpe_steuerstufe` | 8201 | u16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Rücklauftemperatur Ist (value) | `KSM.i_ruecklauftemp_ist.value` | 8202 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Rücklauftemperatur Ist (status) | `KSM.i_ruecklauftemp_ist.status` | 8203 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Kesselleistung | `KSM.brennerleistung` | 8207 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Kesselstatus | `KSM.kesselstatus_anzeige` | 8208…9970 (×2, Δ1762) | s16 / Input (FC04) | `ksm_kesselstatus_anzeige_t` → 0=Aus, 1=Messbetrieb, 2=Betrieb (Reinigung), 3=Einmessen, 4=Betrieb, … (+46) | r | r |  |
| Volllaststunden | `KSM.Betriebsminuten_Summe` | 8209 | u32, 2 Reg. / Input (FC04) | Einheit: `min` | r | r |  |
| Sauerstoff Ist | `KSM.O2Ist` | 8214 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Flammtemperatur Ist (value) | `KSM.i_flammtemp_ist.value` | 8215 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Flammtemperatur Ist (status) | `KSM.i_flammtemp_ist.status` | 8216 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Unterdruck Ist | `KSM.AI_Feuerraum_Unterdruck` | 8218 | s16 / Input (FC04) | Einheit: `1/10Pa` | r | r |  |
| Primärgebläse | `AK.pl_geblaesestufe` | 8221 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Saugzugstufe | `KSM.Saugzugstufe` | 8223 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Nächste Wartung in | `KSM.ServiceintervallReststunden` | 8224 | s16 / Input (FC04) | Einheit: `h` | r | r |  |
| Antrieb Fördersystem | `FS.o_motor_foerdersystem_1` | 8226 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Extern 1 | `KSM.i_extern1` | 8227 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Extern 2 | `KSM.i_extern2` | 8228 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Extern 3 | `KSM.i_extern3` | 8229 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Abgastemperatur (value) | `KSM.i_rauchgastemp_ist.value` | 8231 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Abgastemperatur (status) | `KSM.i_rauchgastemp_ist.status` | 8232 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Brennstoffverbrauch | `FS.pelletsverbrauch` | 8233 | u32, 2 Reg. / Input (FC04) | Einheit: `kg` | r | r |  |
| Brennstofffaktor | `EF2.Brennstofffaktor` | 8235 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Brennerleistung extern | `AK.externe_brennerleistung` | 8236 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Kesseltemp. Soll Extern | `AK.externe_kessel_solltemperatur` | 8237 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Saugturbine | `KSM.DO_Pelletssauger` | 8238 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Außentemperatur Istwert (value) | `SYSTEM.i_aussen_temperatur.value` | 8250 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Außentemperatur Istwert (status) | `SYSTEM.i_aussen_temperatur.status` | 8251 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Multifunktionsausgang 1 (125) | `KSM.o_multifunktionsausgang_1` | 9044 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 2 (127) | `KSM.o_multifunktionsausgang_2` | 9045 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 3 (124) | `KSM.o_multifunktionsausgang_3` | 9046 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 4 (126) | `KSM.o_multifunktionsausgang_4` | 9047 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Modbus Überhitzung | `KSM.modbus_ueberhitzung` | 9495 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r | → Glossar |
| Modbus Wärmeabnahme Max | `KSM.modbus_waermeabnahme_max` | 9496 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Füllstand Aschebehälter | `KSM.aschefuellstand` | 9497 | u16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Drehzahl Saugzug | `KSM.i_drehzahl_saugzug` | 9498 | u16 / Input (FC04) | Einheit: `Upm` | r | r |  |
| Brennerleistung bestimmt durch | `AK.anforderung_bl_ursache` | 9877 | s16 / Input (FC04) | `ak_anf_bl_ursache_t` → 1=Normalbetrieb, 2=Einmessen, 3=Kaminkehrer, 4=Extern, 5=Extern überhitzt, … (+8) | r | r |  |
| Wärmemenge gesamt | `KSM.waermemenge_gesamt_kwh` | 9878 | u32, 2 Reg. / Input (FC04) | Einheit: `1/10kWh` | r | r |  |
| Brennstoffverbrauch Rücksetzzähler | `FS.pelletverbrauch_reset_counter` | 9988 | u16 / Input (FC04) | — | r | r |  |
| Clee Status | `SYSTEM.comfortenergy_status` | 9989 | s16 / Input (FC04) | `comfortenergy_status_t` → 0=deaktiviert, 1=offline, 2=online | r | r | → Glossar |
| Kessel Ein/Aus | `AK.anlage_ein` | 24576 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | rw | rw |  |
| Solltemperatur 1 | `EF2.KesseltempSoll1` | 24577 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Solltemperatur 2 | `EF2.KesseltempSoll2` | 24578 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Rücklauftemperatur Minimum | `KSM.RuecklauftempMin` | 24581 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Externe Vorgabe | `AK.externe_vorgabe` | 24583 | s16 / Holding (FC03/06/16) | `ak_externe_vorgabe_t` → 0=Aus, 1=Temperatur, 2=Leistung, 3=Modbus, 4=Modbus | r | rw | → Glossar |
| Kesselprogramm | `AK.kesselprogramm` | 24584 | s16 / Holding (FC03/06/16) | `ak_kesselprogramm_t` → 0=Anforderung, 1=Zeitprogramm, 2=Dauerbetrieb, 3=Modbus Temperatur, 4=Modbus Leistung+Temperatur, … (+0) | r | rw |  |
| Modbus Lifetick | `KSM.modbus_lifetick` | 24849 | u16 / Holding (FC03/06/16) | — | r | rw | → Glossar |
| Modbus Commit Lifetick | `KSM.modbus_commit_lifetick` | 24850 | u16 / Holding (FC03/06/16) | — | r | r | → Glossar |
| Modbus Kesseltemperatur | `KSM.modbus_kesseltemp_vorgabe` | 24851 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Kesselleistung | `KSM.modbus_leistung_vorgabe` | 24852 | s16 / Holding (FC03/06/16) | Einheit: `1/10%` | r | rw |  |
| Modbus Kesselanforderung | `KSM.modbus_kesselanforderung` | 24854 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | rw | → Glossar |
| Restmenge Brennstofflager | `KSM.restmenge_brennstofflager` | 24927 | u32, 2 Reg. / Holding (FC03/06/16) | Einheit: `kg` | rw | rw |  |
| Modbus Puffertemperatur oben für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_oben.value` | 24932 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Puffertemperatur oben für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_oben.status` | 24933 | s16 / Holding (FC03/06/16) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | rw |  |
| Modbus Puffertemperatur unten für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_unten.value` | 24934 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Puffertemperatur unten für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_unten.status` | 24935 | s16 / Holding (FC03/06/16) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | rw |  |
| Modbus Überstromnutzung | `SYSTEM.modbus_clee_ueberschusstrom` | 25040 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | rw | → Glossar |

## KWB EF3

*57 eindeutige Registertypen.*

| Name | Parameter | Adresse(n) | Typ | Optionen / Wertebereich | User | Expert | Erklärung |
|---|---|---|---|---|:---:|:---:|---|
| Kesseltemperatur Ist (value) | `KSM.i_kesseltemp_ist.value` | 8197 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Kesseltemperatur Ist (status) | `KSM.i_kesseltemp_ist.status` | 8198 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Kesseltemperatur Soll | `KSM.kesseltemp_soll` | 8199 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Kesselpumpe | `KSM.DO_Kesselpumpe` | 8200 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Kesselpumpe % | `KSM.kesselpumpe_steuerstufe` | 8201 | u16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Rücklauftemperatur Ist (value) | `KSM.i_ruecklauftemp_ist.value` | 8202 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Rücklauftemperatur Ist (status) | `KSM.i_ruecklauftemp_ist.status` | 8203 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Kesselleistung | `KSM.brennerleistung` | 8207 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Kesselstatus | `KSM.kesselstatus_anzeige` | 8208…9970 (×2, Δ1762) | s16 / Input (FC04) | `ksm_kesselstatus_anzeige_t` → 0=Aus, 1=Messbetrieb, 2=Betrieb (Reinigung), 3=Einmessen, 4=Betrieb, … (+46) | r | r |  |
| Volllaststunden | `KSM.Betriebsminuten_Summe` | 8209 | u32, 2 Reg. / Input (FC04) | Einheit: `min` | r | r |  |
| Sauerstoff Ist | `KSM.O2Ist` | 8214 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Flammtemperatur Ist (value) | `KSM.i_flammtemp_ist.value` | 8215 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Flammtemperatur Ist (status) | `KSM.i_flammtemp_ist.status` | 8216 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Saugzugstufe | `KSM.Saugzugstufe` | 8223 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Nächste Wartung in | `KSM.ServiceintervallReststunden` | 8224 | s16 / Input (FC04) | Einheit: `h` | r | r |  |
| Antrieb Fördersystem | `FS.o_motor_foerdersystem_1` | 8226 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Extern 1 | `KSM.i_extern1` | 8227 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Extern 2 | `KSM.i_extern2` | 8228 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Extern 3 | `KSM.i_extern3` | 8229 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Abgastemperatur (value) | `KSM.i_rauchgastemp_ist.value` | 8231 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Abgastemperatur (status) | `KSM.i_rauchgastemp_ist.status` | 8232 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Brennstoffverbrauch | `FS.pelletsverbrauch` | 8233 | u32, 2 Reg. / Input (FC04) | Einheit: `kg` | r | r |  |
| Brennstofffaktor | `EF2.Brennstofffaktor` | 8235 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Brennerleistung extern | `AK.externe_brennerleistung` | 8236 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Kesseltemp. Soll Extern | `AK.externe_kessel_solltemperatur` | 8237 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Saugturbine | `KSM.DO_Pelletssauger` | 8238 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Außentemperatur Istwert (value) | `SYSTEM.i_aussen_temperatur.value` | 8250 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Außentemperatur Istwert (status) | `SYSTEM.i_aussen_temperatur.status` | 8251 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Multifunktionsausgang 1 (125) | `KSM.o_multifunktionsausgang_1` | 9044 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 2 (127) | `KSM.o_multifunktionsausgang_2` | 9045 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 3 (124) | `KSM.o_multifunktionsausgang_3` | 9046 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 4 (126) | `KSM.o_multifunktionsausgang_4` | 9047 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Modbus Überhitzung | `KSM.modbus_ueberhitzung` | 9495 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r | → Glossar |
| Modbus Wärmeabnahme Max | `KSM.modbus_waermeabnahme_max` | 9496 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Füllstand Aschebehälter | `KSM.aschefuellstand` | 9497 | u16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Drehzahl Saugzug | `KSM.i_drehzahl_saugzug` | 9498 | u16 / Input (FC04) | Einheit: `Upm` | r | r |  |
| Brennerleistung bestimmt durch | `AK.anforderung_bl_ursache` | 9877 | s16 / Input (FC04) | `ak_anf_bl_ursache_t` → 1=Normalbetrieb, 2=Einmessen, 3=Kaminkehrer, 4=Extern, 5=Extern überhitzt, … (+8) | r | r |  |
| Wärmemenge gesamt | `KSM.waermemenge_gesamt_kwh` | 9878 | u32, 2 Reg. / Input (FC04) | Einheit: `1/10kWh` | r | r |  |
| Brennstoffverbrauch Rücksetzzähler | `FS.pelletverbrauch_reset_counter` | 9988 | u16 / Input (FC04) | — | r | r |  |
| Clee Status | `SYSTEM.comfortenergy_status` | 9989 | s16 / Input (FC04) | `comfortenergy_status_t` → 0=deaktiviert, 1=offline, 2=online | r | r | → Glossar |
| Differenzdruck Ist | `EF2.ef3_differenzdruck_ist` | 10023 | s16 / Input (FC04) | Einheit: `1/10Pa` | r | r |  |
| Kessel Ein/Aus | `AK.anlage_ein` | 24576 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | rw | rw |  |
| Solltemperatur 1 | `EF2.KesseltempSoll1` | 24577 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Solltemperatur 2 | `EF2.KesseltempSoll2` | 24578 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Externe Vorgabe | `AK.externe_vorgabe` | 24583 | s16 / Holding (FC03/06/16) | `ak_externe_vorgabe_t` → 0=Aus, 1=Temperatur, 2=Leistung, 3=Modbus, 4=Modbus | r | rw | → Glossar |
| Kesselprogramm | `AK.kesselprogramm` | 24584 | s16 / Holding (FC03/06/16) | `ak_kesselprogramm_t` → 0=Anforderung, 1=Zeitprogramm, 2=Dauerbetrieb, 3=Modbus Temperatur, 4=Modbus Leistung+Temperatur, … (+0) | r | rw |  |
| Modbus Lifetick | `KSM.modbus_lifetick` | 24849 | u16 / Holding (FC03/06/16) | — | r | rw | → Glossar |
| Modbus Commit Lifetick | `KSM.modbus_commit_lifetick` | 24850 | u16 / Holding (FC03/06/16) | — | r | r | → Glossar |
| Modbus Kesseltemperatur | `KSM.modbus_kesseltemp_vorgabe` | 24851 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Kesselleistung | `KSM.modbus_leistung_vorgabe` | 24852 | s16 / Holding (FC03/06/16) | Einheit: `1/10%` | r | rw |  |
| Modbus Kesselanforderung | `KSM.modbus_kesselanforderung` | 24854 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | rw | → Glossar |
| Restmenge Brennstofflager | `KSM.restmenge_brennstofflager` | 24927 | u32, 2 Reg. / Holding (FC03/06/16) | Einheit: `kg` | rw | rw |  |
| Modbus Puffertemperatur oben für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_oben.value` | 24932 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Puffertemperatur oben für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_oben.status` | 24933 | s16 / Holding (FC03/06/16) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | rw |  |
| Modbus Puffertemperatur unten für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_unten.value` | 24934 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Puffertemperatur unten für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_unten.status` | 24935 | s16 / Holding (FC03/06/16) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | rw |  |
| Modbus Überstromnutzung | `SYSTEM.modbus_clee_ueberschusstrom` | 25040 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | rw | → Glossar |

## KWB Multifire

*60 eindeutige Registertypen.*

| Name | Parameter | Adresse(n) | Typ | Optionen / Wertebereich | User | Expert | Erklärung |
|---|---|---|---|---|:---:|:---:|---|
| Kesseltemperatur Ist (value) | `KSM.i_kesseltemp_ist.value` | 8197 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Kesseltemperatur Ist (status) | `KSM.i_kesseltemp_ist.status` | 8198 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Kesseltemperatur Soll | `KSM.kesseltemp_soll` | 8199 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Kesselpumpe | `KSM.DO_Kesselpumpe` | 8200 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Kesselpumpe % | `KSM.kesselpumpe_steuerstufe` | 8201 | u16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Rücklauftemperatur Ist (value) | `KSM.i_ruecklauftemp_ist.value` | 8202 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Rücklauftemperatur Ist (status) | `KSM.i_ruecklauftemp_ist.status` | 8203 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Verbraucher Anforderung | `KSM.verbraucher_anforderung` | 8206 | s16 / Input (FC04) | `ksm_verbraucher_anforderung_t` → 0=Aus, 1=Heizkreis, 2=BWS, 3=Puffer | r | r |  |
| Kesselleistung | `KSM.brennerleistung` | 8207 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Kesselstatus | `KSM.kesselstatus_anzeige` | 8208…9970 (×2, Δ1762) | s16 / Input (FC04) | `ksm_kesselstatus_anzeige_t` → 0=Aus, 1=Messbetrieb, 2=Betrieb (Reinigung), 3=Einmessen, 4=Betrieb, … (+46) | r | r |  |
| Volllaststunden | `KSM.Betriebsminuten_Summe` | 8209 | u32, 2 Reg. / Input (FC04) | Einheit: `min` | r | r |  |
| Glutbett | `MF2.Glutbettniveau` | 8213 | s16 / Input (FC04) | — | r | r | → Glossar |
| Sauerstoff Ist | `KSM.O2Ist` | 8214 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Flammtemperatur Ist (value) | `KSM.i_flammtemp_ist.value` | 8215 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Flammtemperatur Ist (status) | `KSM.i_flammtemp_ist.status` | 8216 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Ultraschallsensor ist | `MF2.AI_Fuellstand_Zwischenbehaelter` | 8217 | s16 / Input (FC04) | Einheit: `mm` | r | r |  |
| Unterdruck Ist | `KSM.AI_Feuerraum_Unterdruck` | 8218 | s16 / Input (FC04) | Einheit: `1/10Pa` | r | r |  |
| Ausbrandtemperatur (value) | `MF2.i_ausbrandtemp.value` | 8219 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Ausbrandtemperatur (status) | `MF2.i_ausbrandtemp.status` | 8220 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Primärgebläse | `AK.pl_geblaesestufe` | 8221 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Sekundärgebläse | `MF2.sl_geblaesestufe` | 8222 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Saugzugstufe | `KSM.Saugzugstufe` | 8223 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Nächste Wartung in | `KSM.ServiceintervallReststunden` | 8224 | s16 / Input (FC04) | Einheit: `h` | r | r |  |
| Antrieb Fördersystem | `FS.o_motor_foerdersystem_1` | 8226 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Extern 1 | `KSM.i_extern1` | 8227 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Extern 2 | `KSM.i_extern2` | 8228 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Extern 3 | `KSM.i_extern3` | 8229 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Brennstofffaktor | `MF2.Brennstofffaktor` | 8230 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Brennerleistung extern | `AK.externe_brennerleistung` | 8236 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Kesseltemp. Soll Extern | `AK.externe_kessel_solltemperatur` | 8237 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Asche 90% voll | `MF2.i_aschebehaelter_90_prz` | 8239 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Luftverschiebung | `MF2.luftverschiebung_gesamt` | 8240 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Zwischenbehälter Füllstand | `MF2.zwischenbehaelter_fuellstand_prz` | 8241 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Außentemperatur Istwert (value) | `SYSTEM.i_aussen_temperatur.value` | 8250 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Außentemperatur Istwert (status) | `SYSTEM.i_aussen_temperatur.status` | 8251 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Multifunktionsausgang 1 (125) | `KSM.o_multifunktionsausgang_1` | 9044 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 2 (127) | `KSM.o_multifunktionsausgang_2` | 9045 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 3 (124) | `KSM.o_multifunktionsausgang_3` | 9046 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 4 (126) | `KSM.o_multifunktionsausgang_4` | 9047 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Modbus Überhitzung | `KSM.modbus_ueberhitzung` | 9495 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r | → Glossar |
| Modbus Wärmeabnahme Max | `KSM.modbus_waermeabnahme_max` | 9496 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Drehzahl Saugzug | `KSM.i_drehzahl_saugzug` | 9498 | u16 / Input (FC04) | Einheit: `Upm` | r | r |  |
| Brennerleistung bestimmt durch | `AK.anforderung_bl_ursache` | 9877 | s16 / Input (FC04) | `ak_anf_bl_ursache_t` → 1=Normalbetrieb, 2=Einmessen, 3=Kaminkehrer, 4=Extern, 5=Extern überhitzt, … (+8) | r | r |  |
| Wärmemenge gesamt | `KSM.waermemenge_gesamt_kwh` | 9878 | u32, 2 Reg. / Input (FC04) | Einheit: `1/10kWh` | r | r |  |
| Kessel Ein/Aus | `AK.anlage_ein` | 24576 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | rw | rw |  |
| Solltemperatur 1 | `MF2.KesseltempSoll1` | 24579 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Solltemperatur 2 | `MF2.KesseltempSoll2` | 24580 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Rücklauftemperatur Minimum | `KSM.RuecklauftempMin` | 24581 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Externe Vorgabe | `AK.externe_vorgabe` | 24583 | s16 / Holding (FC03/06/16) | `ak_externe_vorgabe_t` → 0=Aus, 1=Temperatur, 2=Leistung, 3=Modbus, 4=Modbus | r | rw | → Glossar |
| Kesselprogramm | `AK.kesselprogramm` | 24584 | s16 / Holding (FC03/06/16) | `ak_kesselprogramm_t` → 0=Anforderung, 1=Zeitprogramm, 2=Dauerbetrieb, 3=Modbus Temperatur, 4=Modbus Leistung+Temperatur, … (+0) | r | rw |  |
| Modbus Lifetick | `KSM.modbus_lifetick` | 24849 | u16 / Holding (FC03/06/16) | — | r | rw | → Glossar |
| Modbus Commit Lifetick | `KSM.modbus_commit_lifetick` | 24850 | u16 / Holding (FC03/06/16) | — | r | r | → Glossar |
| Modbus Kesseltemperatur | `KSM.modbus_kesseltemp_vorgabe` | 24851 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Kesselleistung | `KSM.modbus_leistung_vorgabe` | 24852 | s16 / Holding (FC03/06/16) | Einheit: `1/10%` | r | rw |  |
| Modbus Kesselanforderung | `KSM.modbus_kesselanforderung` | 24854 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | rw | → Glossar |
| Modbus Puffertemperatur oben für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_oben.value` | 24932 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Puffertemperatur oben für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_oben.status` | 24933 | s16 / Holding (FC03/06/16) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | rw |  |
| Modbus Puffertemperatur unten für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_unten.value` | 24934 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Puffertemperatur unten für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_unten.status` | 24935 | s16 / Holding (FC03/06/16) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | rw |  |
| Modbus Überstromnutzung | `SYSTEM.modbus_clee_ueberschusstrom` | 25040 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | rw | → Glossar |

## KWB Pelletfire+

*62 eindeutige Registertypen.*

| Name | Parameter | Adresse(n) | Typ | Optionen / Wertebereich | User | Expert | Erklärung |
|---|---|---|---|---|:---:|:---:|---|
| Kesseltemperatur Ist (value) | `KSM.i_kesseltemp_ist.value` | 8197 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Kesseltemperatur Ist (status) | `KSM.i_kesseltemp_ist.status` | 8198 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Kesseltemperatur Soll | `KSM.kesseltemp_soll` | 8199 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Kesselpumpe | `KSM.DO_Kesselpumpe` | 8200 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Kesselpumpe % | `KSM.kesselpumpe_steuerstufe` | 8201 | u16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Rücklauftemperatur Ist (value) | `KSM.i_ruecklauftemp_ist.value` | 8202 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Rücklauftemperatur Ist (status) | `KSM.i_ruecklauftemp_ist.status` | 8203 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Verbraucher Anforderung | `KSM.verbraucher_anforderung` | 8206 | s16 / Input (FC04) | `ksm_verbraucher_anforderung_t` → 0=Aus, 1=Heizkreis, 2=BWS, 3=Puffer | r | r |  |
| Kesselleistung | `KSM.brennerleistung` | 8207 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Kesselstatus | `KSM.kesselstatus_anzeige` | 8208…9970 (×2, Δ1762) | s16 / Input (FC04) | `ksm_kesselstatus_anzeige_t` → 0=Aus, 1=Messbetrieb, 2=Betrieb (Reinigung), 3=Einmessen, 4=Betrieb, … (+46) | r | r |  |
| Volllaststunden | `KSM.Betriebsminuten_Summe` | 8209 | u32, 2 Reg. / Input (FC04) | Einheit: `min` | r | r |  |
| Glutbett | `MF2.Glutbettniveau` | 8213 | s16 / Input (FC04) | — | r | r | → Glossar |
| Sauerstoff Ist | `KSM.O2Ist` | 8214 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Flammtemperatur Ist (value) | `KSM.i_flammtemp_ist.value` | 8215 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Flammtemperatur Ist (status) | `KSM.i_flammtemp_ist.status` | 8216 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Unterdruck Ist | `KSM.AI_Feuerraum_Unterdruck` | 8218 | s16 / Input (FC04) | Einheit: `1/10Pa` | r | r |  |
| Ausbrandtemperatur (value) | `MF2.i_ausbrandtemp.value` | 8219 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Ausbrandtemperatur (status) | `MF2.i_ausbrandtemp.status` | 8220 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Primärgebläse | `AK.pl_geblaesestufe` | 8221 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Sekundärgebläse | `MF2.sl_geblaesestufe` | 8222 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Saugzugstufe | `KSM.Saugzugstufe` | 8223 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Nächste Wartung in | `KSM.ServiceintervallReststunden` | 8224 | s16 / Input (FC04) | Einheit: `h` | r | r |  |
| Antrieb Fördersystem | `FS.o_motor_foerdersystem_1` | 8226 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Extern 1 | `KSM.i_extern1` | 8227 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Extern 2 | `KSM.i_extern2` | 8228 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Extern 3 | `KSM.i_extern3` | 8229 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Brennstofffaktor | `MF2.Brennstofffaktor` | 8230 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Brennstoffverbrauch | `FS.pelletsverbrauch` | 8233 | u32, 2 Reg. / Input (FC04) | Einheit: `kg` | r | r |  |
| Brennerleistung extern | `AK.externe_brennerleistung` | 8236 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Kesseltemp. Soll Extern | `AK.externe_kessel_solltemperatur` | 8237 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Saugturbine | `KSM.DO_Pelletssauger` | 8238 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Asche 90% voll | `MF2.i_aschebehaelter_90_prz` | 8239 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Luftverschiebung | `MF2.luftverschiebung_gesamt` | 8240 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Außentemperatur Istwert (value) | `SYSTEM.i_aussen_temperatur.value` | 8250 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Außentemperatur Istwert (status) | `SYSTEM.i_aussen_temperatur.status` | 8251 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Multifunktionsausgang 1 (125) | `KSM.o_multifunktionsausgang_1` | 9044 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 2 (127) | `KSM.o_multifunktionsausgang_2` | 9045 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 3 (124) | `KSM.o_multifunktionsausgang_3` | 9046 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 4 (126) | `KSM.o_multifunktionsausgang_4` | 9047 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Modbus Überhitzung | `KSM.modbus_ueberhitzung` | 9495 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r | → Glossar |
| Modbus Wärmeabnahme Max | `KSM.modbus_waermeabnahme_max` | 9496 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Drehzahl Saugzug | `KSM.i_drehzahl_saugzug` | 9498 | u16 / Input (FC04) | Einheit: `Upm` | r | r |  |
| Brennerleistung bestimmt durch | `AK.anforderung_bl_ursache` | 9877 | s16 / Input (FC04) | `ak_anf_bl_ursache_t` → 1=Normalbetrieb, 2=Einmessen, 3=Kaminkehrer, 4=Extern, 5=Extern überhitzt, … (+8) | r | r |  |
| Wärmemenge gesamt | `KSM.waermemenge_gesamt_kwh` | 9878 | u32, 2 Reg. / Input (FC04) | Einheit: `1/10kWh` | r | r |  |
| Brennstoffverbrauch Rücksetzzähler | `FS.pelletverbrauch_reset_counter` | 9988 | u16 / Input (FC04) | — | r | r |  |
| Kessel Ein/Aus | `AK.anlage_ein` | 24576 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | rw | rw |  |
| Solltemperatur 1 | `MF2.KesseltempSoll1` | 24579 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Solltemperatur 2 | `MF2.KesseltempSoll2` | 24580 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Rücklauftemperatur Minimum | `KSM.RuecklauftempMin` | 24581 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Externe Vorgabe | `AK.externe_vorgabe` | 24583 | s16 / Holding (FC03/06/16) | `ak_externe_vorgabe_t` → 0=Aus, 1=Temperatur, 2=Leistung, 3=Modbus, 4=Modbus | r | rw | → Glossar |
| Kesselprogramm | `AK.kesselprogramm` | 24584 | s16 / Holding (FC03/06/16) | `ak_kesselprogramm_t` → 0=Anforderung, 1=Zeitprogramm, 2=Dauerbetrieb, 3=Modbus Temperatur, 4=Modbus Leistung+Temperatur, … (+0) | r | rw |  |
| Modbus Lifetick | `KSM.modbus_lifetick` | 24849 | u16 / Holding (FC03/06/16) | — | r | rw | → Glossar |
| Modbus Commit Lifetick | `KSM.modbus_commit_lifetick` | 24850 | u16 / Holding (FC03/06/16) | — | r | r | → Glossar |
| Modbus Kesseltemperatur | `KSM.modbus_kesseltemp_vorgabe` | 24851 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Kesselleistung | `KSM.modbus_leistung_vorgabe` | 24852 | s16 / Holding (FC03/06/16) | Einheit: `1/10%` | r | rw |  |
| Modbus Kesselanforderung | `KSM.modbus_kesselanforderung` | 24854 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | rw | → Glossar |
| Restmenge Brennstofflager | `KSM.restmenge_brennstofflager` | 24927 | u32, 2 Reg. / Holding (FC03/06/16) | Einheit: `kg` | rw | rw |  |
| Modbus Puffertemperatur oben für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_oben.value` | 24932 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Puffertemperatur oben für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_oben.status` | 24933 | s16 / Holding (FC03/06/16) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | rw |  |
| Modbus Puffertemperatur unten für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_unten.value` | 24934 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Puffertemperatur unten für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_unten.status` | 24935 | s16 / Holding (FC03/06/16) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | rw |  |
| Modbus Überstromnutzung | `SYSTEM.modbus_clee_ueberschusstrom` | 25040 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | rw | → Glossar |

## KWB Combifire

*65 eindeutige Registertypen.*

| Name | Parameter | Adresse(n) | Typ | Optionen / Wertebereich | User | Expert | Erklärung |
|---|---|---|---|---|:---:|:---:|---|
| Kesseltemperatur Ist (value) | `KSM.i_kesseltemp_ist.value` | 8197 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Kesseltemperatur Ist (status) | `KSM.i_kesseltemp_ist.status` | 8198 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Kesseltemperatur Soll | `KSM.kesseltemp_soll` | 8199…24585 (×2, Δ16386) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Kesselpumpe | `KSM.DO_Kesselpumpe` | 8200 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Kesselpumpe % | `KSM.kesselpumpe_steuerstufe` | 8201 | u16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Rücklauftemperatur Ist (value) | `KSM.i_ruecklauftemp_ist.value` | 8202 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Rücklauftemperatur Ist (status) | `KSM.i_ruecklauftemp_ist.status` | 8203 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Verbraucher Anforderung | `KSM.verbraucher_anforderung` | 8206 | s16 / Input (FC04) | `ksm_verbraucher_anforderung_t` → 0=Aus, 1=Heizkreis, 2=BWS, 3=Puffer | r | r |  |
| Kesselleistung | `KSM.brennerleistung` | 8207 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Kesselstatus | `KSM.kesselstatus_anzeige` | 8208 | s16 / Input (FC04) | `ksm_kesselstatus_anzeige_t` → 0=Aus, 1=Messbetrieb, 2=Betrieb (Reinigung), 3=Einmessen, 4=Betrieb, … (+46) | r | r |  |
| Volllaststunden | `KSM.Betriebsminuten_Summe` | 8209…8248 (×2, Δ39) | u32, 2 Reg. / Input (FC04) | Einheit: `min` | r | r |  |
| Status Pelletmodul | `AK.kesselstatus_anzeige_ak` | 8211 | s16 / Input (FC04) | `ksm_kesselstatus_anzeige_t` → 0=Aus, 1=Messbetrieb, 2=Betrieb (Reinigung), 3=Einmessen, 4=Betrieb, … (+46) | r | r |  |
| Status Stückholz | `CF2.kesselstatus_anzeige_sh` | 8212 | s16 / Input (FC04) | `ksm_kesselstatus_anzeige_t` → 0=Aus, 1=Messbetrieb, 2=Betrieb (Reinigung), 3=Einmessen, 4=Betrieb, … (+46) | r | r |  |
| Sauerstoff Ist | `KSM.O2Ist` | 8214 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Flammtemperatur Ist (value) | `KSM.i_flammtemp_ist.value` | 8215 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Flammtemperatur Ist (status) | `KSM.i_flammtemp_ist.status` | 8216 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Unterdruck Ist | `KSM.AI_Feuerraum_Unterdruck` | 8218 | s16 / Input (FC04) | Einheit: `1/10Pa` | r | r |  |
| Primärgebläse | `AK.pl_geblaesestufe` | 8221 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Saugzugstufe | `KSM.Saugzugstufe` | 8223 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Nächste Wartung in | `KSM.ServiceintervallReststunden` | 8224 | s16 / Input (FC04) | Einheit: `h` | r | r |  |
| Antrieb Fördersystem | `FS.o_motor_foerdersystem_1` | 8226 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Extern 1 | `KSM.i_extern1` | 8227 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Extern 2 | `KSM.i_extern2` | 8228 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Extern 3 | `KSM.i_extern3` | 8229 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Brennstoffverbrauch | `FS.pelletsverbrauch` | 8233 | u32, 2 Reg. / Input (FC04) | Einheit: `kg` | r | r |  |
| Brennstofffaktor | `EF2.Brennstofffaktor` | 8235 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Brennerleistung extern | `AK.externe_brennerleistung` | 8236 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Kesseltemp. Soll Extern | `AK.externe_kessel_solltemperatur` | 8237 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Saugturbine | `KSM.DO_Pelletssauger` | 8238 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Primärluftklappe | `CF2.i_pl_klappe_ist_promille` | 8242 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Sekundärluftklappe | `CF2.i_sl_klappe_ist_promille` | 8243 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Betriebsmodus | `CF2.betriebsmodus` | 8244 | s16 / Input (FC04) | `cf2_betriebsmodus_t` → 0=Kein, 1=Stückholz, 2=Pellets, 3=Stückholz (PM Nachlauf), 4=Relaistest | r | r |  |
| Füllraumtüre | `CF2.i_tuer_geschlossen` | 8245 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Maximaler Befüllgrad | `CF2.max_befuellgrad_anzeige` | 8246 | s16 / Input (FC04) | `cf2_max_befuellgrad_anzeige_t` → 0=Keine, 1=Ein Drittel, 2=Zwei Drittel, 3=Voll | r | r |  |
| Zündung Heizung | `CF2.o_zuendung_heizung_sh` | 8247 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 1 (125) | `KSM.o_multifunktionsausgang_1` | 9044 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 2 (127) | `KSM.o_multifunktionsausgang_2` | 9045 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 3 (124) | `KSM.o_multifunktionsausgang_3` | 9046 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 4 (126) | `KSM.o_multifunktionsausgang_4` | 9047 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Modbus Überhitzung | `KSM.modbus_ueberhitzung` | 9495 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r | → Glossar |
| Modbus Wärmeabnahme Max | `KSM.modbus_waermeabnahme_max` | 9496 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Füllstand Aschebehälter | `KSM.aschefuellstand` | 9497 | u16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Drehzahl Saugzug | `KSM.i_drehzahl_saugzug` | 9498 | u16 / Input (FC04) | Einheit: `Upm` | r | r |  |
| Brennerleistung bestimmt durch | `AK.anforderung_bl_ursache` | 9877 | s16 / Input (FC04) | `ak_anf_bl_ursache_t` → 1=Normalbetrieb, 2=Einmessen, 3=Kaminkehrer, 4=Extern, 5=Extern überhitzt, … (+8) | r | r |  |
| Wärmemenge gesamt | `KSM.waermemenge_gesamt_kwh` | 9878 | u32, 2 Reg. / Input (FC04) | Einheit: `1/10kWh` | r | r |  |
| Pelletkesselstatus | `KSM.kesselstatus_anzeige_simple` | 9970 | s16 / Input (FC04) | `kfk_kesselstatus_t` → 0=Aus, 1=Bereitschaft, 2=Zünden, 3=Betrieb, 4=Nachlauf, … (+3) | r | r |  |
| Brennstoffverbrauch Rücksetzzähler | `FS.pelletverbrauch_reset_counter` | 9988 | u16 / Input (FC04) | — | r | r |  |
| Kessel Ein/Aus | `AK.anlage_ein` | 24576 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | rw | rw |  |
| Solltemperatur 1 | `EF2.KesseltempSoll1` | 24577 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Solltemperatur 2 | `EF2.KesseltempSoll2` | 24578 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Rücklauftemperatur Minimum | `KSM.RuecklauftempMin` | 24581 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Externe Vorgabe | `AK.externe_vorgabe` | 24583 | s16 / Holding (FC03/06/16) | `ak_externe_vorgabe_t` → 0=Aus, 1=Temperatur, 2=Leistung, 3=Modbus, 4=Modbus | r | rw | → Glossar |
| Kesselprogramm | `AK.kesselprogramm` | 24584 | s16 / Holding (FC03/06/16) | `ak_kesselprogramm_t` → 0=Anforderung, 1=Zeitprogramm, 2=Dauerbetrieb, 3=Modbus Temperatur, 4=Modbus Leistung+Temperatur, … (+0) | r | rw |  |
| Automatische Zündung Funktion | `CF2.automatische_Zuendung_SH` | 24586 | s16 / Holding (FC03/06/16) | `cf2_automatische_zuendung_t` → 0=Aus, 1=Auswahl, 2=Anforderung, 3=Sofort | r | rw |  |
| Modbus Lifetick | `KSM.modbus_lifetick` | 24849 | u16 / Holding (FC03/06/16) | — | r | rw | → Glossar |
| Modbus Commit Lifetick | `KSM.modbus_commit_lifetick` | 24850 | u16 / Holding (FC03/06/16) | — | r | r | → Glossar |
| Modbus Kesseltemperatur | `KSM.modbus_kesseltemp_vorgabe` | 24851 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Kesselleistung | `KSM.modbus_leistung_vorgabe` | 24852 | s16 / Holding (FC03/06/16) | Einheit: `1/10%` | r | rw |  |
| Modbus Kesselanforderung | `KSM.modbus_kesselanforderung` | 24854 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | rw | → Glossar |
| Restmenge Brennstofflager | `KSM.restmenge_brennstofflager` | 24927 | u32, 2 Reg. / Holding (FC03/06/16) | Einheit: `kg` | rw | rw |  |
| Modbus Puffertemperatur oben für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_oben.value` | 24932 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Puffertemperatur oben für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_oben.status` | 24933 | s16 / Holding (FC03/06/16) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | rw |  |
| Modbus Puffertemperatur unten für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_unten.value` | 24934 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Puffertemperatur unten für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_unten.status` | 24935 | s16 / Holding (FC03/06/16) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | rw |  |
| Modbus Überstromnutzung | `SYSTEM.modbus_clee_ueberschusstrom` | 25040 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | rw | → Glossar |

## KWB CF 2

*65 eindeutige Registertypen.*

| Name | Parameter | Adresse(n) | Typ | Optionen / Wertebereich | User | Expert | Erklärung |
|---|---|---|---|---|:---:|:---:|---|
| Kesseltemperatur Ist (value) | `KSM.i_kesseltemp_ist.value` | 8197 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Kesseltemperatur Ist (status) | `KSM.i_kesseltemp_ist.status` | 8198 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Kesseltemperatur Soll | `KSM.kesseltemp_soll` | 8199…24585 (×2, Δ16386) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Kesselpumpe | `KSM.DO_Kesselpumpe` | 8200 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Kesselpumpe % | `KSM.kesselpumpe_steuerstufe` | 8201 | u16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Rücklauftemperatur Ist (value) | `KSM.i_ruecklauftemp_ist.value` | 8202 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Rücklauftemperatur Ist (status) | `KSM.i_ruecklauftemp_ist.status` | 8203 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Verbraucher Anforderung | `KSM.verbraucher_anforderung` | 8206 | s16 / Input (FC04) | `ksm_verbraucher_anforderung_t` → 0=Aus, 1=Heizkreis, 2=BWS, 3=Puffer | r | r |  |
| Kesselleistung | `KSM.brennerleistung` | 8207 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Kesselstatus | `KSM.kesselstatus_anzeige` | 8208 | s16 / Input (FC04) | `ksm_kesselstatus_anzeige_t` → 0=Aus, 1=Messbetrieb, 2=Betrieb (Reinigung), 3=Einmessen, 4=Betrieb, … (+46) | r | r |  |
| Volllaststunden | `KSM.Betriebsminuten_Summe` | 8209…8248 (×2, Δ39) | u32, 2 Reg. / Input (FC04) | Einheit: `min` | r | r |  |
| Status Pelletmodul | `AK.kesselstatus_anzeige_ak` | 8211 | s16 / Input (FC04) | `ksm_kesselstatus_anzeige_t` → 0=Aus, 1=Messbetrieb, 2=Betrieb (Reinigung), 3=Einmessen, 4=Betrieb, … (+46) | r | r |  |
| Status Stückholz | `CF2.kesselstatus_anzeige_sh` | 8212 | s16 / Input (FC04) | `ksm_kesselstatus_anzeige_t` → 0=Aus, 1=Messbetrieb, 2=Betrieb (Reinigung), 3=Einmessen, 4=Betrieb, … (+46) | r | r |  |
| Sauerstoff Ist | `KSM.O2Ist` | 8214 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Flammtemperatur Ist (value) | `KSM.i_flammtemp_ist.value` | 8215 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Flammtemperatur Ist (status) | `KSM.i_flammtemp_ist.status` | 8216 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Unterdruck Ist | `KSM.AI_Feuerraum_Unterdruck` | 8218 | s16 / Input (FC04) | Einheit: `1/10Pa` | r | r |  |
| Primärgebläse | `AK.pl_geblaesestufe` | 8221 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Saugzugstufe | `KSM.Saugzugstufe` | 8223 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Nächste Wartung in | `KSM.ServiceintervallReststunden` | 8224 | s16 / Input (FC04) | Einheit: `h` | r | r |  |
| Antrieb Fördersystem | `FS.o_motor_foerdersystem_1` | 8226 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Extern 1 | `KSM.i_extern1` | 8227 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Extern 2 | `KSM.i_extern2` | 8228 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Extern 3 | `KSM.i_extern3` | 8229 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Brennstoffverbrauch | `FS.pelletsverbrauch` | 8233 | u32, 2 Reg. / Input (FC04) | Einheit: `kg` | r | r |  |
| Brennstofffaktor | `EF2.Brennstofffaktor` | 8235 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Brennerleistung extern | `AK.externe_brennerleistung` | 8236 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Kesseltemp. Soll Extern | `AK.externe_kessel_solltemperatur` | 8237 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Saugturbine | `KSM.DO_Pelletssauger` | 8238 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Primärluftklappe | `CF2.i_pl_klappe_ist_promille` | 8242 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Sekundärluftklappe | `CF2.i_sl_klappe_ist_promille` | 8243 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Betriebsmodus | `CF2.betriebsmodus` | 8244 | s16 / Input (FC04) | `cf2_betriebsmodus_t` → 0=Kein, 1=Stückholz, 2=Pellets, 3=Stückholz (PM Nachlauf), 4=Relaistest | r | r |  |
| Füllraumtüre | `CF2.i_tuer_geschlossen` | 8245 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Maximaler Befüllgrad | `CF2.max_befuellgrad_anzeige` | 8246 | s16 / Input (FC04) | `cf2_max_befuellgrad_anzeige_t` → 0=Keine, 1=Ein Drittel, 2=Zwei Drittel, 3=Voll | r | r |  |
| Zündung Heizung | `CF2.o_zuendung_heizung_sh` | 8247 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 1 (125) | `KSM.o_multifunktionsausgang_1` | 9044 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 2 (127) | `KSM.o_multifunktionsausgang_2` | 9045 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 3 (124) | `KSM.o_multifunktionsausgang_3` | 9046 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 4 (126) | `KSM.o_multifunktionsausgang_4` | 9047 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Modbus Überhitzung | `KSM.modbus_ueberhitzung` | 9495 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r | → Glossar |
| Modbus Wärmeabnahme Max | `KSM.modbus_waermeabnahme_max` | 9496 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Füllstand Aschebehälter | `KSM.aschefuellstand` | 9497 | u16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Drehzahl Saugzug | `KSM.i_drehzahl_saugzug` | 9498 | u16 / Input (FC04) | Einheit: `Upm` | r | r |  |
| Brennerleistung bestimmt durch | `AK.anforderung_bl_ursache` | 9877 | s16 / Input (FC04) | `ak_anf_bl_ursache_t` → 1=Normalbetrieb, 2=Einmessen, 3=Kaminkehrer, 4=Extern, 5=Extern überhitzt, … (+8) | r | r |  |
| Wärmemenge gesamt | `KSM.waermemenge_gesamt_kwh` | 9878 | u32, 2 Reg. / Input (FC04) | Einheit: `1/10kWh` | r | r |  |
| Pelletkesselstatus | `KSM.kesselstatus_anzeige_simple` | 9970 | s16 / Input (FC04) | `kfk_kesselstatus_t` → 0=Aus, 1=Bereitschaft, 2=Zünden, 3=Betrieb, 4=Nachlauf, … (+3) | r | r |  |
| Brennstoffverbrauch Rücksetzzähler | `FS.pelletverbrauch_reset_counter` | 9988 | u16 / Input (FC04) | — | r | r |  |
| Kessel Ein/Aus | `AK.anlage_ein` | 24576 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | rw | rw |  |
| Solltemperatur 1 | `EF2.KesseltempSoll1` | 24577 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Solltemperatur 2 | `EF2.KesseltempSoll2` | 24578 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Rücklauftemperatur Minimum | `KSM.RuecklauftempMin` | 24581 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Externe Vorgabe | `AK.externe_vorgabe` | 24583 | s16 / Holding (FC03/06/16) | `ak_externe_vorgabe_t` → 0=Aus, 1=Temperatur, 2=Leistung, 3=Modbus, 4=Modbus | r | rw | → Glossar |
| Kesselprogramm | `AK.kesselprogramm` | 24584 | s16 / Holding (FC03/06/16) | `ak_kesselprogramm_t` → 0=Anforderung, 1=Zeitprogramm, 2=Dauerbetrieb, 3=Modbus Temperatur, 4=Modbus Leistung+Temperatur, … (+0) | r | rw |  |
| Automatische Zündung Funktion | `CF2.automatische_Zuendung_SH` | 24586 | s16 / Holding (FC03/06/16) | `cf2_automatische_zuendung_t` → 0=Aus, 1=Auswahl, 2=Anforderung, 3=Sofort | r | rw |  |
| Modbus Lifetick | `KSM.modbus_lifetick` | 24849 | u16 / Holding (FC03/06/16) | — | r | rw | → Glossar |
| Modbus Commit Lifetick | `KSM.modbus_commit_lifetick` | 24850 | u16 / Holding (FC03/06/16) | — | r | r | → Glossar |
| Modbus Kesseltemperatur | `KSM.modbus_kesseltemp_vorgabe` | 24851 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Kesselleistung | `KSM.modbus_leistung_vorgabe` | 24852 | s16 / Holding (FC03/06/16) | Einheit: `1/10%` | r | rw |  |
| Modbus Kesselanforderung | `KSM.modbus_kesselanforderung` | 24854 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | rw | → Glossar |
| Restmenge Brennstofflager | `KSM.restmenge_brennstofflager` | 24927 | u32, 2 Reg. / Holding (FC03/06/16) | Einheit: `kg` | rw | rw |  |
| Modbus Puffertemperatur oben für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_oben.value` | 24932 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Puffertemperatur oben für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_oben.status` | 24933 | s16 / Holding (FC03/06/16) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | rw |  |
| Modbus Puffertemperatur unten für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_unten.value` | 24934 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Puffertemperatur unten für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_unten.status` | 24935 | s16 / Holding (FC03/06/16) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | rw |  |
| Modbus Überstromnutzung | `SYSTEM.modbus_clee_ueberschusstrom` | 25040 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | rw | → Glossar |

## KWB CF 1

*67 eindeutige Registertypen.*

| Name | Parameter | Adresse(n) | Typ | Optionen / Wertebereich | User | Expert | Erklärung |
|---|---|---|---|---|:---:|:---:|---|
| Kesseltemperatur Ist (value) | `KSM.i_kesseltemp_ist.value` | 8197 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Kesseltemperatur Ist (status) | `KSM.i_kesseltemp_ist.status` | 8198 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Kesseltemperatur Soll | `KSM.kesseltemp_soll` | 8199…24585 (×2, Δ16386) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Kesselpumpe | `KSM.DO_Kesselpumpe` | 8200 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Kesselpumpe % | `KSM.kesselpumpe_steuerstufe` | 8201 | u16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Rücklauftemperatur Ist (value) | `KSM.i_ruecklauftemp_ist.value` | 8202 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Rücklauftemperatur Ist (status) | `KSM.i_ruecklauftemp_ist.status` | 8203 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Verbraucher Anforderung | `KSM.verbraucher_anforderung` | 8206 | s16 / Input (FC04) | `ksm_verbraucher_anforderung_t` → 0=Aus, 1=Heizkreis, 2=BWS, 3=Puffer | r | r |  |
| Kesselleistung | `KSM.brennerleistung` | 8207 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Kesselstatus | `KSM.kesselstatus_anzeige` | 8208 | s16 / Input (FC04) | `ksm_kesselstatus_anzeige_t` → 0=Aus, 1=Messbetrieb, 2=Betrieb (Reinigung), 3=Einmessen, 4=Betrieb, … (+46) | r | r |  |
| Volllaststunden | `KSM.Betriebsminuten_Summe` | 8209…8248 (×2, Δ39) | u32, 2 Reg. / Input (FC04) | Einheit: `min` | r | r |  |
| Status Pelletmodul | `AK.kesselstatus_anzeige_ak` | 8211 | s16 / Input (FC04) | `ksm_kesselstatus_anzeige_t` → 0=Aus, 1=Messbetrieb, 2=Betrieb (Reinigung), 3=Einmessen, 4=Betrieb, … (+46) | r | r |  |
| Status Stückholz | `CF2.kesselstatus_anzeige_sh` | 8212 | s16 / Input (FC04) | `ksm_kesselstatus_anzeige_t` → 0=Aus, 1=Messbetrieb, 2=Betrieb (Reinigung), 3=Einmessen, 4=Betrieb, … (+46) | r | r |  |
| Sauerstoff Ist | `KSM.O2Ist` | 8214 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Flammtemperatur Ist (value) | `KSM.i_flammtemp_ist.value` | 8215 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Flammtemperatur Ist (status) | `KSM.i_flammtemp_ist.status` | 8216 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Unterdruck Ist | `KSM.AI_Feuerraum_Unterdruck` | 8218 | s16 / Input (FC04) | Einheit: `1/10Pa` | r | r |  |
| Primärgebläse | `AK.pl_geblaesestufe` | 8221 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Saugzugstufe | `KSM.Saugzugstufe` | 8223 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Nächste Wartung in | `KSM.ServiceintervallReststunden` | 8224 | s16 / Input (FC04) | Einheit: `h` | r | r |  |
| Antrieb Fördersystem | `FS.o_motor_foerdersystem_1` | 8226 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Extern 1 | `KSM.i_extern1` | 8227 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Extern 2 | `KSM.i_extern2` | 8228 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Extern 3 | `KSM.i_extern3` | 8229 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Abgastemperatur (value) | `KSM.i_rauchgastemp_ist.value` | 8231 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Abgastemperatur (status) | `KSM.i_rauchgastemp_ist.status` | 8232 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Brennstoffverbrauch | `FS.pelletsverbrauch` | 8233 | u32, 2 Reg. / Input (FC04) | Einheit: `kg` | r | r |  |
| Brennstofffaktor | `EF2.Brennstofffaktor` | 8235 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Brennerleistung extern | `AK.externe_brennerleistung` | 8236 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Kesseltemp. Soll Extern | `AK.externe_kessel_solltemperatur` | 8237 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Saugturbine | `KSM.DO_Pelletssauger` | 8238 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Primärluftklappe | `CF2.i_pl_klappe_ist_promille` | 8242 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Sekundärluftklappe | `CF2.i_sl_klappe_ist_promille` | 8243 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Betriebsmodus | `CF2.betriebsmodus` | 8244 | s16 / Input (FC04) | `cf2_betriebsmodus_t` → 0=Kein, 1=Stückholz, 2=Pellets, 3=Stückholz (PM Nachlauf), 4=Relaistest | r | r |  |
| Füllraumtüre | `CF2.i_tuer_geschlossen` | 8245 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Maximaler Befüllgrad | `CF2.max_befuellgrad_anzeige` | 8246 | s16 / Input (FC04) | `cf2_max_befuellgrad_anzeige_t` → 0=Keine, 1=Ein Drittel, 2=Zwei Drittel, 3=Voll | r | r |  |
| Zündung Heizung | `CF2.o_zuendung_heizung_sh` | 8247 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 1 (125) | `KSM.o_multifunktionsausgang_1` | 9044 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 2 (127) | `KSM.o_multifunktionsausgang_2` | 9045 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 3 (124) | `KSM.o_multifunktionsausgang_3` | 9046 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 4 (126) | `KSM.o_multifunktionsausgang_4` | 9047 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Modbus Überhitzung | `KSM.modbus_ueberhitzung` | 9495 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r | → Glossar |
| Modbus Wärmeabnahme Max | `KSM.modbus_waermeabnahme_max` | 9496 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Füllstand Aschebehälter | `KSM.aschefuellstand` | 9497 | u16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Drehzahl Saugzug | `KSM.i_drehzahl_saugzug` | 9498 | u16 / Input (FC04) | Einheit: `Upm` | r | r |  |
| Brennerleistung bestimmt durch | `AK.anforderung_bl_ursache` | 9877 | s16 / Input (FC04) | `ak_anf_bl_ursache_t` → 1=Normalbetrieb, 2=Einmessen, 3=Kaminkehrer, 4=Extern, 5=Extern überhitzt, … (+8) | r | r |  |
| Wärmemenge gesamt | `KSM.waermemenge_gesamt_kwh` | 9878 | u32, 2 Reg. / Input (FC04) | Einheit: `1/10kWh` | r | r |  |
| Pelletkesselstatus | `KSM.kesselstatus_anzeige_simple` | 9970 | s16 / Input (FC04) | `kfk_kesselstatus_t` → 0=Aus, 1=Bereitschaft, 2=Zünden, 3=Betrieb, 4=Nachlauf, … (+3) | r | r |  |
| Brennstoffverbrauch Rücksetzzähler | `FS.pelletverbrauch_reset_counter` | 9988 | u16 / Input (FC04) | — | r | r |  |
| Kessel Ein/Aus | `AK.anlage_ein` | 24576 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | rw | rw |  |
| Solltemperatur 1 | `EF2.KesseltempSoll1` | 24577 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Solltemperatur 2 | `EF2.KesseltempSoll2` | 24578 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Rücklauftemperatur Minimum | `KSM.RuecklauftempMin` | 24581 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Externe Vorgabe | `AK.externe_vorgabe` | 24583 | s16 / Holding (FC03/06/16) | `ak_externe_vorgabe_t` → 0=Aus, 1=Temperatur, 2=Leistung, 3=Modbus, 4=Modbus | r | rw | → Glossar |
| Kesselprogramm | `AK.kesselprogramm` | 24584 | s16 / Holding (FC03/06/16) | `ak_kesselprogramm_t` → 0=Anforderung, 1=Zeitprogramm, 2=Dauerbetrieb, 3=Modbus Temperatur, 4=Modbus Leistung+Temperatur, … (+0) | r | rw |  |
| Automatische Zündung Funktion | `CF2.automatische_Zuendung_SH` | 24586 | s16 / Holding (FC03/06/16) | `cf2_automatische_zuendung_t` → 0=Aus, 1=Auswahl, 2=Anforderung, 3=Sofort | r | rw |  |
| Modbus Lifetick | `KSM.modbus_lifetick` | 24849 | u16 / Holding (FC03/06/16) | — | r | rw | → Glossar |
| Modbus Commit Lifetick | `KSM.modbus_commit_lifetick` | 24850 | u16 / Holding (FC03/06/16) | — | r | r | → Glossar |
| Modbus Kesseltemperatur | `KSM.modbus_kesseltemp_vorgabe` | 24851 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Kesselleistung | `KSM.modbus_leistung_vorgabe` | 24852 | s16 / Holding (FC03/06/16) | Einheit: `1/10%` | r | rw |  |
| Modbus Kesselanforderung | `KSM.modbus_kesselanforderung` | 24854 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | rw | → Glossar |
| Restmenge Brennstofflager | `KSM.restmenge_brennstofflager` | 24927 | u32, 2 Reg. / Holding (FC03/06/16) | Einheit: `kg` | rw | rw |  |
| Modbus Puffertemperatur oben für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_oben.value` | 24932 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Puffertemperatur oben für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_oben.status` | 24933 | s16 / Holding (FC03/06/16) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | rw |  |
| Modbus Puffertemperatur unten für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_unten.value` | 24934 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Puffertemperatur unten für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_unten.status` | 24935 | s16 / Holding (FC03/06/16) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | rw |  |
| Modbus Überstromnutzung | `SYSTEM.modbus_clee_ueberschusstrom` | 25040 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | rw | → Glossar |

## KWB CF 1.5

*65 eindeutige Registertypen.*

| Name | Parameter | Adresse(n) | Typ | Optionen / Wertebereich | User | Expert | Erklärung |
|---|---|---|---|---|:---:|:---:|---|
| Kesseltemperatur Ist (value) | `KSM.i_kesseltemp_ist.value` | 8197 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Kesseltemperatur Ist (status) | `KSM.i_kesseltemp_ist.status` | 8198 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Kesseltemperatur Soll | `KSM.kesseltemp_soll` | 8199…24585 (×2, Δ16386) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Kesselpumpe | `KSM.DO_Kesselpumpe` | 8200 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Kesselpumpe % | `KSM.kesselpumpe_steuerstufe` | 8201 | u16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Rücklauftemperatur Ist (value) | `KSM.i_ruecklauftemp_ist.value` | 8202 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Rücklauftemperatur Ist (status) | `KSM.i_ruecklauftemp_ist.status` | 8203 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Verbraucher Anforderung | `KSM.verbraucher_anforderung` | 8206 | s16 / Input (FC04) | `ksm_verbraucher_anforderung_t` → 0=Aus, 1=Heizkreis, 2=BWS, 3=Puffer | r | r |  |
| Kesselleistung | `KSM.brennerleistung` | 8207 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Kesselstatus | `KSM.kesselstatus_anzeige` | 8208 | s16 / Input (FC04) | `ksm_kesselstatus_anzeige_t` → 0=Aus, 1=Messbetrieb, 2=Betrieb (Reinigung), 3=Einmessen, 4=Betrieb, … (+46) | r | r |  |
| Volllaststunden | `KSM.Betriebsminuten_Summe` | 8209…8248 (×2, Δ39) | u32, 2 Reg. / Input (FC04) | Einheit: `min` | r | r |  |
| Status Pelletmodul | `AK.kesselstatus_anzeige_ak` | 8211 | s16 / Input (FC04) | `ksm_kesselstatus_anzeige_t` → 0=Aus, 1=Messbetrieb, 2=Betrieb (Reinigung), 3=Einmessen, 4=Betrieb, … (+46) | r | r |  |
| Status Stückholz | `CF2.kesselstatus_anzeige_sh` | 8212 | s16 / Input (FC04) | `ksm_kesselstatus_anzeige_t` → 0=Aus, 1=Messbetrieb, 2=Betrieb (Reinigung), 3=Einmessen, 4=Betrieb, … (+46) | r | r |  |
| Sauerstoff Ist | `KSM.O2Ist` | 8214 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Flammtemperatur Ist (value) | `KSM.i_flammtemp_ist.value` | 8215 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Flammtemperatur Ist (status) | `KSM.i_flammtemp_ist.status` | 8216 | s16 / Input (FC04) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | r |  |
| Unterdruck Ist | `KSM.AI_Feuerraum_Unterdruck` | 8218 | s16 / Input (FC04) | Einheit: `1/10Pa` | r | r |  |
| Primärgebläse | `AK.pl_geblaesestufe` | 8221 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Saugzugstufe | `KSM.Saugzugstufe` | 8223 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Nächste Wartung in | `KSM.ServiceintervallReststunden` | 8224 | s16 / Input (FC04) | Einheit: `h` | r | r |  |
| Antrieb Fördersystem | `FS.o_motor_foerdersystem_1` | 8226 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Extern 1 | `KSM.i_extern1` | 8227 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Extern 2 | `KSM.i_extern2` | 8228 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Extern 3 | `KSM.i_extern3` | 8229 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Brennstoffverbrauch | `FS.pelletsverbrauch` | 8233 | u32, 2 Reg. / Input (FC04) | Einheit: `kg` | r | r |  |
| Brennstofffaktor | `EF2.Brennstofffaktor` | 8235 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Brennerleistung extern | `AK.externe_brennerleistung` | 8236 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Kesseltemp. Soll Extern | `AK.externe_kessel_solltemperatur` | 8237 | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Saugturbine | `KSM.DO_Pelletssauger` | 8238 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Primärluftklappe | `CF2.i_pl_klappe_ist_promille` | 8242 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Sekundärluftklappe | `CF2.i_sl_klappe_ist_promille` | 8243 | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Betriebsmodus | `CF2.betriebsmodus` | 8244 | s16 / Input (FC04) | `cf2_betriebsmodus_t` → 0=Kein, 1=Stückholz, 2=Pellets, 3=Stückholz (PM Nachlauf), 4=Relaistest | r | r |  |
| Füllraumtüre | `CF2.i_tuer_geschlossen` | 8245 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Maximaler Befüllgrad | `CF2.max_befuellgrad_anzeige` | 8246 | s16 / Input (FC04) | `cf2_max_befuellgrad_anzeige_t` → 0=Keine, 1=Ein Drittel, 2=Zwei Drittel, 3=Voll | r | r |  |
| Zündung Heizung | `CF2.o_zuendung_heizung_sh` | 8247 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 1 (125) | `KSM.o_multifunktionsausgang_1` | 9044 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 2 (127) | `KSM.o_multifunktionsausgang_2` | 9045 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 3 (124) | `KSM.o_multifunktionsausgang_3` | 9046 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Multifunktionsausgang 4 (126) | `KSM.o_multifunktionsausgang_4` | 9047 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Modbus Überhitzung | `KSM.modbus_ueberhitzung` | 9495 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r | → Glossar |
| Modbus Wärmeabnahme Max | `KSM.modbus_waermeabnahme_max` | 9496 | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| Füllstand Aschebehälter | `KSM.aschefuellstand` | 9497 | u16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Drehzahl Saugzug | `KSM.i_drehzahl_saugzug` | 9498 | u16 / Input (FC04) | Einheit: `Upm` | r | r |  |
| Brennerleistung bestimmt durch | `AK.anforderung_bl_ursache` | 9877 | s16 / Input (FC04) | `ak_anf_bl_ursache_t` → 1=Normalbetrieb, 2=Einmessen, 3=Kaminkehrer, 4=Extern, 5=Extern überhitzt, … (+8) | r | r |  |
| Wärmemenge gesamt | `KSM.waermemenge_gesamt_kwh` | 9878 | u32, 2 Reg. / Input (FC04) | Einheit: `1/10kWh` | r | r |  |
| Pelletkesselstatus | `KSM.kesselstatus_anzeige_simple` | 9970 | s16 / Input (FC04) | `kfk_kesselstatus_t` → 0=Aus, 1=Bereitschaft, 2=Zünden, 3=Betrieb, 4=Nachlauf, … (+3) | r | r |  |
| Brennstoffverbrauch Rücksetzzähler | `FS.pelletverbrauch_reset_counter` | 9988 | u16 / Input (FC04) | — | r | r |  |
| Kessel Ein/Aus | `AK.anlage_ein` | 24576 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | rw | rw |  |
| Solltemperatur 1 | `EF2.KesseltempSoll1` | 24577 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Solltemperatur 2 | `EF2.KesseltempSoll2` | 24578 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Rücklauftemperatur Minimum | `KSM.RuecklauftempMin` | 24581 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Externe Vorgabe | `AK.externe_vorgabe` | 24583 | s16 / Holding (FC03/06/16) | `ak_externe_vorgabe_t` → 0=Aus, 1=Temperatur, 2=Leistung, 3=Modbus, 4=Modbus | r | rw | → Glossar |
| Kesselprogramm | `AK.kesselprogramm` | 24584 | s16 / Holding (FC03/06/16) | `ak_kesselprogramm_t` → 0=Anforderung, 1=Zeitprogramm, 2=Dauerbetrieb, 3=Modbus Temperatur, 4=Modbus Leistung+Temperatur, … (+0) | r | rw |  |
| Automatische Zündung Funktion | `CF2.automatische_Zuendung_SH` | 24586 | s16 / Holding (FC03/06/16) | `cf2_automatische_zuendung_t` → 0=Aus, 1=Auswahl, 2=Anforderung, 3=Sofort | r | rw |  |
| Modbus Lifetick | `KSM.modbus_lifetick` | 24849 | u16 / Holding (FC03/06/16) | — | r | rw | → Glossar |
| Modbus Commit Lifetick | `KSM.modbus_commit_lifetick` | 24850 | u16 / Holding (FC03/06/16) | — | r | r | → Glossar |
| Modbus Kesseltemperatur | `KSM.modbus_kesseltemp_vorgabe` | 24851 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Kesselleistung | `KSM.modbus_leistung_vorgabe` | 24852 | s16 / Holding (FC03/06/16) | Einheit: `1/10%` | r | rw |  |
| Modbus Kesselanforderung | `KSM.modbus_kesselanforderung` | 24854 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | rw | → Glossar |
| Restmenge Brennstofflager | `KSM.restmenge_brennstofflager` | 24927 | u32, 2 Reg. / Holding (FC03/06/16) | Einheit: `kg` | rw | rw |  |
| Modbus Puffertemperatur oben für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_oben.value` | 24932 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Puffertemperatur oben für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_oben.status` | 24933 | s16 / Holding (FC03/06/16) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | rw |  |
| Modbus Puffertemperatur unten für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_unten.value` | 24934 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Modbus Puffertemperatur unten für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_unten.status` | 24935 | s16 / Holding (FC03/06/16) | `system_sensor_status_t` → 0=Defekt, 1=Fehlt, 2=OK | r | rw |  |
| Modbus Überstromnutzung | `SYSTEM.modbus_clee_ueberschusstrom` | 25040 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | rw | → Glossar |

## KWB EasyAir Plus

*49 eindeutige Registertypen.*

| Name | Parameter | Adresse(n) | Typ | Optionen / Wertebereich | User | Expert | Erklärung |
|---|---|---|---|---|:---:|:---:|---|
| WEZ Solltemperatur | `EAPDEV.vorlauftemperatur_soll` | 10230…10231 (×2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Momentanleistung | `EAPDEV.momentanleistung` | 10238…10239 (×2) | u16 / Input (FC04) | Einheit: `1/100kW` | r | r |  |
| Verdichter Drehzahl Ist | `EAPDEV.drehzahl_ist` | 10246…10247 (×2) | u16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Verdichter Drehzahl Soll | `EAPDEV.drehzahl_soll` | 10254…10255 (×2) | u16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Aufgen. elektr. Leistung | `EAPDEV.aufgenommene_elektr_leistung` | 10262…10263 (×2) | u16 / Input (FC04) | Einheit: `1/100kW` | r | r |  |
| Vorlauftemperatur Ist | `EAPDEV.vorlauftemperatur_ist` | 10270…10271 (×2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Rücklauftemperatur Ist | `EAPDEV.ruecklauftemperatur_ist` | 10278…10279 (×2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Ansauglufttemperatur | `EAPDEV.ansauglufttemperatur` | 10286…10287 (×2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Sauggastemperatur | `EAPDEV.sauggastemperatur` | 10294…10295 (×2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Heissgastemperatur | `EAPDEV.heissgastemperatur` | 10302…10303 (×2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Drehzahl Ventilator | `EAPDEV.drehzahl_ventilator` | 10310…10311 (×2) | u16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Volumenstrom | `EAPDEV.volumenstrom` | 10318…10319 (×2) | u16 / Input (FC04) | Einheit: `1/10l/min` | r | r |  |
| Volumenstrom gemittelt | `EAPDEV.volumenstrom_gemittelt` | 10326…10327 (×2) | u16 / Input (FC04) | Einheit: `1/10l/min` | r | r |  |
| Drehzahl CP | `EAPDEV.drehzahl_cp` | 10334…10335 (×2) | s16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Überhitzung | `EAPDEV.ueberhitzung` | 10342…10343 (×2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Unterkühlung | `EAPDEV.unterkuehlung` | 10350…10351 (×2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Verdampfungstemperatur | `EAPDEV.verdampfungstemperatur` | 10358…10359 (×2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Kondensationstemperatur | `EAPDEV.kondensationstemperatur` | 10366…10367 (×2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Niederdruck (relativ) | `EAPDEV.niederdruck` | 10374…10375 (×2) | u16 / Input (FC04) | Einheit: `1/10bar` | r | r |  |
| Hochdruck (relativ) | `EAPDEV.hochdruck` | 10382…10383 (×2) | u16 / Input (FC04) | Einheit: `1/10bar` | r | r |  |
| Temp. Flüssigkeitsleitung | `EAPDEV.temperatur_fluessigkeitsleitung` | 10390…10391 (×2) | s16 / Input (FC04) | Einheit: `1/10°C` | r | r |  |
| Position 1. EX-Ventil | `EAPDEV.position_erstes_expansionsventil` | 10398…10399 (×2) | u16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Position 2. EX-Ventil | `EAPDEV.position_zweites_expansionsventi` | 10406…10407 (×2) | u16 / Input (FC04) | Einheit: `1/10%` | r | r |  |
| Bivalenz-ELH | `EAPDEV.bivalenz_elh` | 10414…10415 (×2) | s16 / Input (FC04) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | r |  |
| COP | `EAPDEV.cop` | 10422…10423 (×2) | u16 / Input (FC04) | Einheit: `1/10` | r | r |  |
| Erw. Betriebsstatus | `EAPDEV.erweiterter_betriebsstatus` | 10430…10431 (×2) | s16 / Input (FC04) | `eap_erweiterter_betriebsstatus_t` → 0=Aus, 1=Heizen Heizkreis, 2=Kühlen, 4=Heizen WW | r | r |  |
| Status | `EAPDEV.status` | 10438…10439 (×2) | s16 / Input (FC04) | `eap_status_t` → 0=Aus, 1=Betrieb, 2=Kühlen, 3=Sperre (Bivalenz, WW), 4=WW Heizbetrieb, … (+22) | r | r |  |
| Anforderung durch | `EAPDEV.anforderung_ursache` | 10446…10447 (×2) | s16 / Input (FC04) | `eap_anforderung_ursache_t` → 0=Aus, 1=Heizen Heizkreis, 2=Heizen Warmw., 3=Kühlen, 4=Relaistest, … (+6) | r | r |  |
| Zustand Wärmepumpe | `EAPDEV.zustand_waermepumpe` | 10454…10455 (×2) | s16 / Input (FC04) | `eap_zustand_t` → 0=Ok, 1=Fehler, 2=Warnung | r | r |  |
| Modbus Lifetick | `KSM.modbus_lifetick` | 24849 | u16 / Holding (FC03/06/16) | — | r | rw | → Glossar |
| Modbus Commit Lifetick | `KSM.modbus_commit_lifetick` | 24850 | u16 / Holding (FC03/06/16) | — | r | r | → Glossar |
| Sollwert für Heizen | `EAPDEV.sollwert_heizkreisbetrieb` | 25168…25169 (×2) | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | r |  |
| Sollwert für Warmwasser | `EAPDEV.sollwert_speicherbetrieb` | 25176…25177 (×2) | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | r |  |
| Sollwert für Kühlen | `EAPDEV.sollwert_kuehlbetrieb` | 25184…25185 (×2) | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | r |  |
| Leistungsbegrenzung | `EAPDEV.leistungsbegrenzung` | 25192…25193 (×2) | u16 / Holding (FC03/06/16) | Einheit: `1/10%` | r | r |  |
| Modbus VL-Temp. Soll | `EAPDEV.modbus_vorlauf_soll` | 25200…25201 (×2) | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | r | rw |  |
| Mobus Max. Verdichter Soll | `EAPDEV.modbus_max_verdichterdrehz_soll` | 25208…25209 (×2) | u16 / Holding (FC03/06/16) | Einheit: `1/10%` | r | rw |  |
| Max. Leistung Heizen | `EAPDEV.max_leistung_heizen` | 25216…25217 (×2) | s16 / Holding (FC03/06/16) | Einheit: `1/10%` | r | r |  |
| Min. Leistung Heizen | `EAPDEV.min_leistung_heizen` | 25224…25225 (×2) | s16 / Holding (FC03/06/16) | Einheit: `1/10%` | r | r |  |
| Max. Leistung Warmwasser | `EAPDEV.max_leistung_warmwasser` | 25232…25233 (×2) | s16 / Holding (FC03/06/16) | Einheit: `1/10%` | r | r |  |
| Min. Leistung Warmwasser | `EAPDEV.min_leistung_warmwasser` | 25240…25241 (×2) | s16 / Holding (FC03/06/16) | Einheit: `1/10%` | r | r |  |
| Max. Leistung Kühlen | `EAPDEV.max_leistung_kuehlen` | 25248…25249 (×2) | s16 / Holding (FC03/06/16) | Einheit: `1/10%` | r | r |  |
| Min. Leistung Kühlen | `EAPDEV.min_leistung_kuehlen` | 25256…25257 (×2) | s16 / Holding (FC03/06/16) | Einheit: `1/10%` | r | r |  |
| Zeitfenster Beginn | `EAPDEV.fluester1_beginn` | 25264…25281 (×4, unregelm.) | u16 / Holding (FC03/06/16) | — | r | r |  |
| Zeitfenster Ende | `EAPDEV.fluester1_ende` | 25272…25289 (×4, unregelm.) | u16 / Holding (FC03/06/16) | — | r | r |  |
| Max. Drehzahl | `EAPDEV.fluester_max_drehzahl` | 25296…25297 (×2) | s16 / Holding (FC03/06/16) | Einheit: `1/10%` | r | r |  |
| SG Boilerladung | `EAP.sg_boilerladung_modbus` | 25350 | s16 / Holding (FC03/06/16) | `system_ein_aus_t` → 0=Aus, 1=Ein | r | rw |  |
| Brauchw. Solltemp. | `EAP.brauchwasser_solltemp` | 25351 | s16 / Holding (FC03/06/16) | Einheit: `1/10°C` | rw | rw |  |
| Max.Leistung WW | `EAP.sg_max_leistung_ww_modbus` | 25377 | s16 / Holding (FC03/06/16) | Einheit: `1/10%` | r | rw |  |

## Wertetabellen

Vollständige Auflistung aller Wertetabellen, die in der Spalte *Optionen / Wertebereich* referenziert werden.

### `ak_anf_bl_ursache_t`

| Wert | Bedeutung |
|---:|---|
| 1 | Normalbetrieb |
| 2 | Einmessen |
| 3 | Kaminkehrer |
| 4 | Extern |
| 5 | Extern überhitzt |
| 6 | Stoker leeren |
| 7 | Min. für Reinigung |
| 8 | Stoker Überhitzung |
| 9 | Zyklusbetrieb |
| 10 | Puffermanagement |
| 11 | PuMgmt. überhitzt |
| 12 | Modbus |
| 13 | Modbus Clee |

### `ak_externe_vorgabe_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Aus |
| 1 | Temperatur |
| 2 | Leistung |
| 3 | Modbus |
| 4 | Modbus |

### `ak_kesselprogramm_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Anforderung |
| 1 | Zeitprogramm |
| 2 | Dauerbetrieb |
| 3 | Modbus Temperatur |
| 4 | Modbus Leistung+Temperatur |

### `boiler_programm_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Zeit |
| 1 | Temp. |
| 2 | Aus |

### `boiler_quelle_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Wärmepumpe 1 |
| 1 | Puffer |
| 2 | WP1 oder Puffer |

### `boiler_status_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Störung |
| 1 | Aus |
| 2 | Legionellenschutz |
| 3 | Urlaub |
| 4 | Einmalladung |
| 5 | Außerhalb der Ladezeit |
| 6 | Laden bis Solltemp. |
| 7 | Temp. ausreichend |
| 8 | Blockierschutz |
| 9 | Warten Pumpenfreigabe |
| 10 | Kessel Überhitzung |
| 11 | ZWQ Überhitzung |
| 12 | max. Wärmeabnahme |
| 13 | Nachlauf |
| 14 | Nachlauf (Warten Freig.) |
| 15 | SmartGrid Heizen |
| 16 | SmartGrid Clee Heizen |

### `cf2_automatische_zuendung_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Aus |
| 1 | Auswahl |
| 2 | Anforderung |
| 3 | Sofort |

### `cf2_betriebsmodus_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Kein |
| 1 | Stückholz |
| 2 | Pellets |
| 3 | Stückholz (PM Nachlauf) |
| 4 | Relaistest |

### `cf2_max_befuellgrad_anzeige_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Keine |
| 1 | Ein Drittel |
| 2 | Zwei Drittel |
| 3 | Voll |

### `comfortenergy_status_t`

| Wert | Bedeutung |
|---:|---|
| 0 | deaktiviert |
| 1 | offline |
| 2 | online |

### `eap_anforderung_ursache_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Aus |
| 1 | Heizen Heizkreis |
| 2 | Heizen Warmw. |
| 3 | Kühlen |
| 4 | Relaistest |
| 5 | Testbetrieb |
| 6 | Modbus Aus |
| 7 | Modb. Heizen Hk |
| 8 | Modb. Heizen Ww |
| 9 | Modbus Kühlen |
| 10 | Gesperrt durch ZWQ |

### `eap_erweiterter_betriebsstatus_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Aus |
| 1 | Heizen Heizkreis |
| 2 | Kühlen |
| 4 | Heizen WW |

### `eap_status_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Aus |
| 1 | Betrieb |
| 2 | Kühlen |
| 3 | Sperre (Bivalenz, WW) |
| 4 | WW Heizbetrieb |
| 5 | WP Frostschutz |
| 6 | WP Temp. zu tief |
| 7 | WP-Vorlauf zu hoch |
| 8 | Abtauung |
| 9 | Kühlen (passiv) |
| 11 | HD Störung |
| 12 | Niederdruck Störung |
| 16 | Wiedereinschalt Verzögerung |
| 17 | EVU-Sperre |
| 18 | Vorlaufzeit prim. |
| 19 | Nachlaufzeit prim. |
| 44 | MOP |
| 49 | Erfolglose Abtauung |
| 51 | Vorlaufzeit Kond.Pumpe |
| 55 | Störung Kommunikation |
| 73 | Durchfluss WQ/GW Kreis |
| 77 | Begrenzung Verdichter |
| 95 | Flüsterbetrieb |
| 96 | Leistungsbegrenzung aktiv |
| 97 | Kompressor Öl vorheizen |
| 98 | Kaltstart |
| 99 | Nicht konfiguriert |

### `eap_zustand_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Ok |
| 1 | Fehler |
| 2 | Warnung |

### `hk_modbus_programm_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Frostschutz |
| 1 | Absenk  auto |
| 2 | Komfort auto |
| 3 | Absenk |
| 4 | Komfort |

### `hk_modbus_temperatur_auswahl_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Vorlauftemp. Soll |
| 1 | Raumtemp. Soll |

### `hk_programm_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Automatik |
| 1 | Frostschutz |
| 2 | Aus |
| 3 | Komfort |
| 4 | Absenk |

### `hk_status_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Absenk |
| 1 | Komfort |
| 2 | Frostschutz |
| 3 | Urlaub |
| 4 | Aus |
| 5 | Estrich |
| 6 | Max. Wärmeabnahme |
| 7 | Max. Wärmeabnahme |
| 8 | Modbus Vorlauftemp. Soll |
| 9 | Modbus Absenk auto |
| 10 | Modbus Komfort auto |
| 11 | Modbus Frostschutz |
| 12 | Vormischer Betrieb |
| 13 | Modbus Absenk |
| 14 | Modbus Komfort |

### `kesselseriennummer_san_code_t`

| Wert | Bedeutung |
|---:|---|
| 0 | ... |
| 1 | 000- |
| 2 | 02SAN |
| 3 | 03SAN |
| 4 | 04SAN |
| 5 | 05SAN |
| 6 | 06SAN |
| 7 | 07SAN |
| 8 | 08SAN |
| 9 | 09SAN |
| 10 | 10SAN |
| 11 | 11SAN |
| 12 | 12SAN |
| 13 | 13SAN |
| 14 | 14SAN |
| 15 | 15SAN |
| 16 | 16SAN |
| 17 | 17SAN |
| 18 | 18SAN |
| 19 | 19SAN |
| 20 | 20SAN |
| 21 | 21SAN |
| 22 | 22SAN |
| 23 | 23SAN |
| 24 | 24SAN |
| 25 | 25SAN |
| 26 | 26SAN |
| 27 | 27SAN |
| 28 | 28SAN |
| 29 | 29SAN |
| 30 | 30SAN |
| 31 | 31SAN |
| 32 | 32SAN |
| 33 | 33SAN |
| 34 | 34SAN |
| 35 | 35SAN |
| 36 | 36SAN |
| 37 | 37SAN |
| 38 | 38SAN |
| 39 | 39SAN |
| 40 | 40SAN |
| 41 | 41SAN |
| 42 | 42SAN |
| 43 | 43SAN |
| 44 | 44SAN |
| 45 | 45SAN |
| 46 | 46SAN |
| 47 | 47SAN |
| 48 | 48SAN |
| 49 | 49SAN |
| 50 | 50SAN |

### `kfk_kesselstatus_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Aus |
| 1 | Bereitschaft |
| 2 | Zünden |
| 3 | Betrieb |
| 4 | Nachlauf |
| 5 | Störung |
| 6 | Bereit (SH) |
| 7 | Betrieb (SH) |

### `kfs_angeforderte_kessel_t`

| Wert | Bedeutung |
|---:|---|
| 1 | 1 |
| 2 | 2 |
| 3 | 3 |
| 4 | 4 |
| 5 | 5 |
| 6 | 6 |
| 7 | 7 |
| 8 | 8 |

### `kfs_profile_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Winter |
| 1 | Sommer |

### `ksm_kesselstatus_anzeige_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Aus |
| 1 | Messbetrieb |
| 2 | Betrieb (Reinigung) |
| 3 | Einmessen |
| 4 | Betrieb |
| 5 | Nachlauf |
| 6 | Neustart |
| 7 | Störung Nachlauf |
| 8 | Störung Aus |
| 9 | Wartung |
| 10 | Bereit (-Zuendanf) |
| 11 | Zünden Start Saugzug |
| 12 | Zünden FS Füllen |
| 13 | Zünden Einschieben 1 |
| 14 | Zünden Einschieben 3 |
| 15 | Zünden Heizen |
| 16 | Heizen Durchzünden |
| 17 | Zünden Einschieben 2 |
| 18 | Zünden Warten |
| 19 | Durchzünden |
| 20 | 1. IB Betrieb |
| 21 | Bereit (-Ext1) |
| 22 | Bereit (-Zweitkessel) |
| 23 | Bereit (-FS) |
| 24 | Bereit (-Reinigung) |
| 25 | Bereit (+Stop) |
| 26 | Bereit (-Ext3) |
| 27 | Bereit (-Lambdasonde) |
| 30 | Bereit (-Anf) |
| 31 | Bereit (+Wartezeit) |
| 32 | Bereit (+Anf) |
| 34 | Betrieb Leerschieben |
| 35 | Aus |
| 36 | Anheizen |
| 37 | Warten Zündanf. |
| 38 | Warten Zündfreig. |
| 39 | Start Zündung |
| 40 | Zünden |
| 41 | Heizen |
| 42 | Feuerhaltung |
| 43 | Feuer aus |
| 44 | Störung Feuer aus |
| 45 | Tür offen |
| 46 | Überhitzung |
| 47 | Störung Feuerhaltung |
| 49 | Sh aus, PM freigegeben |
| 50 | Start Pelletmodul |
| 51 | Pelletmodul Gesperrt |
| 52 | Wartung |
| 53 | Betrieb vor Wartung |
| 54 | Wartungsabschaltung |

### `ksm_verbraucher_anforderung_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Aus |
| 1 | Heizkreis |
| 2 | BWS |
| 3 | Puffer |

### `puffer_o_umschaltventil_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Nicht vorhanden |
| 1 | Oben |
| 2 | Unten |

### `puffer_programm_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Zeit |
| 1 | Temperatur |
| 2 | Aus |
| 3 | Zeit+ |
| 4 | Sommer |

### `solar_status_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Aus |
| 1 | Handbetrieb |
| 2 | Laden Speicher 1 |
| 3 | Laden Speicher 2 |
| 4 | Störung |
| 5 | Solarschutz |
| 6 | Rückkühlung 1 |
| 7 | Rückkühlung 2 |
| 8 | Frostschutz |

### `solar_status_ursache_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Programm Aus |
| 1 | Handbetrieb |
| 2 | Kollektortemperatur ausreichend |
| 3 | Temperaturdifferenz Kollektor / Speicher 1 zu gering |
| 4 | Maximaltemperatur Speicher 1 überschritten |
| 5 | Maximaltemperatur Speicher 2 überschritten |
| 6 | Absoluter Vorrang (Kollektortemperatur zu gering) |
| 7 | Blockierschutz |
| 8 | Kollektortemperatur zu hoch |
| 9 | Alarm im Solarkreis aktiv |
| 10 | Maximaltemperatur Speicher 1+2 überschritten |
| 11 | Kollektorminimaltemperatur unterschritten |
| 12 | Frostschutz |
| 13 | Intervallfunktion |
| 14 | Rückkühlung |

### `system_ein_aus_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Aus |
| 1 | Ein |

### `system_gui_kessel_typ_t`

| Wert | Bedeutung |
|---:|---|
| 0 | - |
| 1 | KWB Easyfire |
| 2 | KWB CF 2 |
| 3 | KWB Combifire |
| 4 | KWB Multifire |
| 5 | KWB Pelletfire+ |
| 6 | KWB CF 1 |
| 7 | Kein |
| 8 | KWB CF 1.5 |
| 9 | KWB Easyfire 3 |
| 10 | KWB CF 1E |

### `system_sensor_status_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Defekt |
| 1 | Fehlt |
| 2 | OK |

### `system_yes_no_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Nein |
| 1 | Ja |

### `uebergabestation_status_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Aus |
| 1 | Vorlauf |
| 2 | Betrieb |
| 3 | Rücklauftemp. Begrenzung |
| 4 | Nachlauf |
| 5 | Notlauf |

### `wmm_rolle_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Autonom |
| 1 | KFS |
| 2 | Powerfire 1 150-300kW |
| 3 | EasyAir Plus |
| 4 | Powerfire 2 400-500kW |

### `zirk_programm_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Aus |
| 1 | Automatik |
| 2 | Dauerbetrieb |

### `zk_status_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Aus |
| 1 | Betrieb |
| 2 | Überhitzung |
| 3 | Verzögerung |
| 4 | Störung |
| 5 | Mindestlaufzeit |
| 6 | Mindeststehzeit |
| 7 | Betrieb Modbus |

### `zus_wq_wp_status_t`

| Wert | Bedeutung |
|---:|---|
| 0 | Aus |
| 1 | Betrieb |
| 2 | Mindestlaufzeit |
| 3 | Mindeststehzeit |

## Anhang A — Vollständige Adressliste

Alle 2796 Modbus-Adressen, sortiert nach Quelle und Adresse.

### Universal (`modbus_registers.json`, 22 Register)

| Adresse | Name (mit Slot) | Parameter | Typ | FC | User | Expert |
|---:|---|---|---|:---:|:---:|:---:|
| 8192 | Software (major) | `SYSTEM.sw_version.major` | u16 | 04 | r | r |
| 8193 | Software (minor) | `SYSTEM.sw_version.minor` | u16 | 04 | r | r |
| 8194 | Software (patch) | `SYSTEM.sw_version.patch` | u16 | 04 | r | r |
| 8195 | Revision | `SYSTEM.sw_revision` | u32 | 04 | r | r |
| 8204 | Anlage OK | `KSM.anlage_kein_alarm_keine_stoerung` | s16 | 04 | r | r |
| 8205 | Summenstörung | `KSM.summen_alarm_oder_stoerung` | s16 | 04 | r | r |
| 8252 | Anzahl Alarme | `SYSTEM.alarme_total` | u32 | 04 | r | r |
| 8254 | Anzahl offene Alarme | `SYSTEM.alarme_offen` | u32 | 04 | r | r |
| 10022 | Summenstörung mit Kesselabschaltung | `KSM.anlage_stoerung_mit_abschaltung` | s16 | 04 | r | r |
| 10024 | Kesseltyp | `SYSTEM.gui_kessel_typ` | s16 | 04 | r | r |
| 10025 | WMM Rolle | `SYSTEM.wmm_rolle` | s16 | 04 | r | r |
| 10228 | BGE | `SYSTEM.bge_serial_number` | u32 | 04 | r | r |
| 24582 | Alarme beheben | `SYSTEM.alarme_beheben_von_extern` | s16 | 03 | rw | rw |
| 25159 | Modbus Lifetick Kessel ignorieren | `SYSTEM.modbus_lifetick_ignore_kessel` | s16 | 03 | r | rw |
| 25160 | Modbus Lifetick Heizkreise ignorieren | `SYSTEM.modbus_lifetick_ignore_hk` | s16 | 03 | r | rw |
| 25161 | Modbus Lifetick Solaranlagen ignorieren | `SYSTEM.modbus_lifetick_ignore_solar` | s16 | 03 | r | rw |
| 25162 | Modbus Lifetick Zweitwärmequellen ignorieren (Wärmepumpe oder Kessel) | `SYSTEM.modbus_lifetick_ignore_zwq` | s16 | 03 | r | rw |
| 25163 | Modbus Lifetick Zusatzwärmequellen ignorieren | `SYSTEM.modbus_lifetick_ignore_zuswq` | s16 | 03 | r | rw |
| 25164 | Modbus Lifetick Überschussstromkontakt (MFA) ignorieren | `SYSTEM.modbus_lifetick_ignor_uestrommfa` | s16 | 03 | r | rw |
| 25165 | SAN Code | `SYSTEM.kessel_seriennummer_san_code` | s16 | 03 | r | r |
| 25166 | Seriennummer | `SYSTEM.kessel_seriennummer` | u32 | 03 | r | r |
| 25304 | Modbus Lifetick Wärmepumpe ignorieren | `SYSTEM.modbus_lifetick_ignore_wp` | s16 | 03 | r | rw |

### Heizkreise (`heating_circuits.json`, 449 Register)

| Adresse | Name (mit Slot) | Parameter | Typ | FC | User | Expert |
|---:|---|---|---|:---:|:---:|:---:|
| 8260 | HK 1.1: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8261 | HK 1.1: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8262 | HK 1.2: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8263 | HK 1.2: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8264 | HK 2.1: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8265 | HK 2.1: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8266 | HK 2.2: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8267 | HK 2.2: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8268 | HK 3.1: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8269 | HK 3.1: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8270 | HK 3.2: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8271 | HK 3.2: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8272 | HK 4.1: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8273 | HK 4.1: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8274 | HK 4.2: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8275 | HK 4.2: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8276 | HK 5.1: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8277 | HK 5.1: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8278 | HK 5.2: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8279 | HK 5.2: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8280 | HK 6.1: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8281 | HK 6.1: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8282 | HK 6.2: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8283 | HK 6.2: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8284 | HK 7.1: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8285 | HK 7.1: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8286 | HK 7.2: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8287 | HK 7.2: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8288 | HK 8.1: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8289 | HK 8.1: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8290 | HK 8.2: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8291 | HK 8.2: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8292 | HK 9.1: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8293 | HK 9.1: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8294 | HK 9.2: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8295 | HK 9.2: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8296 | HK 10.1: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8297 | HK 10.1: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8298 | HK 10.2: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8299 | HK 10.2: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8300 | HK 11.1: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8301 | HK 11.1: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8302 | HK 11.2: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8303 | HK 11.2: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8304 | HK 12.1: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8305 | HK 12.1: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8306 | HK 12.2: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8307 | HK 12.2: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8308 | HK 13.1: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8309 | HK 13.1: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8310 | HK 13.2: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8311 | HK 13.2: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8312 | HK 14.1: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8313 | HK 14.1: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8314 | HK 14.2: Vorlauftemperatur Ist (value) | `HK.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 8315 | HK 14.2: Vorlauftemperatur Ist (status) | `HK.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 8328 | HK 1.1: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8329 | HK 1.2: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8330 | HK 2.1: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8331 | HK 2.2: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8332 | HK 3.1: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8333 | HK 3.2: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8334 | HK 4.1: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8335 | HK 4.2: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8336 | HK 5.1: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8337 | HK 5.2: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8338 | HK 6.1: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8339 | HK 6.2: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8340 | HK 7.1: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8341 | HK 7.2: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8342 | HK 8.1: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8343 | HK 8.2: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8344 | HK 9.1: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8345 | HK 9.2: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8346 | HK 10.1: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8347 | HK 10.2: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8348 | HK 11.1: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8349 | HK 11.2: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8350 | HK 12.1: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8351 | HK 12.2: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8352 | HK 13.1: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8353 | HK 13.2: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8354 | HK 14.1: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8355 | HK 14.2: Vorlauftemperatur Soll | `HK.vorlauf_temperatur_soll` | s16 | 04 | r | r |
| 8365 | HK 1.1: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8366 | HK 1.1: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8367 | HK 1.2: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8368 | HK 1.2: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8369 | HK 2.1: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8370 | HK 2.1: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8371 | HK 2.2: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8372 | HK 2.2: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8373 | HK 3.1: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8374 | HK 3.1: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8375 | HK 3.2: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8376 | HK 3.2: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8377 | HK 4.1: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8378 | HK 4.1: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8379 | HK 4.2: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8380 | HK 4.2: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8381 | HK 5.1: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8382 | HK 5.1: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8383 | HK 5.2: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8384 | HK 5.2: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8385 | HK 6.1: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8386 | HK 6.1: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8387 | HK 6.2: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8388 | HK 6.2: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8389 | HK 7.1: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8390 | HK 7.1: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8391 | HK 7.2: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8392 | HK 7.2: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8393 | HK 8.1: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8394 | HK 8.1: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8395 | HK 8.2: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8396 | HK 8.2: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8397 | HK 9.1: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8398 | HK 9.1: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8399 | HK 9.2: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8400 | HK 9.2: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8401 | HK 10.1: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8402 | HK 10.1: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8403 | HK 10.2: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8404 | HK 10.2: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8405 | HK 11.1: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8406 | HK 11.1: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8407 | HK 11.2: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8408 | HK 11.2: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8409 | HK 12.1: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8410 | HK 12.1: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8411 | HK 12.2: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8412 | HK 12.2: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8413 | HK 13.1: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8414 | HK 13.1: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8415 | HK 13.2: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8416 | HK 13.2: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8417 | HK 14.1: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8418 | HK 14.1: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8419 | HK 14.2: Raumtemperatur Ist (value) | `HK.i_raum_temperatur.value` | s16 | 04 | r | r |
| 8420 | HK 14.2: Raumtemperatur Ist (status) | `HK.i_raum_temperatur.status` | s16 | 04 | r | r |
| 8435 | HK 1.1: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8436 | HK 1.1: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8437 | HK 1.2: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8438 | HK 1.2: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8439 | HK 2.1: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8440 | HK 2.1: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8441 | HK 2.2: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8442 | HK 2.2: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8443 | HK 3.1: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8444 | HK 3.1: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8445 | HK 3.2: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8446 | HK 3.2: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8447 | HK 4.1: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8448 | HK 4.1: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8449 | HK 4.2: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8450 | HK 4.2: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8451 | HK 5.1: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8452 | HK 5.1: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8453 | HK 5.2: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8454 | HK 5.2: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8455 | HK 6.1: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8456 | HK 6.1: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8457 | HK 6.2: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8458 | HK 6.2: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8459 | HK 7.1: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8460 | HK 7.1: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8461 | HK 7.2: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8462 | HK 7.2: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8463 | HK 8.1: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8464 | HK 8.1: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8465 | HK 8.2: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8466 | HK 8.2: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8467 | HK 9.1: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8468 | HK 9.1: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8469 | HK 9.2: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8470 | HK 9.2: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8471 | HK 10.1: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8472 | HK 10.1: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8473 | HK 10.2: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8474 | HK 10.2: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8475 | HK 11.1: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8476 | HK 11.1: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8477 | HK 11.2: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8478 | HK 11.2: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8479 | HK 12.1: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8480 | HK 12.1: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8481 | HK 12.2: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8482 | HK 12.2: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8483 | HK 13.1: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8484 | HK 13.1: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8485 | HK 13.2: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8486 | HK 13.2: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8487 | HK 14.1: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8488 | HK 14.1: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8489 | HK 14.2: Außentemperatur (value) | `HK.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8490 | HK 14.2: Außentemperatur (status) | `HK.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 8503 | HK 1.1: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8504 | HK 1.2: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8505 | HK 2.1: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8506 | HK 2.2: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8507 | HK 3.1: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8508 | HK 3.2: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8509 | HK 4.1: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8510 | HK 4.2: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8511 | HK 5.1: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8512 | HK 5.2: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8513 | HK 6.1: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8514 | HK 6.2: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8515 | HK 7.1: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8516 | HK 7.2: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8517 | HK 8.1: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8518 | HK 8.2: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8519 | HK 9.1: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8520 | HK 9.2: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8521 | HK 10.1: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8522 | HK 10.2: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8523 | HK 11.1: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8524 | HK 11.2: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8525 | HK 12.1: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8526 | HK 12.2: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8527 | HK 13.1: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8528 | HK 13.2: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8529 | HK 14.1: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8530 | HK 14.2: Pumpe | `HK.o_pumpe` | s16 | 04 | r | r |
| 8538 | HK 1.1: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8539 | HK 1.2: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8540 | HK 2.1: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8541 | HK 2.2: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8542 | HK 3.1: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8543 | HK 3.2: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8544 | HK 4.1: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8545 | HK 4.2: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8546 | HK 5.1: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8547 | HK 5.2: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8548 | HK 6.1: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8549 | HK 6.2: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8550 | HK 7.1: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8551 | HK 7.2: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8552 | HK 8.1: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8553 | HK 8.2: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8554 | HK 9.1: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8555 | HK 9.2: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8556 | HK 10.1: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8557 | HK 10.2: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8558 | HK 11.1: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8559 | HK 11.2: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8560 | HK 12.1: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8561 | HK 12.2: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8562 | HK 13.1: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8563 | HK 13.2: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8564 | HK 14.1: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8565 | HK 14.2: Raumtemperatur Soll | `HK.raum_temperatur_soll` | s16 | 04 | r | r |
| 8573 | HK 1.1: Status | `HK.status` | s16 | 04 | r | r |
| 8574 | HK 1.2: Status | `HK.status` | s16 | 04 | r | r |
| 8575 | HK 2.1: Status | `HK.status` | s16 | 04 | r | r |
| 8576 | HK 2.2: Status | `HK.status` | s16 | 04 | r | r |
| 8577 | HK 3.1: Status | `HK.status` | s16 | 04 | r | r |
| 8578 | HK 3.2: Status | `HK.status` | s16 | 04 | r | r |
| 8579 | HK 4.1: Status | `HK.status` | s16 | 04 | r | r |
| 8580 | HK 4.2: Status | `HK.status` | s16 | 04 | r | r |
| 8581 | HK 5.1: Status | `HK.status` | s16 | 04 | r | r |
| 8582 | HK 5.2: Status | `HK.status` | s16 | 04 | r | r |
| 8583 | HK 6.1: Status | `HK.status` | s16 | 04 | r | r |
| 8584 | HK 6.2: Status | `HK.status` | s16 | 04 | r | r |
| 8585 | HK 7.1: Status | `HK.status` | s16 | 04 | r | r |
| 8586 | HK 7.2: Status | `HK.status` | s16 | 04 | r | r |
| 8587 | HK 8.1: Status | `HK.status` | s16 | 04 | r | r |
| 8588 | HK 8.2: Status | `HK.status` | s16 | 04 | r | r |
| 8589 | HK 9.1: Status | `HK.status` | s16 | 04 | r | r |
| 8590 | HK 9.2: Status | `HK.status` | s16 | 04 | r | r |
| 8591 | HK 10.1: Status | `HK.status` | s16 | 04 | r | r |
| 8592 | HK 10.2: Status | `HK.status` | s16 | 04 | r | r |
| 8593 | HK 11.1: Status | `HK.status` | s16 | 04 | r | r |
| 8594 | HK 11.2: Status | `HK.status` | s16 | 04 | r | r |
| 8595 | HK 12.1: Status | `HK.status` | s16 | 04 | r | r |
| 8596 | HK 12.2: Status | `HK.status` | s16 | 04 | r | r |
| 8597 | HK 13.1: Status | `HK.status` | s16 | 04 | r | r |
| 8598 | HK 13.2: Status | `HK.status` | s16 | 04 | r | r |
| 8599 | HK 14.1: Status | `HK.status` | s16 | 04 | r | r |
| 8600 | HK 14.2: Status | `HK.status` | s16 | 04 | r | r |
| 24589 | HK 1.1: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24590 | HK 1.2: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24591 | HK 2.1: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24592 | HK 2.2: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24593 | HK 3.1: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24594 | HK 3.2: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24595 | HK 4.1: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24596 | HK 4.2: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24597 | HK 5.1: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24598 | HK 5.2: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24599 | HK 6.1: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24600 | HK 6.2: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24601 | HK 7.1: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24602 | HK 7.2: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24603 | HK 8.1: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24604 | HK 8.2: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24605 | HK 9.1: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24606 | HK 9.2: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24607 | HK 10.1: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24608 | HK 10.2: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24609 | HK 11.1: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24610 | HK 11.2: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24611 | HK 12.1: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24612 | HK 12.2: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24613 | HK 13.1: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24614 | HK 13.2: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24615 | HK 14.1: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24616 | HK 14.2: Programm wählen | `HK.programm` | s16 | 03 | rw | rw |
| 24624 | HK 1.1: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24625 | HK 1.2: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24626 | HK 2.1: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24627 | HK 2.2: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24628 | HK 3.1: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24629 | HK 3.2: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24630 | HK 4.1: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24631 | HK 4.2: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24632 | HK 5.1: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24633 | HK 5.2: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24634 | HK 6.1: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24635 | HK 6.2: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24636 | HK 7.1: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24637 | HK 7.2: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24638 | HK 8.1: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24639 | HK 8.2: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24640 | HK 9.1: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24641 | HK 9.2: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24642 | HK 10.1: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24643 | HK 10.2: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24644 | HK 11.1: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24645 | HK 11.2: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24646 | HK 12.1: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24647 | HK 12.2: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24648 | HK 13.1: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24649 | HK 13.2: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24650 | HK 14.1: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24651 | HK 14.2: Komforttemperatur | `HK.raum_temperatur_soll_tag` | s16 | 03 | rw | rw |
| 24659 | HK 1.1: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24660 | HK 1.2: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24661 | HK 2.1: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24662 | HK 2.2: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24663 | HK 3.1: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24664 | HK 3.2: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24665 | HK 4.1: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24666 | HK 4.2: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24667 | HK 5.1: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24668 | HK 5.2: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24669 | HK 6.1: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24670 | HK 6.2: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24671 | HK 7.1: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24672 | HK 7.2: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24673 | HK 8.1: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24674 | HK 8.2: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24675 | HK 9.1: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24676 | HK 9.2: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24677 | HK 10.1: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24678 | HK 10.2: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24679 | HK 11.1: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24680 | HK 11.2: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24681 | HK 12.1: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24682 | HK 12.2: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24683 | HK 13.1: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24684 | HK 13.2: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24685 | HK 14.1: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24686 | HK 14.2: Absenktemperatur | `HK.raum_temperatur_soll_nacht` | s16 | 03 | rw | rw |
| 24859 | HK 1.1: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24860 | HK 1.2: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24861 | HK 2.1: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24862 | HK 2.2: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24863 | HK 3.1: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24864 | HK 3.2: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24865 | HK 4.1: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24866 | HK 4.2: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24867 | HK 5.1: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24868 | HK 5.2: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24869 | HK 6.1: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24870 | HK 6.2: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24871 | HK 7.1: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24872 | HK 7.2: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24873 | HK 8.1: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24874 | HK 8.2: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24875 | HK 9.1: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24876 | HK 9.2: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24877 | HK 10.1: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24878 | HK 10.2: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24879 | HK 11.1: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24880 | HK 11.2: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24881 | HK 12.1: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24882 | HK 12.2: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24883 | HK 13.1: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24884 | HK 13.2: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24885 | HK 14.1: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24886 | HK 14.2: Modbus Anforderung | `HK.modbus_anforderung` | s16 | 03 | r | rw |
| 24894 | HK 1.1: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24895 | HK 1.2: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24896 | HK 2.1: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24897 | HK 2.2: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24898 | HK 3.1: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24899 | HK 3.2: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24900 | HK 4.1: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24901 | HK 4.2: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24902 | HK 5.1: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24903 | HK 5.2: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24904 | HK 6.1: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24905 | HK 6.2: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24906 | HK 7.1: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24907 | HK 7.2: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24908 | HK 8.1: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24909 | HK 8.2: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24910 | HK 9.1: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24911 | HK 9.2: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24912 | HK 10.1: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24913 | HK 10.2: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24914 | HK 11.1: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24915 | HK 11.2: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24916 | HK 12.1: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24917 | HK 12.2: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24918 | HK 13.1: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24919 | HK 13.2: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24920 | HK 14.1: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24921 | HK 14.2: Modbus Vorlauftemperatur Soll | `HK.modbus_temperatur` | s16 | 03 | r | rw |
| 24936 | HK Sollvorgabe | `KSM.hk_modbus_temperatur_auswahl` | s16 | 03 | r | rw |
| 24939 | HK 1.1: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24940 | HK 1.2: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24941 | HK 2.1: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24942 | HK 2.2: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24943 | HK 3.1: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24944 | HK 3.2: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24945 | HK 4.1: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24946 | HK 4.2: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24947 | HK 5.1: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24948 | HK 5.2: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24949 | HK 6.1: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24950 | HK 6.2: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24951 | HK 7.1: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24952 | HK 7.2: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24953 | HK 8.1: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24954 | HK 8.2: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24955 | HK 9.1: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24956 | HK 9.2: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24957 | HK 10.1: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24958 | HK 10.2: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24959 | HK 11.1: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24960 | HK 11.2: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24961 | HK 12.1: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24962 | HK 12.2: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24963 | HK 13.1: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24964 | HK 13.2: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24965 | HK 14.1: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |
| 24966 | HK 14.2: Modbus Programm | `HK.modbus_programm` | s16 | 03 | r | rw |

### Pufferspeicher (`buffer_storage.json`, 345 Register)

| Adresse | Name (mit Slot) | Parameter | Typ | FC | User | Expert |
|---:|---|---|---|:---:|:---:|:---:|
| 8708 | PUF 0: Temperatur 1 (value) | `PUF.i_ist_temperatur_1.value` | s16 | 04 | r | r |
| 8709 | PUF 0: Temperatur 1 (status) | `PUF.i_ist_temperatur_1.status` | s16 | 04 | r | r |
| 8710 | PUF 1: Temperatur 1 (value) | `PUF.i_ist_temperatur_1.value` | s16 | 04 | r | r |
| 8711 | PUF 1: Temperatur 1 (status) | `PUF.i_ist_temperatur_1.status` | s16 | 04 | r | r |
| 8712 | PUF 2: Temperatur 1 (value) | `PUF.i_ist_temperatur_1.value` | s16 | 04 | r | r |
| 8713 | PUF 2: Temperatur 1 (status) | `PUF.i_ist_temperatur_1.status` | s16 | 04 | r | r |
| 8714 | PUF 3: Temperatur 1 (value) | `PUF.i_ist_temperatur_1.value` | s16 | 04 | r | r |
| 8715 | PUF 3: Temperatur 1 (status) | `PUF.i_ist_temperatur_1.status` | s16 | 04 | r | r |
| 8716 | PUF 4: Temperatur 1 (value) | `PUF.i_ist_temperatur_1.value` | s16 | 04 | r | r |
| 8717 | PUF 4: Temperatur 1 (status) | `PUF.i_ist_temperatur_1.status` | s16 | 04 | r | r |
| 8718 | PUF 5: Temperatur 1 (value) | `PUF.i_ist_temperatur_1.value` | s16 | 04 | r | r |
| 8719 | PUF 5: Temperatur 1 (status) | `PUF.i_ist_temperatur_1.status` | s16 | 04 | r | r |
| 8720 | PUF 6: Temperatur 1 (value) | `PUF.i_ist_temperatur_1.value` | s16 | 04 | r | r |
| 8721 | PUF 6: Temperatur 1 (status) | `PUF.i_ist_temperatur_1.status` | s16 | 04 | r | r |
| 8722 | PUF 7: Temperatur 1 (value) | `PUF.i_ist_temperatur_1.value` | s16 | 04 | r | r |
| 8723 | PUF 7: Temperatur 1 (status) | `PUF.i_ist_temperatur_1.status` | s16 | 04 | r | r |
| 8724 | PUF 8: Temperatur 1 (value) | `PUF.i_ist_temperatur_1.value` | s16 | 04 | r | r |
| 8725 | PUF 8: Temperatur 1 (status) | `PUF.i_ist_temperatur_1.status` | s16 | 04 | r | r |
| 8726 | PUF 9: Temperatur 1 (value) | `PUF.i_ist_temperatur_1.value` | s16 | 04 | r | r |
| 8727 | PUF 9: Temperatur 1 (status) | `PUF.i_ist_temperatur_1.status` | s16 | 04 | r | r |
| 8728 | PUF 10: Temperatur 1 (value) | `PUF.i_ist_temperatur_1.value` | s16 | 04 | r | r |
| 8729 | PUF 10: Temperatur 1 (status) | `PUF.i_ist_temperatur_1.status` | s16 | 04 | r | r |
| 8730 | PUF 11: Temperatur 1 (value) | `PUF.i_ist_temperatur_1.value` | s16 | 04 | r | r |
| 8731 | PUF 11: Temperatur 1 (status) | `PUF.i_ist_temperatur_1.status` | s16 | 04 | r | r |
| 8732 | PUF 12: Temperatur 1 (value) | `PUF.i_ist_temperatur_1.value` | s16 | 04 | r | r |
| 8733 | PUF 12: Temperatur 1 (status) | `PUF.i_ist_temperatur_1.status` | s16 | 04 | r | r |
| 8734 | PUF 13: Temperatur 1 (value) | `PUF.i_ist_temperatur_1.value` | s16 | 04 | r | r |
| 8735 | PUF 13: Temperatur 1 (status) | `PUF.i_ist_temperatur_1.status` | s16 | 04 | r | r |
| 8736 | PUF 14: Temperatur 1 (value) | `PUF.i_ist_temperatur_1.value` | s16 | 04 | r | r |
| 8737 | PUF 14: Temperatur 1 (status) | `PUF.i_ist_temperatur_1.status` | s16 | 04 | r | r |
| 8742 | PUF 0: Temperatur 2 (value) | `PUF.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 8743 | PUF 0: Temperatur 2 (status) | `PUF.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 8744 | PUF 1: Temperatur 2 (value) | `PUF.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 8745 | PUF 1: Temperatur 2 (status) | `PUF.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 8746 | PUF 2: Temperatur 2 (value) | `PUF.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 8747 | PUF 2: Temperatur 2 (status) | `PUF.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 8748 | PUF 3: Temperatur 2 (value) | `PUF.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 8749 | PUF 3: Temperatur 2 (status) | `PUF.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 8750 | PUF 4: Temperatur 2 (value) | `PUF.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 8751 | PUF 4: Temperatur 2 (status) | `PUF.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 8752 | PUF 5: Temperatur 2 (value) | `PUF.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 8753 | PUF 5: Temperatur 2 (status) | `PUF.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 8754 | PUF 6: Temperatur 2 (value) | `PUF.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 8755 | PUF 6: Temperatur 2 (status) | `PUF.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 8756 | PUF 7: Temperatur 2 (value) | `PUF.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 8757 | PUF 7: Temperatur 2 (status) | `PUF.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 8758 | PUF 8: Temperatur 2 (value) | `PUF.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 8759 | PUF 8: Temperatur 2 (status) | `PUF.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 8760 | PUF 9: Temperatur 2 (value) | `PUF.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 8761 | PUF 9: Temperatur 2 (status) | `PUF.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 8762 | PUF 10: Temperatur 2 (value) | `PUF.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 8763 | PUF 10: Temperatur 2 (status) | `PUF.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 8764 | PUF 11: Temperatur 2 (value) | `PUF.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 8765 | PUF 11: Temperatur 2 (status) | `PUF.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 8766 | PUF 12: Temperatur 2 (value) | `PUF.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 8767 | PUF 12: Temperatur 2 (status) | `PUF.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 8768 | PUF 13: Temperatur 2 (value) | `PUF.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 8769 | PUF 13: Temperatur 2 (status) | `PUF.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 8770 | PUF 14: Temperatur 2 (value) | `PUF.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 8771 | PUF 14: Temperatur 2 (status) | `PUF.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 8776 | PUF 0: Temperatur 3 (value) | `PUF.i_ist_temperatur_3.value` | s16 | 04 | r | r |
| 8777 | PUF 0: Temperatur 3 (status) | `PUF.i_ist_temperatur_3.status` | s16 | 04 | r | r |
| 8778 | PUF 1: Temperatur 3 (value) | `PUF.i_ist_temperatur_3.value` | s16 | 04 | r | r |
| 8779 | PUF 1: Temperatur 3 (status) | `PUF.i_ist_temperatur_3.status` | s16 | 04 | r | r |
| 8780 | PUF 2: Temperatur 3 (value) | `PUF.i_ist_temperatur_3.value` | s16 | 04 | r | r |
| 8781 | PUF 2: Temperatur 3 (status) | `PUF.i_ist_temperatur_3.status` | s16 | 04 | r | r |
| 8782 | PUF 3: Temperatur 3 (value) | `PUF.i_ist_temperatur_3.value` | s16 | 04 | r | r |
| 8783 | PUF 3: Temperatur 3 (status) | `PUF.i_ist_temperatur_3.status` | s16 | 04 | r | r |
| 8784 | PUF 4: Temperatur 3 (value) | `PUF.i_ist_temperatur_3.value` | s16 | 04 | r | r |
| 8785 | PUF 4: Temperatur 3 (status) | `PUF.i_ist_temperatur_3.status` | s16 | 04 | r | r |
| 8786 | PUF 5: Temperatur 3 (value) | `PUF.i_ist_temperatur_3.value` | s16 | 04 | r | r |
| 8787 | PUF 5: Temperatur 3 (status) | `PUF.i_ist_temperatur_3.status` | s16 | 04 | r | r |
| 8788 | PUF 6: Temperatur 3 (value) | `PUF.i_ist_temperatur_3.value` | s16 | 04 | r | r |
| 8789 | PUF 6: Temperatur 3 (status) | `PUF.i_ist_temperatur_3.status` | s16 | 04 | r | r |
| 8790 | PUF 7: Temperatur 3 (value) | `PUF.i_ist_temperatur_3.value` | s16 | 04 | r | r |
| 8791 | PUF 7: Temperatur 3 (status) | `PUF.i_ist_temperatur_3.status` | s16 | 04 | r | r |
| 8792 | PUF 8: Temperatur 3 (value) | `PUF.i_ist_temperatur_3.value` | s16 | 04 | r | r |
| 8793 | PUF 8: Temperatur 3 (status) | `PUF.i_ist_temperatur_3.status` | s16 | 04 | r | r |
| 8794 | PUF 9: Temperatur 3 (value) | `PUF.i_ist_temperatur_3.value` | s16 | 04 | r | r |
| 8795 | PUF 9: Temperatur 3 (status) | `PUF.i_ist_temperatur_3.status` | s16 | 04 | r | r |
| 8796 | PUF 10: Temperatur 3 (value) | `PUF.i_ist_temperatur_3.value` | s16 | 04 | r | r |
| 8797 | PUF 10: Temperatur 3 (status) | `PUF.i_ist_temperatur_3.status` | s16 | 04 | r | r |
| 8798 | PUF 11: Temperatur 3 (value) | `PUF.i_ist_temperatur_3.value` | s16 | 04 | r | r |
| 8799 | PUF 11: Temperatur 3 (status) | `PUF.i_ist_temperatur_3.status` | s16 | 04 | r | r |
| 8800 | PUF 12: Temperatur 3 (value) | `PUF.i_ist_temperatur_3.value` | s16 | 04 | r | r |
| 8801 | PUF 12: Temperatur 3 (status) | `PUF.i_ist_temperatur_3.status` | s16 | 04 | r | r |
| 8802 | PUF 13: Temperatur 3 (value) | `PUF.i_ist_temperatur_3.value` | s16 | 04 | r | r |
| 8803 | PUF 13: Temperatur 3 (status) | `PUF.i_ist_temperatur_3.status` | s16 | 04 | r | r |
| 8804 | PUF 14: Temperatur 3 (value) | `PUF.i_ist_temperatur_3.value` | s16 | 04 | r | r |
| 8805 | PUF 14: Temperatur 3 (status) | `PUF.i_ist_temperatur_3.status` | s16 | 04 | r | r |
| 8810 | PUF 0: Temperatur 4 (value) | `PUF.i_ist_temperatur_4.value` | s16 | 04 | r | r |
| 8811 | PUF 0: Temperatur 4 (status) | `PUF.i_ist_temperatur_4.status` | s16 | 04 | r | r |
| 8812 | PUF 1: Temperatur 4 (value) | `PUF.i_ist_temperatur_4.value` | s16 | 04 | r | r |
| 8813 | PUF 1: Temperatur 4 (status) | `PUF.i_ist_temperatur_4.status` | s16 | 04 | r | r |
| 8814 | PUF 2: Temperatur 4 (value) | `PUF.i_ist_temperatur_4.value` | s16 | 04 | r | r |
| 8815 | PUF 2: Temperatur 4 (status) | `PUF.i_ist_temperatur_4.status` | s16 | 04 | r | r |
| 8816 | PUF 3: Temperatur 4 (value) | `PUF.i_ist_temperatur_4.value` | s16 | 04 | r | r |
| 8817 | PUF 3: Temperatur 4 (status) | `PUF.i_ist_temperatur_4.status` | s16 | 04 | r | r |
| 8818 | PUF 4: Temperatur 4 (value) | `PUF.i_ist_temperatur_4.value` | s16 | 04 | r | r |
| 8819 | PUF 4: Temperatur 4 (status) | `PUF.i_ist_temperatur_4.status` | s16 | 04 | r | r |
| 8820 | PUF 5: Temperatur 4 (value) | `PUF.i_ist_temperatur_4.value` | s16 | 04 | r | r |
| 8821 | PUF 5: Temperatur 4 (status) | `PUF.i_ist_temperatur_4.status` | s16 | 04 | r | r |
| 8822 | PUF 6: Temperatur 4 (value) | `PUF.i_ist_temperatur_4.value` | s16 | 04 | r | r |
| 8823 | PUF 6: Temperatur 4 (status) | `PUF.i_ist_temperatur_4.status` | s16 | 04 | r | r |
| 8824 | PUF 7: Temperatur 4 (value) | `PUF.i_ist_temperatur_4.value` | s16 | 04 | r | r |
| 8825 | PUF 7: Temperatur 4 (status) | `PUF.i_ist_temperatur_4.status` | s16 | 04 | r | r |
| 8826 | PUF 8: Temperatur 4 (value) | `PUF.i_ist_temperatur_4.value` | s16 | 04 | r | r |
| 8827 | PUF 8: Temperatur 4 (status) | `PUF.i_ist_temperatur_4.status` | s16 | 04 | r | r |
| 8828 | PUF 9: Temperatur 4 (value) | `PUF.i_ist_temperatur_4.value` | s16 | 04 | r | r |
| 8829 | PUF 9: Temperatur 4 (status) | `PUF.i_ist_temperatur_4.status` | s16 | 04 | r | r |
| 8830 | PUF 10: Temperatur 4 (value) | `PUF.i_ist_temperatur_4.value` | s16 | 04 | r | r |
| 8831 | PUF 10: Temperatur 4 (status) | `PUF.i_ist_temperatur_4.status` | s16 | 04 | r | r |
| 8832 | PUF 11: Temperatur 4 (value) | `PUF.i_ist_temperatur_4.value` | s16 | 04 | r | r |
| 8833 | PUF 11: Temperatur 4 (status) | `PUF.i_ist_temperatur_4.status` | s16 | 04 | r | r |
| 8834 | PUF 12: Temperatur 4 (value) | `PUF.i_ist_temperatur_4.value` | s16 | 04 | r | r |
| 8835 | PUF 12: Temperatur 4 (status) | `PUF.i_ist_temperatur_4.status` | s16 | 04 | r | r |
| 8836 | PUF 13: Temperatur 4 (value) | `PUF.i_ist_temperatur_4.value` | s16 | 04 | r | r |
| 8837 | PUF 13: Temperatur 4 (status) | `PUF.i_ist_temperatur_4.status` | s16 | 04 | r | r |
| 8838 | PUF 14: Temperatur 4 (value) | `PUF.i_ist_temperatur_4.value` | s16 | 04 | r | r |
| 8839 | PUF 14: Temperatur 4 (status) | `PUF.i_ist_temperatur_4.status` | s16 | 04 | r | r |
| 8844 | PUF 0: Temperatur 5 (value) | `PUF.i_ist_temperatur_5.value` | s16 | 04 | r | r |
| 8845 | PUF 0: Temperatur 5 (status) | `PUF.i_ist_temperatur_5.status` | s16 | 04 | r | r |
| 8846 | PUF 1: Temperatur 5 (value) | `PUF.i_ist_temperatur_5.value` | s16 | 04 | r | r |
| 8847 | PUF 1: Temperatur 5 (status) | `PUF.i_ist_temperatur_5.status` | s16 | 04 | r | r |
| 8848 | PUF 2: Temperatur 5 (value) | `PUF.i_ist_temperatur_5.value` | s16 | 04 | r | r |
| 8849 | PUF 2: Temperatur 5 (status) | `PUF.i_ist_temperatur_5.status` | s16 | 04 | r | r |
| 8850 | PUF 3: Temperatur 5 (value) | `PUF.i_ist_temperatur_5.value` | s16 | 04 | r | r |
| 8851 | PUF 3: Temperatur 5 (status) | `PUF.i_ist_temperatur_5.status` | s16 | 04 | r | r |
| 8852 | PUF 4: Temperatur 5 (value) | `PUF.i_ist_temperatur_5.value` | s16 | 04 | r | r |
| 8853 | PUF 4: Temperatur 5 (status) | `PUF.i_ist_temperatur_5.status` | s16 | 04 | r | r |
| 8854 | PUF 5: Temperatur 5 (value) | `PUF.i_ist_temperatur_5.value` | s16 | 04 | r | r |
| 8855 | PUF 5: Temperatur 5 (status) | `PUF.i_ist_temperatur_5.status` | s16 | 04 | r | r |
| 8856 | PUF 6: Temperatur 5 (value) | `PUF.i_ist_temperatur_5.value` | s16 | 04 | r | r |
| 8857 | PUF 6: Temperatur 5 (status) | `PUF.i_ist_temperatur_5.status` | s16 | 04 | r | r |
| 8858 | PUF 7: Temperatur 5 (value) | `PUF.i_ist_temperatur_5.value` | s16 | 04 | r | r |
| 8859 | PUF 7: Temperatur 5 (status) | `PUF.i_ist_temperatur_5.status` | s16 | 04 | r | r |
| 8860 | PUF 8: Temperatur 5 (value) | `PUF.i_ist_temperatur_5.value` | s16 | 04 | r | r |
| 8861 | PUF 8: Temperatur 5 (status) | `PUF.i_ist_temperatur_5.status` | s16 | 04 | r | r |
| 8862 | PUF 9: Temperatur 5 (value) | `PUF.i_ist_temperatur_5.value` | s16 | 04 | r | r |
| 8863 | PUF 9: Temperatur 5 (status) | `PUF.i_ist_temperatur_5.status` | s16 | 04 | r | r |
| 8864 | PUF 10: Temperatur 5 (value) | `PUF.i_ist_temperatur_5.value` | s16 | 04 | r | r |
| 8865 | PUF 10: Temperatur 5 (status) | `PUF.i_ist_temperatur_5.status` | s16 | 04 | r | r |
| 8866 | PUF 11: Temperatur 5 (value) | `PUF.i_ist_temperatur_5.value` | s16 | 04 | r | r |
| 8867 | PUF 11: Temperatur 5 (status) | `PUF.i_ist_temperatur_5.status` | s16 | 04 | r | r |
| 8868 | PUF 12: Temperatur 5 (value) | `PUF.i_ist_temperatur_5.value` | s16 | 04 | r | r |
| 8869 | PUF 12: Temperatur 5 (status) | `PUF.i_ist_temperatur_5.status` | s16 | 04 | r | r |
| 8870 | PUF 13: Temperatur 5 (value) | `PUF.i_ist_temperatur_5.value` | s16 | 04 | r | r |
| 8871 | PUF 13: Temperatur 5 (status) | `PUF.i_ist_temperatur_5.status` | s16 | 04 | r | r |
| 8872 | PUF 14: Temperatur 5 (value) | `PUF.i_ist_temperatur_5.value` | s16 | 04 | r | r |
| 8873 | PUF 14: Temperatur 5 (status) | `PUF.i_ist_temperatur_5.status` | s16 | 04 | r | r |
| 8878 | PUF 0: Pumpe | `PUF.o_pumpe` | s16 | 04 | r | r |
| 8879 | PUF 1: Pumpe | `PUF.o_pumpe` | s16 | 04 | r | r |
| 8880 | PUF 2: Pumpe | `PUF.o_pumpe` | s16 | 04 | r | r |
| 8881 | PUF 3: Pumpe | `PUF.o_pumpe` | s16 | 04 | r | r |
| 8882 | PUF 4: Pumpe | `PUF.o_pumpe` | s16 | 04 | r | r |
| 8883 | PUF 5: Pumpe | `PUF.o_pumpe` | s16 | 04 | r | r |
| 8884 | PUF 6: Pumpe | `PUF.o_pumpe` | s16 | 04 | r | r |
| 8885 | PUF 7: Pumpe | `PUF.o_pumpe` | s16 | 04 | r | r |
| 8886 | PUF 8: Pumpe | `PUF.o_pumpe` | s16 | 04 | r | r |
| 8887 | PUF 9: Pumpe | `PUF.o_pumpe` | s16 | 04 | r | r |
| 8888 | PUF 10: Pumpe | `PUF.o_pumpe` | s16 | 04 | r | r |
| 8889 | PUF 11: Pumpe | `PUF.o_pumpe` | s16 | 04 | r | r |
| 8890 | PUF 12: Pumpe | `PUF.o_pumpe` | s16 | 04 | r | r |
| 8891 | PUF 13: Pumpe | `PUF.o_pumpe` | s16 | 04 | r | r |
| 8892 | PUF 14: Pumpe | `PUF.o_pumpe` | s16 | 04 | r | r |
| 8895 | PUF 0: Anforderung | `PUF.anforderung` | s16 | 04 | r | r |
| 8896 | PUF 1: Anforderung | `PUF.anforderung` | s16 | 04 | r | r |
| 8897 | PUF 2: Anforderung | `PUF.anforderung` | s16 | 04 | r | r |
| 8898 | PUF 3: Anforderung | `PUF.anforderung` | s16 | 04 | r | r |
| 8899 | PUF 4: Anforderung | `PUF.anforderung` | s16 | 04 | r | r |
| 8900 | PUF 5: Anforderung | `PUF.anforderung` | s16 | 04 | r | r |
| 8901 | PUF 6: Anforderung | `PUF.anforderung` | s16 | 04 | r | r |
| 8902 | PUF 7: Anforderung | `PUF.anforderung` | s16 | 04 | r | r |
| 8903 | PUF 8: Anforderung | `PUF.anforderung` | s16 | 04 | r | r |
| 8904 | PUF 9: Anforderung | `PUF.anforderung` | s16 | 04 | r | r |
| 8905 | PUF 10: Anforderung | `PUF.anforderung` | s16 | 04 | r | r |
| 8906 | PUF 11: Anforderung | `PUF.anforderung` | s16 | 04 | r | r |
| 8907 | PUF 12: Anforderung | `PUF.anforderung` | s16 | 04 | r | r |
| 8908 | PUF 13: Anforderung | `PUF.anforderung` | s16 | 04 | r | r |
| 8909 | PUF 14: Anforderung | `PUF.anforderung` | s16 | 04 | r | r |
| 8912 | PUF 0: Umschaltventil | `PUF.o_umschaltventil` | s16 | 04 | r | r |
| 8913 | PUF 1: Umschaltventil | `PUF.o_umschaltventil` | s16 | 04 | r | r |
| 8914 | PUF 2: Umschaltventil | `PUF.o_umschaltventil` | s16 | 04 | r | r |
| 8915 | PUF 3: Umschaltventil | `PUF.o_umschaltventil` | s16 | 04 | r | r |
| 8916 | PUF 4: Umschaltventil | `PUF.o_umschaltventil` | s16 | 04 | r | r |
| 8917 | PUF 5: Umschaltventil | `PUF.o_umschaltventil` | s16 | 04 | r | r |
| 8918 | PUF 6: Umschaltventil | `PUF.o_umschaltventil` | s16 | 04 | r | r |
| 8919 | PUF 7: Umschaltventil | `PUF.o_umschaltventil` | s16 | 04 | r | r |
| 8920 | PUF 8: Umschaltventil | `PUF.o_umschaltventil` | s16 | 04 | r | r |
| 8921 | PUF 9: Umschaltventil | `PUF.o_umschaltventil` | s16 | 04 | r | r |
| 8922 | PUF 10: Umschaltventil | `PUF.o_umschaltventil` | s16 | 04 | r | r |
| 8923 | PUF 11: Umschaltventil | `PUF.o_umschaltventil` | s16 | 04 | r | r |
| 8924 | PUF 12: Umschaltventil | `PUF.o_umschaltventil` | s16 | 04 | r | r |
| 8925 | PUF 13: Umschaltventil | `PUF.o_umschaltventil` | s16 | 04 | r | r |
| 8926 | PUF 14: Umschaltventil | `PUF.o_umschaltventil` | s16 | 04 | r | r |
| 9971 | ZUB 0: Verbraucher Soll | `GRP.verbraucher_anf_temperatur` | s16 | 04 | r | r |
| 9972 | ZUB 1: Verbraucher Soll | `GRP.verbraucher_anf_temperatur` | s16 | 04 | r | r |
| 9973 | ZUB 2: Verbraucher Soll | `GRP.verbraucher_anf_temperatur` | s16 | 04 | r | r |
| 9974 | ZUB 3: Verbraucher Soll | `GRP.verbraucher_anf_temperatur` | s16 | 04 | r | r |
| 9975 | ZUB 4: Verbraucher Soll | `GRP.verbraucher_anf_temperatur` | s16 | 04 | r | r |
| 9976 | ZUB 5: Verbraucher Soll | `GRP.verbraucher_anf_temperatur` | s16 | 04 | r | r |
| 9977 | ZUB 6: Verbraucher Soll | `GRP.verbraucher_anf_temperatur` | s16 | 04 | r | r |
| 9978 | ZUB 7: Verbraucher Soll | `GRP.verbraucher_anf_temperatur` | s16 | 04 | r | r |
| 9979 | ZUB 8: Verbraucher Soll | `GRP.verbraucher_anf_temperatur` | s16 | 04 | r | r |
| 9980 | ZUB 9: Verbraucher Soll | `GRP.verbraucher_anf_temperatur` | s16 | 04 | r | r |
| 9981 | ZUB 10: Verbraucher Soll | `GRP.verbraucher_anf_temperatur` | s16 | 04 | r | r |
| 9982 | ZUB 11: Verbraucher Soll | `GRP.verbraucher_anf_temperatur` | s16 | 04 | r | r |
| 9983 | ZUB 12: Verbraucher Soll | `GRP.verbraucher_anf_temperatur` | s16 | 04 | r | r |
| 9984 | ZUB 13: Verbraucher Soll | `GRP.verbraucher_anf_temperatur` | s16 | 04 | r | r |
| 9985 | ZUB 14: Verbraucher Soll | `GRP.verbraucher_anf_temperatur` | s16 | 04 | r | r |
| 10058 | PUF 0: Anforderung Heizstab | `PUF.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10059 | PUF 1: Anforderung Heizstab | `PUF.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10060 | PUF 2: Anforderung Heizstab | `PUF.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10061 | PUF 3: Anforderung Heizstab | `PUF.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10062 | PUF 4: Anforderung Heizstab | `PUF.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10063 | PUF 5: Anforderung Heizstab | `PUF.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10064 | PUF 6: Anforderung Heizstab | `PUF.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10065 | PUF 7: Anforderung Heizstab | `PUF.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10066 | PUF 8: Anforderung Heizstab | `PUF.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10067 | PUF 9: Anforderung Heizstab | `PUF.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10068 | PUF 10: Anforderung Heizstab | `PUF.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10069 | PUF 11: Anforderung Heizstab | `PUF.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10070 | PUF 12: Anforderung Heizstab | `PUF.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10071 | PUF 13: Anforderung Heizstab | `PUF.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10072 | PUF 14: Anforderung Heizstab | `PUF.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10075 | PUF 0: Temperatur bei Heizstab (value) | `PUF.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10076 | PUF 0: Temperatur bei Heizstab (status) | `PUF.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10077 | PUF 1: Temperatur bei Heizstab (value) | `PUF.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10078 | PUF 1: Temperatur bei Heizstab (status) | `PUF.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10079 | PUF 2: Temperatur bei Heizstab (value) | `PUF.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10080 | PUF 2: Temperatur bei Heizstab (status) | `PUF.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10081 | PUF 3: Temperatur bei Heizstab (value) | `PUF.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10082 | PUF 3: Temperatur bei Heizstab (status) | `PUF.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10083 | PUF 4: Temperatur bei Heizstab (value) | `PUF.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10084 | PUF 4: Temperatur bei Heizstab (status) | `PUF.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10085 | PUF 5: Temperatur bei Heizstab (value) | `PUF.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10086 | PUF 5: Temperatur bei Heizstab (status) | `PUF.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10087 | PUF 6: Temperatur bei Heizstab (value) | `PUF.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10088 | PUF 6: Temperatur bei Heizstab (status) | `PUF.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10089 | PUF 7: Temperatur bei Heizstab (value) | `PUF.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10090 | PUF 7: Temperatur bei Heizstab (status) | `PUF.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10091 | PUF 8: Temperatur bei Heizstab (value) | `PUF.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10092 | PUF 8: Temperatur bei Heizstab (status) | `PUF.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10093 | PUF 9: Temperatur bei Heizstab (value) | `PUF.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10094 | PUF 9: Temperatur bei Heizstab (status) | `PUF.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10095 | PUF 10: Temperatur bei Heizstab (value) | `PUF.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10096 | PUF 10: Temperatur bei Heizstab (status) | `PUF.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10097 | PUF 11: Temperatur bei Heizstab (value) | `PUF.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10098 | PUF 11: Temperatur bei Heizstab (status) | `PUF.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10099 | PUF 12: Temperatur bei Heizstab (value) | `PUF.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10100 | PUF 12: Temperatur bei Heizstab (status) | `PUF.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10101 | PUF 13: Temperatur bei Heizstab (value) | `PUF.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10102 | PUF 13: Temperatur bei Heizstab (status) | `PUF.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10103 | PUF 14: Temperatur bei Heizstab (value) | `PUF.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10104 | PUF 14: Temperatur bei Heizstab (status) | `PUF.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 24760 | PUF 0: Programm wählen | `PUF.programm` | s16 | 03 | rw | rw |
| 24761 | PUF 1: Programm wählen | `PUF.programm` | s16 | 03 | rw | rw |
| 24762 | PUF 2: Programm wählen | `PUF.programm` | s16 | 03 | rw | rw |
| 24763 | PUF 3: Programm wählen | `PUF.programm` | s16 | 03 | rw | rw |
| 24764 | PUF 4: Programm wählen | `PUF.programm` | s16 | 03 | rw | rw |
| 24765 | PUF 5: Programm wählen | `PUF.programm` | s16 | 03 | rw | rw |
| 24766 | PUF 6: Programm wählen | `PUF.programm` | s16 | 03 | rw | rw |
| 24767 | PUF 7: Programm wählen | `PUF.programm` | s16 | 03 | rw | rw |
| 24768 | PUF 8: Programm wählen | `PUF.programm` | s16 | 03 | rw | rw |
| 24769 | PUF 9: Programm wählen | `PUF.programm` | s16 | 03 | rw | rw |
| 24770 | PUF 10: Programm wählen | `PUF.programm` | s16 | 03 | rw | rw |
| 24771 | PUF 11: Programm wählen | `PUF.programm` | s16 | 03 | rw | rw |
| 24772 | PUF 12: Programm wählen | `PUF.programm` | s16 | 03 | rw | rw |
| 24773 | PUF 13: Programm wählen | `PUF.programm` | s16 | 03 | rw | rw |
| 24774 | PUF 14: Programm wählen | `PUF.programm` | s16 | 03 | rw | rw |
| 24777 | PUF 0: Temperatur Min/Max (min) | `PUF.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24778 | PUF 0: Temperatur Min/Max (max) | `PUF.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24779 | PUF 1: Temperatur Min/Max (min) | `PUF.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24780 | PUF 1: Temperatur Min/Max (max) | `PUF.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24781 | PUF 2: Temperatur Min/Max (min) | `PUF.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24782 | PUF 2: Temperatur Min/Max (max) | `PUF.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24783 | PUF 3: Temperatur Min/Max (min) | `PUF.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24784 | PUF 3: Temperatur Min/Max (max) | `PUF.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24785 | PUF 4: Temperatur Min/Max (min) | `PUF.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24786 | PUF 4: Temperatur Min/Max (max) | `PUF.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24787 | PUF 5: Temperatur Min/Max (min) | `PUF.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24788 | PUF 5: Temperatur Min/Max (max) | `PUF.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24789 | PUF 6: Temperatur Min/Max (min) | `PUF.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24790 | PUF 6: Temperatur Min/Max (max) | `PUF.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24791 | PUF 7: Temperatur Min/Max (min) | `PUF.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24792 | PUF 7: Temperatur Min/Max (max) | `PUF.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24793 | PUF 8: Temperatur Min/Max (min) | `PUF.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24794 | PUF 8: Temperatur Min/Max (max) | `PUF.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24795 | PUF 9: Temperatur Min/Max (min) | `PUF.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24796 | PUF 9: Temperatur Min/Max (max) | `PUF.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24797 | PUF 10: Temperatur Min/Max (min) | `PUF.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24798 | PUF 10: Temperatur Min/Max (max) | `PUF.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24799 | PUF 11: Temperatur Min/Max (min) | `PUF.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24800 | PUF 11: Temperatur Min/Max (max) | `PUF.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24801 | PUF 12: Temperatur Min/Max (min) | `PUF.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24802 | PUF 12: Temperatur Min/Max (max) | `PUF.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24803 | PUF 13: Temperatur Min/Max (min) | `PUF.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24804 | PUF 13: Temperatur Min/Max (max) | `PUF.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24805 | PUF 14: Temperatur Min/Max (min) | `PUF.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24806 | PUF 14: Temperatur Min/Max (max) | `PUF.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24811 | PUF 0: Brauchwassertemp. min. | `PUF.brauchwassertemp_min` | s16 | 03 | rw | rw |
| 24812 | PUF 1: Brauchwassertemp. min. | `PUF.brauchwassertemp_min` | s16 | 03 | rw | rw |
| 24813 | PUF 2: Brauchwassertemp. min. | `PUF.brauchwassertemp_min` | s16 | 03 | rw | rw |
| 24814 | PUF 3: Brauchwassertemp. min. | `PUF.brauchwassertemp_min` | s16 | 03 | rw | rw |
| 24815 | PUF 4: Brauchwassertemp. min. | `PUF.brauchwassertemp_min` | s16 | 03 | rw | rw |
| 24816 | PUF 5: Brauchwassertemp. min. | `PUF.brauchwassertemp_min` | s16 | 03 | rw | rw |
| 24817 | PUF 6: Brauchwassertemp. min. | `PUF.brauchwassertemp_min` | s16 | 03 | rw | rw |
| 24818 | PUF 7: Brauchwassertemp. min. | `PUF.brauchwassertemp_min` | s16 | 03 | rw | rw |
| 24819 | PUF 8: Brauchwassertemp. min. | `PUF.brauchwassertemp_min` | s16 | 03 | rw | rw |
| 24820 | PUF 9: Brauchwassertemp. min. | `PUF.brauchwassertemp_min` | s16 | 03 | rw | rw |
| 24821 | PUF 10: Brauchwassertemp. min. | `PUF.brauchwassertemp_min` | s16 | 03 | rw | rw |
| 24822 | PUF 11: Brauchwassertemp. min. | `PUF.brauchwassertemp_min` | s16 | 03 | rw | rw |
| 24823 | PUF 12: Brauchwassertemp. min. | `PUF.brauchwassertemp_min` | s16 | 03 | rw | rw |
| 24824 | PUF 13: Brauchwassertemp. min. | `PUF.brauchwassertemp_min` | s16 | 03 | rw | rw |
| 24825 | PUF 14: Brauchwassertemp. min. | `PUF.brauchwassertemp_min` | s16 | 03 | rw | rw |
| 25057 | PUF 0: Max. Temperatur Heizstab | `PUF.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25058 | PUF 1: Max. Temperatur Heizstab | `PUF.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25059 | PUF 2: Max. Temperatur Heizstab | `PUF.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25060 | PUF 3: Max. Temperatur Heizstab | `PUF.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25061 | PUF 4: Max. Temperatur Heizstab | `PUF.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25062 | PUF 5: Max. Temperatur Heizstab | `PUF.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25063 | PUF 6: Max. Temperatur Heizstab | `PUF.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25064 | PUF 7: Max. Temperatur Heizstab | `PUF.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25065 | PUF 8: Max. Temperatur Heizstab | `PUF.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25066 | PUF 9: Max. Temperatur Heizstab | `PUF.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25067 | PUF 10: Max. Temperatur Heizstab | `PUF.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25068 | PUF 11: Max. Temperatur Heizstab | `PUF.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25069 | PUF 12: Max. Temperatur Heizstab | `PUF.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25070 | PUF 13: Max. Temperatur Heizstab | `PUF.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25071 | PUF 14: Max. Temperatur Heizstab | `PUF.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25074 | PUF 0: Modbus Anforderung Heizstab | `PUF.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25075 | PUF 1: Modbus Anforderung Heizstab | `PUF.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25076 | PUF 2: Modbus Anforderung Heizstab | `PUF.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25077 | PUF 3: Modbus Anforderung Heizstab | `PUF.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25078 | PUF 4: Modbus Anforderung Heizstab | `PUF.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25079 | PUF 5: Modbus Anforderung Heizstab | `PUF.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25080 | PUF 6: Modbus Anforderung Heizstab | `PUF.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25081 | PUF 7: Modbus Anforderung Heizstab | `PUF.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25082 | PUF 8: Modbus Anforderung Heizstab | `PUF.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25083 | PUF 9: Modbus Anforderung Heizstab | `PUF.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25084 | PUF 10: Modbus Anforderung Heizstab | `PUF.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25085 | PUF 11: Modbus Anforderung Heizstab | `PUF.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25086 | PUF 12: Modbus Anforderung Heizstab | `PUF.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25087 | PUF 13: Modbus Anforderung Heizstab | `PUF.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25088 | PUF 14: Modbus Anforderung Heizstab | `PUF.heizstab_modbus_anforderung` | s16 | 03 | r | rw |

### Brauchwasserspeicher (`dhw_storage.json`, 336 Register)

| Adresse | Name (mit Slot) | Parameter | Typ | FC | User | Expert |
|---:|---|---|---|:---:|:---:|:---:|
| 8608 | BWS 1: Temperatur Ist (value) | `BOI.i_ist_temperatur.value` | s16 | 04 | r | r |
| 8609 | BWS 1: Temperatur Ist (status) | `BOI.i_ist_temperatur.status` | s16 | 04 | r | r |
| 8610 | BWS 2: Temperatur Ist (value) | `BOI.i_ist_temperatur.value` | s16 | 04 | r | r |
| 8611 | BWS 2: Temperatur Ist (status) | `BOI.i_ist_temperatur.status` | s16 | 04 | r | r |
| 8612 | BWS 3: Temperatur Ist (value) | `BOI.i_ist_temperatur.value` | s16 | 04 | r | r |
| 8613 | BWS 3: Temperatur Ist (status) | `BOI.i_ist_temperatur.status` | s16 | 04 | r | r |
| 8614 | BWS 4: Temperatur Ist (value) | `BOI.i_ist_temperatur.value` | s16 | 04 | r | r |
| 8615 | BWS 4: Temperatur Ist (status) | `BOI.i_ist_temperatur.status` | s16 | 04 | r | r |
| 8616 | BWS 5: Temperatur Ist (value) | `BOI.i_ist_temperatur.value` | s16 | 04 | r | r |
| 8617 | BWS 5: Temperatur Ist (status) | `BOI.i_ist_temperatur.status` | s16 | 04 | r | r |
| 8618 | BWS 6: Temperatur Ist (value) | `BOI.i_ist_temperatur.value` | s16 | 04 | r | r |
| 8619 | BWS 6: Temperatur Ist (status) | `BOI.i_ist_temperatur.status` | s16 | 04 | r | r |
| 8620 | BWS 7: Temperatur Ist (value) | `BOI.i_ist_temperatur.value` | s16 | 04 | r | r |
| 8621 | BWS 7: Temperatur Ist (status) | `BOI.i_ist_temperatur.status` | s16 | 04 | r | r |
| 8622 | BWS 8: Temperatur Ist (value) | `BOI.i_ist_temperatur.value` | s16 | 04 | r | r |
| 8623 | BWS 8: Temperatur Ist (status) | `BOI.i_ist_temperatur.status` | s16 | 04 | r | r |
| 8624 | BWS 9: Temperatur Ist (value) | `BOI.i_ist_temperatur.value` | s16 | 04 | r | r |
| 8625 | BWS 9: Temperatur Ist (status) | `BOI.i_ist_temperatur.status` | s16 | 04 | r | r |
| 8626 | BWS 10: Temperatur Ist (value) | `BOI.i_ist_temperatur.value` | s16 | 04 | r | r |
| 8627 | BWS 10: Temperatur Ist (status) | `BOI.i_ist_temperatur.status` | s16 | 04 | r | r |
| 8628 | BWS 11: Temperatur Ist (value) | `BOI.i_ist_temperatur.value` | s16 | 04 | r | r |
| 8629 | BWS 11: Temperatur Ist (status) | `BOI.i_ist_temperatur.status` | s16 | 04 | r | r |
| 8630 | BWS 12: Temperatur Ist (value) | `BOI.i_ist_temperatur.value` | s16 | 04 | r | r |
| 8631 | BWS 12: Temperatur Ist (status) | `BOI.i_ist_temperatur.status` | s16 | 04 | r | r |
| 8632 | BWS 13: Temperatur Ist (value) | `BOI.i_ist_temperatur.value` | s16 | 04 | r | r |
| 8633 | BWS 13: Temperatur Ist (status) | `BOI.i_ist_temperatur.status` | s16 | 04 | r | r |
| 8634 | BWS 14: Temperatur Ist (value) | `BOI.i_ist_temperatur.value` | s16 | 04 | r | r |
| 8635 | BWS 14: Temperatur Ist (status) | `BOI.i_ist_temperatur.status` | s16 | 04 | r | r |
| 8641 | BWS 1: Ladepumpe | `BOI.o_pumpe` | s16 | 04 | r | r |
| 8642 | BWS 2: Ladepumpe | `BOI.o_pumpe` | s16 | 04 | r | r |
| 8643 | BWS 3: Ladepumpe | `BOI.o_pumpe` | s16 | 04 | r | r |
| 8644 | BWS 4: Ladepumpe | `BOI.o_pumpe` | s16 | 04 | r | r |
| 8645 | BWS 5: Ladepumpe | `BOI.o_pumpe` | s16 | 04 | r | r |
| 8646 | BWS 6: Ladepumpe | `BOI.o_pumpe` | s16 | 04 | r | r |
| 8647 | BWS 7: Ladepumpe | `BOI.o_pumpe` | s16 | 04 | r | r |
| 8648 | BWS 8: Ladepumpe | `BOI.o_pumpe` | s16 | 04 | r | r |
| 8649 | BWS 9: Ladepumpe | `BOI.o_pumpe` | s16 | 04 | r | r |
| 8650 | BWS 10: Ladepumpe | `BOI.o_pumpe` | s16 | 04 | r | r |
| 8651 | BWS 11: Ladepumpe | `BOI.o_pumpe` | s16 | 04 | r | r |
| 8652 | BWS 12: Ladepumpe | `BOI.o_pumpe` | s16 | 04 | r | r |
| 8653 | BWS 13: Ladepumpe | `BOI.o_pumpe` | s16 | 04 | r | r |
| 8654 | BWS 14: Ladepumpe | `BOI.o_pumpe` | s16 | 04 | r | r |
| 8658 | BWS 1: Anforderung | `BOI.anforderung` | s16 | 04 | r | r |
| 8659 | BWS 2: Anforderung | `BOI.anforderung` | s16 | 04 | r | r |
| 8660 | BWS 3: Anforderung | `BOI.anforderung` | s16 | 04 | r | r |
| 8661 | BWS 4: Anforderung | `BOI.anforderung` | s16 | 04 | r | r |
| 8662 | BWS 5: Anforderung | `BOI.anforderung` | s16 | 04 | r | r |
| 8663 | BWS 6: Anforderung | `BOI.anforderung` | s16 | 04 | r | r |
| 8664 | BWS 7: Anforderung | `BOI.anforderung` | s16 | 04 | r | r |
| 8665 | BWS 8: Anforderung | `BOI.anforderung` | s16 | 04 | r | r |
| 8666 | BWS 9: Anforderung | `BOI.anforderung` | s16 | 04 | r | r |
| 8667 | BWS 10: Anforderung | `BOI.anforderung` | s16 | 04 | r | r |
| 8668 | BWS 11: Anforderung | `BOI.anforderung` | s16 | 04 | r | r |
| 8669 | BWS 12: Anforderung | `BOI.anforderung` | s16 | 04 | r | r |
| 8670 | BWS 13: Anforderung | `BOI.anforderung` | s16 | 04 | r | r |
| 8671 | BWS 14: Anforderung | `BOI.anforderung` | s16 | 04 | r | r |
| 8675 | BWS 1: Temperatur Soll | `BOI.soll_temperatur` | s16 | 04 | r | r |
| 8676 | BWS 2: Temperatur Soll | `BOI.soll_temperatur` | s16 | 04 | r | r |
| 8677 | BWS 3: Temperatur Soll | `BOI.soll_temperatur` | s16 | 04 | r | r |
| 8678 | BWS 4: Temperatur Soll | `BOI.soll_temperatur` | s16 | 04 | r | r |
| 8679 | BWS 5: Temperatur Soll | `BOI.soll_temperatur` | s16 | 04 | r | r |
| 8680 | BWS 6: Temperatur Soll | `BOI.soll_temperatur` | s16 | 04 | r | r |
| 8681 | BWS 7: Temperatur Soll | `BOI.soll_temperatur` | s16 | 04 | r | r |
| 8682 | BWS 8: Temperatur Soll | `BOI.soll_temperatur` | s16 | 04 | r | r |
| 8683 | BWS 9: Temperatur Soll | `BOI.soll_temperatur` | s16 | 04 | r | r |
| 8684 | BWS 10: Temperatur Soll | `BOI.soll_temperatur` | s16 | 04 | r | r |
| 8685 | BWS 11: Temperatur Soll | `BOI.soll_temperatur` | s16 | 04 | r | r |
| 8686 | BWS 12: Temperatur Soll | `BOI.soll_temperatur` | s16 | 04 | r | r |
| 8687 | BWS 13: Temperatur Soll | `BOI.soll_temperatur` | s16 | 04 | r | r |
| 8688 | BWS 14: Temperatur Soll | `BOI.soll_temperatur` | s16 | 04 | r | r |
| 8692 | BWS 1: Status | `BOI.status` | s16 | 04 | r | r |
| 8693 | BWS 2: Status | `BOI.status` | s16 | 04 | r | r |
| 8694 | BWS 3: Status | `BOI.status` | s16 | 04 | r | r |
| 8695 | BWS 4: Status | `BOI.status` | s16 | 04 | r | r |
| 8696 | BWS 5: Status | `BOI.status` | s16 | 04 | r | r |
| 8697 | BWS 6: Status | `BOI.status` | s16 | 04 | r | r |
| 8698 | BWS 7: Status | `BOI.status` | s16 | 04 | r | r |
| 8699 | BWS 8: Status | `BOI.status` | s16 | 04 | r | r |
| 8700 | BWS 9: Status | `BOI.status` | s16 | 04 | r | r |
| 8701 | BWS 10: Status | `BOI.status` | s16 | 04 | r | r |
| 8702 | BWS 11: Status | `BOI.status` | s16 | 04 | r | r |
| 8703 | BWS 12: Status | `BOI.status` | s16 | 04 | r | r |
| 8704 | BWS 13: Status | `BOI.status` | s16 | 04 | r | r |
| 8705 | BWS 14: Status | `BOI.status` | s16 | 04 | r | r |
| 9433 | BWS 1: Temperatur 2 (value) | `BOI.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 9434 | BWS 1: Temperatur 2 (status) | `BOI.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 9435 | BWS 2: Temperatur 2 (value) | `BOI.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 9436 | BWS 2: Temperatur 2 (status) | `BOI.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 9437 | BWS 3: Temperatur 2 (value) | `BOI.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 9438 | BWS 3: Temperatur 2 (status) | `BOI.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 9439 | BWS 4: Temperatur 2 (value) | `BOI.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 9440 | BWS 4: Temperatur 2 (status) | `BOI.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 9441 | BWS 5: Temperatur 2 (value) | `BOI.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 9442 | BWS 5: Temperatur 2 (status) | `BOI.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 9443 | BWS 6: Temperatur 2 (value) | `BOI.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 9444 | BWS 6: Temperatur 2 (status) | `BOI.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 9445 | BWS 7: Temperatur 2 (value) | `BOI.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 9446 | BWS 7: Temperatur 2 (status) | `BOI.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 9447 | BWS 8: Temperatur 2 (value) | `BOI.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 9448 | BWS 8: Temperatur 2 (status) | `BOI.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 9449 | BWS 9: Temperatur 2 (value) | `BOI.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 9450 | BWS 9: Temperatur 2 (status) | `BOI.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 9451 | BWS 10: Temperatur 2 (value) | `BOI.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 9452 | BWS 10: Temperatur 2 (status) | `BOI.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 9453 | BWS 11: Temperatur 2 (value) | `BOI.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 9454 | BWS 11: Temperatur 2 (status) | `BOI.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 9455 | BWS 12: Temperatur 2 (value) | `BOI.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 9456 | BWS 12: Temperatur 2 (status) | `BOI.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 9457 | BWS 13: Temperatur 2 (value) | `BOI.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 9458 | BWS 13: Temperatur 2 (status) | `BOI.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 9459 | BWS 14: Temperatur 2 (value) | `BOI.i_ist_temperatur_2.value` | s16 | 04 | r | r |
| 9460 | BWS 14: Temperatur 2 (status) | `BOI.i_ist_temperatur_2.status` | s16 | 04 | r | r |
| 10110 | BWS 1: Anforderung Heizstab | `BOI.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10111 | BWS 2: Anforderung Heizstab | `BOI.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10112 | BWS 3: Anforderung Heizstab | `BOI.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10113 | BWS 4: Anforderung Heizstab | `BOI.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10114 | BWS 5: Anforderung Heizstab | `BOI.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10115 | BWS 6: Anforderung Heizstab | `BOI.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10116 | BWS 7: Anforderung Heizstab | `BOI.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10117 | BWS 8: Anforderung Heizstab | `BOI.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10118 | BWS 9: Anforderung Heizstab | `BOI.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10119 | BWS 10: Anforderung Heizstab | `BOI.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10120 | BWS 11: Anforderung Heizstab | `BOI.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10121 | BWS 12: Anforderung Heizstab | `BOI.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10122 | BWS 13: Anforderung Heizstab | `BOI.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10123 | BWS 14: Anforderung Heizstab | `BOI.o_heizstab_anforderung` | s16 | 04 | r | r |
| 10128 | BWS 1: Temperatur bei Heizstab (value) | `BOI.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10129 | BWS 1: Temperatur bei Heizstab (status) | `BOI.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10130 | BWS 2: Temperatur bei Heizstab (value) | `BOI.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10131 | BWS 2: Temperatur bei Heizstab (status) | `BOI.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10132 | BWS 3: Temperatur bei Heizstab (value) | `BOI.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10133 | BWS 3: Temperatur bei Heizstab (status) | `BOI.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10134 | BWS 4: Temperatur bei Heizstab (value) | `BOI.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10135 | BWS 4: Temperatur bei Heizstab (status) | `BOI.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10136 | BWS 5: Temperatur bei Heizstab (value) | `BOI.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10137 | BWS 5: Temperatur bei Heizstab (status) | `BOI.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10138 | BWS 6: Temperatur bei Heizstab (value) | `BOI.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10139 | BWS 6: Temperatur bei Heizstab (status) | `BOI.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10140 | BWS 7: Temperatur bei Heizstab (value) | `BOI.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10141 | BWS 7: Temperatur bei Heizstab (status) | `BOI.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10142 | BWS 8: Temperatur bei Heizstab (value) | `BOI.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10143 | BWS 8: Temperatur bei Heizstab (status) | `BOI.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10144 | BWS 9: Temperatur bei Heizstab (value) | `BOI.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10145 | BWS 9: Temperatur bei Heizstab (status) | `BOI.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10146 | BWS 10: Temperatur bei Heizstab (value) | `BOI.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10147 | BWS 10: Temperatur bei Heizstab (status) | `BOI.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10148 | BWS 11: Temperatur bei Heizstab (value) | `BOI.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10149 | BWS 11: Temperatur bei Heizstab (status) | `BOI.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10150 | BWS 12: Temperatur bei Heizstab (value) | `BOI.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10151 | BWS 12: Temperatur bei Heizstab (status) | `BOI.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10152 | BWS 13: Temperatur bei Heizstab (value) | `BOI.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10153 | BWS 13: Temperatur bei Heizstab (status) | `BOI.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10154 | BWS 14: Temperatur bei Heizstab (value) | `BOI.i_temp_heizstab_bei_sensorwahl.value` | s16 | 04 | r | r |
| 10155 | BWS 14: Temperatur bei Heizstab (status) | `BOI.i_temp_heizstab_bei_sensorwahl.status` | s16 | 04 | r | r |
| 10161 | BWS 1: Anforderung Wärmepumpe | `BOI.o_waermepumpe_anforderung` | s16 | 04 | r | r |
| 10162 | BWS 2: Anforderung Wärmepumpe | `BOI.o_waermepumpe_anforderung` | s16 | 04 | r | r |
| 10163 | BWS 3: Anforderung Wärmepumpe | `BOI.o_waermepumpe_anforderung` | s16 | 04 | r | r |
| 10164 | BWS 4: Anforderung Wärmepumpe | `BOI.o_waermepumpe_anforderung` | s16 | 04 | r | r |
| 10165 | BWS 5: Anforderung Wärmepumpe | `BOI.o_waermepumpe_anforderung` | s16 | 04 | r | r |
| 10166 | BWS 6: Anforderung Wärmepumpe | `BOI.o_waermepumpe_anforderung` | s16 | 04 | r | r |
| 10167 | BWS 7: Anforderung Wärmepumpe | `BOI.o_waermepumpe_anforderung` | s16 | 04 | r | r |
| 10168 | BWS 8: Anforderung Wärmepumpe | `BOI.o_waermepumpe_anforderung` | s16 | 04 | r | r |
| 10169 | BWS 9: Anforderung Wärmepumpe | `BOI.o_waermepumpe_anforderung` | s16 | 04 | r | r |
| 10170 | BWS 10: Anforderung Wärmepumpe | `BOI.o_waermepumpe_anforderung` | s16 | 04 | r | r |
| 10171 | BWS 11: Anforderung Wärmepumpe | `BOI.o_waermepumpe_anforderung` | s16 | 04 | r | r |
| 10172 | BWS 12: Anforderung Wärmepumpe | `BOI.o_waermepumpe_anforderung` | s16 | 04 | r | r |
| 10173 | BWS 13: Anforderung Wärmepumpe | `BOI.o_waermepumpe_anforderung` | s16 | 04 | r | r |
| 10174 | BWS 14: Anforderung Wärmepumpe | `BOI.o_waermepumpe_anforderung` | s16 | 04 | r | r |
| 10179 | BWS 1: Speichertemp. Wärmepumpe (value) | `BOI.i_temp_waermepumpe_bei_senswahl.value` | s16 | 04 | r | r |
| 10180 | BWS 1: Speichertemp. Wärmepumpe (status) | `BOI.i_temp_waermepumpe_bei_senswahl.status` | s16 | 04 | r | r |
| 10181 | BWS 2: Speichertemp. Wärmepumpe (value) | `BOI.i_temp_waermepumpe_bei_senswahl.value` | s16 | 04 | r | r |
| 10182 | BWS 2: Speichertemp. Wärmepumpe (status) | `BOI.i_temp_waermepumpe_bei_senswahl.status` | s16 | 04 | r | r |
| 10183 | BWS 3: Speichertemp. Wärmepumpe (value) | `BOI.i_temp_waermepumpe_bei_senswahl.value` | s16 | 04 | r | r |
| 10184 | BWS 3: Speichertemp. Wärmepumpe (status) | `BOI.i_temp_waermepumpe_bei_senswahl.status` | s16 | 04 | r | r |
| 10185 | BWS 4: Speichertemp. Wärmepumpe (value) | `BOI.i_temp_waermepumpe_bei_senswahl.value` | s16 | 04 | r | r |
| 10186 | BWS 4: Speichertemp. Wärmepumpe (status) | `BOI.i_temp_waermepumpe_bei_senswahl.status` | s16 | 04 | r | r |
| 10187 | BWS 5: Speichertemp. Wärmepumpe (value) | `BOI.i_temp_waermepumpe_bei_senswahl.value` | s16 | 04 | r | r |
| 10188 | BWS 5: Speichertemp. Wärmepumpe (status) | `BOI.i_temp_waermepumpe_bei_senswahl.status` | s16 | 04 | r | r |
| 10189 | BWS 6: Speichertemp. Wärmepumpe (value) | `BOI.i_temp_waermepumpe_bei_senswahl.value` | s16 | 04 | r | r |
| 10190 | BWS 6: Speichertemp. Wärmepumpe (status) | `BOI.i_temp_waermepumpe_bei_senswahl.status` | s16 | 04 | r | r |
| 10191 | BWS 7: Speichertemp. Wärmepumpe (value) | `BOI.i_temp_waermepumpe_bei_senswahl.value` | s16 | 04 | r | r |
| 10192 | BWS 7: Speichertemp. Wärmepumpe (status) | `BOI.i_temp_waermepumpe_bei_senswahl.status` | s16 | 04 | r | r |
| 10193 | BWS 8: Speichertemp. Wärmepumpe (value) | `BOI.i_temp_waermepumpe_bei_senswahl.value` | s16 | 04 | r | r |
| 10194 | BWS 8: Speichertemp. Wärmepumpe (status) | `BOI.i_temp_waermepumpe_bei_senswahl.status` | s16 | 04 | r | r |
| 10195 | BWS 9: Speichertemp. Wärmepumpe (value) | `BOI.i_temp_waermepumpe_bei_senswahl.value` | s16 | 04 | r | r |
| 10196 | BWS 9: Speichertemp. Wärmepumpe (status) | `BOI.i_temp_waermepumpe_bei_senswahl.status` | s16 | 04 | r | r |
| 10197 | BWS 10: Speichertemp. Wärmepumpe (value) | `BOI.i_temp_waermepumpe_bei_senswahl.value` | s16 | 04 | r | r |
| 10198 | BWS 10: Speichertemp. Wärmepumpe (status) | `BOI.i_temp_waermepumpe_bei_senswahl.status` | s16 | 04 | r | r |
| 10199 | BWS 11: Speichertemp. Wärmepumpe (value) | `BOI.i_temp_waermepumpe_bei_senswahl.value` | s16 | 04 | r | r |
| 10200 | BWS 11: Speichertemp. Wärmepumpe (status) | `BOI.i_temp_waermepumpe_bei_senswahl.status` | s16 | 04 | r | r |
| 10201 | BWS 12: Speichertemp. Wärmepumpe (value) | `BOI.i_temp_waermepumpe_bei_senswahl.value` | s16 | 04 | r | r |
| 10202 | BWS 12: Speichertemp. Wärmepumpe (status) | `BOI.i_temp_waermepumpe_bei_senswahl.status` | s16 | 04 | r | r |
| 10203 | BWS 13: Speichertemp. Wärmepumpe (value) | `BOI.i_temp_waermepumpe_bei_senswahl.value` | s16 | 04 | r | r |
| 10204 | BWS 13: Speichertemp. Wärmepumpe (status) | `BOI.i_temp_waermepumpe_bei_senswahl.status` | s16 | 04 | r | r |
| 10205 | BWS 14: Speichertemp. Wärmepumpe (value) | `BOI.i_temp_waermepumpe_bei_senswahl.value` | s16 | 04 | r | r |
| 10206 | BWS 14: Speichertemp. Wärmepumpe (status) | `BOI.i_temp_waermepumpe_bei_senswahl.status` | s16 | 04 | r | r |
| 10212 | BWS 1: Status Wärmepumpe | `BOI.waermepumpe_status` | s16 | 04 | r | r |
| 10213 | BWS 2: Status Wärmepumpe | `BOI.waermepumpe_status` | s16 | 04 | r | r |
| 10214 | BWS 3: Status Wärmepumpe | `BOI.waermepumpe_status` | s16 | 04 | r | r |
| 10215 | BWS 4: Status Wärmepumpe | `BOI.waermepumpe_status` | s16 | 04 | r | r |
| 10216 | BWS 5: Status Wärmepumpe | `BOI.waermepumpe_status` | s16 | 04 | r | r |
| 10217 | BWS 6: Status Wärmepumpe | `BOI.waermepumpe_status` | s16 | 04 | r | r |
| 10218 | BWS 7: Status Wärmepumpe | `BOI.waermepumpe_status` | s16 | 04 | r | r |
| 10219 | BWS 8: Status Wärmepumpe | `BOI.waermepumpe_status` | s16 | 04 | r | r |
| 10220 | BWS 9: Status Wärmepumpe | `BOI.waermepumpe_status` | s16 | 04 | r | r |
| 10221 | BWS 10: Status Wärmepumpe | `BOI.waermepumpe_status` | s16 | 04 | r | r |
| 10222 | BWS 11: Status Wärmepumpe | `BOI.waermepumpe_status` | s16 | 04 | r | r |
| 10223 | BWS 12: Status Wärmepumpe | `BOI.waermepumpe_status` | s16 | 04 | r | r |
| 10224 | BWS 13: Status Wärmepumpe | `BOI.waermepumpe_status` | s16 | 04 | r | r |
| 10225 | BWS 14: Status Wärmepumpe | `BOI.waermepumpe_status` | s16 | 04 | r | r |
| 24693 | BWS 1: Programm wählen | `BOI.programm` | s16 | 03 | rw | rw |
| 24694 | BWS 2: Programm wählen | `BOI.programm` | s16 | 03 | rw | rw |
| 24695 | BWS 3: Programm wählen | `BOI.programm` | s16 | 03 | rw | rw |
| 24696 | BWS 4: Programm wählen | `BOI.programm` | s16 | 03 | rw | rw |
| 24697 | BWS 5: Programm wählen | `BOI.programm` | s16 | 03 | rw | rw |
| 24698 | BWS 6: Programm wählen | `BOI.programm` | s16 | 03 | rw | rw |
| 24699 | BWS 7: Programm wählen | `BOI.programm` | s16 | 03 | rw | rw |
| 24700 | BWS 8: Programm wählen | `BOI.programm` | s16 | 03 | rw | rw |
| 24701 | BWS 9: Programm wählen | `BOI.programm` | s16 | 03 | rw | rw |
| 24702 | BWS 10: Programm wählen | `BOI.programm` | s16 | 03 | rw | rw |
| 24703 | BWS 11: Programm wählen | `BOI.programm` | s16 | 03 | rw | rw |
| 24704 | BWS 12: Programm wählen | `BOI.programm` | s16 | 03 | rw | rw |
| 24705 | BWS 13: Programm wählen | `BOI.programm` | s16 | 03 | rw | rw |
| 24706 | BWS 14: Programm wählen | `BOI.programm` | s16 | 03 | rw | rw |
| 24711 | BWS 1: Temperatur Min/Max (min) | `BOI.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24712 | BWS 1: Temperatur Min/Max (max) | `BOI.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24713 | BWS 2: Temperatur Min/Max (min) | `BOI.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24714 | BWS 2: Temperatur Min/Max (max) | `BOI.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24715 | BWS 3: Temperatur Min/Max (min) | `BOI.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24716 | BWS 3: Temperatur Min/Max (max) | `BOI.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24717 | BWS 4: Temperatur Min/Max (min) | `BOI.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24718 | BWS 4: Temperatur Min/Max (max) | `BOI.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24719 | BWS 5: Temperatur Min/Max (min) | `BOI.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24720 | BWS 5: Temperatur Min/Max (max) | `BOI.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24721 | BWS 6: Temperatur Min/Max (min) | `BOI.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24722 | BWS 6: Temperatur Min/Max (max) | `BOI.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24723 | BWS 7: Temperatur Min/Max (min) | `BOI.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24724 | BWS 7: Temperatur Min/Max (max) | `BOI.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24725 | BWS 8: Temperatur Min/Max (min) | `BOI.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24726 | BWS 8: Temperatur Min/Max (max) | `BOI.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24727 | BWS 9: Temperatur Min/Max (min) | `BOI.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24728 | BWS 9: Temperatur Min/Max (max) | `BOI.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24729 | BWS 10: Temperatur Min/Max (min) | `BOI.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24730 | BWS 10: Temperatur Min/Max (max) | `BOI.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24731 | BWS 11: Temperatur Min/Max (min) | `BOI.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24732 | BWS 11: Temperatur Min/Max (max) | `BOI.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24733 | BWS 12: Temperatur Min/Max (min) | `BOI.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24734 | BWS 12: Temperatur Min/Max (max) | `BOI.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24735 | BWS 13: Temperatur Min/Max (min) | `BOI.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24736 | BWS 13: Temperatur Min/Max (max) | `BOI.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24737 | BWS 14: Temperatur Min/Max (min) | `BOI.temperatur_grenzen.min` | s16 | 03 | rw | rw |
| 24738 | BWS 14: Temperatur Min/Max (max) | `BOI.temperatur_grenzen.max` | s16 | 03 | rw | rw |
| 24744 | BWS 1: Brauchwasser 1x erhitzen | `BOI.schnellladung` | s16 | 03 | rw | rw |
| 24745 | BWS 2: Brauchwasser 1x erhitzen | `BOI.schnellladung` | s16 | 03 | rw | rw |
| 24746 | BWS 3: Brauchwasser 1x erhitzen | `BOI.schnellladung` | s16 | 03 | rw | rw |
| 24747 | BWS 4: Brauchwasser 1x erhitzen | `BOI.schnellladung` | s16 | 03 | rw | rw |
| 24748 | BWS 5: Brauchwasser 1x erhitzen | `BOI.schnellladung` | s16 | 03 | rw | rw |
| 24749 | BWS 6: Brauchwasser 1x erhitzen | `BOI.schnellladung` | s16 | 03 | rw | rw |
| 24750 | BWS 7: Brauchwasser 1x erhitzen | `BOI.schnellladung` | s16 | 03 | rw | rw |
| 24751 | BWS 8: Brauchwasser 1x erhitzen | `BOI.schnellladung` | s16 | 03 | rw | rw |
| 24752 | BWS 9: Brauchwasser 1x erhitzen | `BOI.schnellladung` | s16 | 03 | rw | rw |
| 24753 | BWS 10: Brauchwasser 1x erhitzen | `BOI.schnellladung` | s16 | 03 | rw | rw |
| 24754 | BWS 11: Brauchwasser 1x erhitzen | `BOI.schnellladung` | s16 | 03 | rw | rw |
| 24755 | BWS 12: Brauchwasser 1x erhitzen | `BOI.schnellladung` | s16 | 03 | rw | rw |
| 24756 | BWS 13: Brauchwasser 1x erhitzen | `BOI.schnellladung` | s16 | 03 | rw | rw |
| 24757 | BWS 14: Brauchwasser 1x erhitzen | `BOI.schnellladung` | s16 | 03 | rw | rw |
| 25092 | BWS 1: Max. Temperatur Heizstab | `BOI.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25093 | BWS 2: Max. Temperatur Heizstab | `BOI.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25094 | BWS 3: Max. Temperatur Heizstab | `BOI.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25095 | BWS 4: Max. Temperatur Heizstab | `BOI.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25096 | BWS 5: Max. Temperatur Heizstab | `BOI.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25097 | BWS 6: Max. Temperatur Heizstab | `BOI.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25098 | BWS 7: Max. Temperatur Heizstab | `BOI.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25099 | BWS 8: Max. Temperatur Heizstab | `BOI.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25100 | BWS 9: Max. Temperatur Heizstab | `BOI.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25101 | BWS 10: Max. Temperatur Heizstab | `BOI.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25102 | BWS 11: Max. Temperatur Heizstab | `BOI.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25103 | BWS 12: Max. Temperatur Heizstab | `BOI.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25104 | BWS 13: Max. Temperatur Heizstab | `BOI.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25105 | BWS 14: Max. Temperatur Heizstab | `BOI.heizstab_temperatur_max` | s16 | 03 | r | rw |
| 25109 | BWS 1: Modbus Anforderung Heizstab | `BOI.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25110 | BWS 2: Modbus Anforderung Heizstab | `BOI.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25111 | BWS 3: Modbus Anforderung Heizstab | `BOI.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25112 | BWS 4: Modbus Anforderung Heizstab | `BOI.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25113 | BWS 5: Modbus Anforderung Heizstab | `BOI.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25114 | BWS 6: Modbus Anforderung Heizstab | `BOI.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25115 | BWS 7: Modbus Anforderung Heizstab | `BOI.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25116 | BWS 8: Modbus Anforderung Heizstab | `BOI.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25117 | BWS 9: Modbus Anforderung Heizstab | `BOI.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25118 | BWS 10: Modbus Anforderung Heizstab | `BOI.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25119 | BWS 11: Modbus Anforderung Heizstab | `BOI.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25120 | BWS 12: Modbus Anforderung Heizstab | `BOI.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25121 | BWS 13: Modbus Anforderung Heizstab | `BOI.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25122 | BWS 14: Modbus Anforderung Heizstab | `BOI.heizstab_modbus_anforderung` | s16 | 03 | r | rw |
| 25126 | BWS 1: Max. Temperatur Wärmepumpe | `BOI.waermepumpe_temperatur_max` | s16 | 03 | r | rw |
| 25127 | BWS 2: Max. Temperatur Wärmepumpe | `BOI.waermepumpe_temperatur_max` | s16 | 03 | r | rw |
| 25128 | BWS 3: Max. Temperatur Wärmepumpe | `BOI.waermepumpe_temperatur_max` | s16 | 03 | r | rw |
| 25129 | BWS 4: Max. Temperatur Wärmepumpe | `BOI.waermepumpe_temperatur_max` | s16 | 03 | r | rw |
| 25130 | BWS 5: Max. Temperatur Wärmepumpe | `BOI.waermepumpe_temperatur_max` | s16 | 03 | r | rw |
| 25131 | BWS 6: Max. Temperatur Wärmepumpe | `BOI.waermepumpe_temperatur_max` | s16 | 03 | r | rw |
| 25132 | BWS 7: Max. Temperatur Wärmepumpe | `BOI.waermepumpe_temperatur_max` | s16 | 03 | r | rw |
| 25133 | BWS 8: Max. Temperatur Wärmepumpe | `BOI.waermepumpe_temperatur_max` | s16 | 03 | r | rw |
| 25134 | BWS 9: Max. Temperatur Wärmepumpe | `BOI.waermepumpe_temperatur_max` | s16 | 03 | r | rw |
| 25135 | BWS 10: Max. Temperatur Wärmepumpe | `BOI.waermepumpe_temperatur_max` | s16 | 03 | r | rw |
| 25136 | BWS 11: Max. Temperatur Wärmepumpe | `BOI.waermepumpe_temperatur_max` | s16 | 03 | r | rw |
| 25137 | BWS 12: Max. Temperatur Wärmepumpe | `BOI.waermepumpe_temperatur_max` | s16 | 03 | r | rw |
| 25138 | BWS 13: Max. Temperatur Wärmepumpe | `BOI.waermepumpe_temperatur_max` | s16 | 03 | r | rw |
| 25139 | BWS 14: Max. Temperatur Wärmepumpe | `BOI.waermepumpe_temperatur_max` | s16 | 03 | r | rw |
| 25143 | BWS 1: Modbus Anf. Wärmepumpe | `BOI.waermepumpe_modbus_anforderung` | s16 | 03 | r | rw |
| 25144 | BWS 2: Modbus Anf. Wärmepumpe | `BOI.waermepumpe_modbus_anforderung` | s16 | 03 | r | rw |
| 25145 | BWS 3: Modbus Anf. Wärmepumpe | `BOI.waermepumpe_modbus_anforderung` | s16 | 03 | r | rw |
| 25146 | BWS 4: Modbus Anf. Wärmepumpe | `BOI.waermepumpe_modbus_anforderung` | s16 | 03 | r | rw |
| 25147 | BWS 5: Modbus Anf. Wärmepumpe | `BOI.waermepumpe_modbus_anforderung` | s16 | 03 | r | rw |
| 25148 | BWS 6: Modbus Anf. Wärmepumpe | `BOI.waermepumpe_modbus_anforderung` | s16 | 03 | r | rw |
| 25149 | BWS 7: Modbus Anf. Wärmepumpe | `BOI.waermepumpe_modbus_anforderung` | s16 | 03 | r | rw |
| 25150 | BWS 8: Modbus Anf. Wärmepumpe | `BOI.waermepumpe_modbus_anforderung` | s16 | 03 | r | rw |
| 25151 | BWS 9: Modbus Anf. Wärmepumpe | `BOI.waermepumpe_modbus_anforderung` | s16 | 03 | r | rw |
| 25152 | BWS 10: Modbus Anf. Wärmepumpe | `BOI.waermepumpe_modbus_anforderung` | s16 | 03 | r | rw |
| 25153 | BWS 11: Modbus Anf. Wärmepumpe | `BOI.waermepumpe_modbus_anforderung` | s16 | 03 | r | rw |
| 25154 | BWS 12: Modbus Anf. Wärmepumpe | `BOI.waermepumpe_modbus_anforderung` | s16 | 03 | r | rw |
| 25155 | BWS 13: Modbus Anf. Wärmepumpe | `BOI.waermepumpe_modbus_anforderung` | s16 | 03 | r | rw |
| 25156 | BWS 14: Modbus Anf. Wärmepumpe | `BOI.waermepumpe_modbus_anforderung` | s16 | 03 | r | rw |
| 25353 | BWS 1: Quelle | `BOI.quelle` | s16 | 03 | r | r |
| 25354 | BWS 2: Quelle | `BOI.quelle` | s16 | 03 | r | r |
| 25355 | BWS 3: Quelle | `BOI.quelle` | s16 | 03 | r | r |
| 25356 | BWS 4: Quelle | `BOI.quelle` | s16 | 03 | r | r |
| 25357 | BWS 5: Quelle | `BOI.quelle` | s16 | 03 | r | r |
| 25358 | BWS 6: Quelle | `BOI.quelle` | s16 | 03 | r | r |
| 25359 | BWS 7: Quelle | `BOI.quelle` | s16 | 03 | r | r |
| 25360 | BWS 8: Quelle | `BOI.quelle` | s16 | 03 | r | r |
| 25361 | BWS 9: Quelle | `BOI.quelle` | s16 | 03 | r | r |
| 25362 | BWS 10: Quelle | `BOI.quelle` | s16 | 03 | r | r |
| 25363 | BWS 11: Quelle | `BOI.quelle` | s16 | 03 | r | r |
| 25364 | BWS 12: Quelle | `BOI.quelle` | s16 | 03 | r | r |
| 25365 | BWS 13: Quelle | `BOI.quelle` | s16 | 03 | r | r |
| 25366 | BWS 14: Quelle | `BOI.quelle` | s16 | 03 | r | r |

### Zweitwärmequellen (`secondary_heat_sources.json`, 140 Register)

| Adresse | Name (mit Slot) | Parameter | Typ | FC | User | Expert |
|---:|---|---|---|:---:|:---:|:---:|
| 8981 | ZWQ 1: Kesselpumpe | `ZK.o_pumpe` | s16 | 04 | r | r |
| 8982 | ZWQ 2: Kesselpumpe | `ZK.o_pumpe` | s16 | 04 | r | r |
| 8983 | ZWQ 3: Kesselpumpe | `ZK.o_pumpe` | s16 | 04 | r | r |
| 8984 | ZWQ 4: Kesselpumpe | `ZK.o_pumpe` | s16 | 04 | r | r |
| 8985 | ZWQ 5: Kesselpumpe | `ZK.o_pumpe` | s16 | 04 | r | r |
| 8986 | ZWQ 6: Kesselpumpe | `ZK.o_pumpe` | s16 | 04 | r | r |
| 8987 | ZWQ 7: Kesselpumpe | `ZK.o_pumpe` | s16 | 04 | r | r |
| 8988 | ZWQ 8: Kesselpumpe | `ZK.o_pumpe` | s16 | 04 | r | r |
| 8989 | ZWQ 9: Kesselpumpe | `ZK.o_pumpe` | s16 | 04 | r | r |
| 8990 | ZWQ 10: Kesselpumpe | `ZK.o_pumpe` | s16 | 04 | r | r |
| 8991 | ZWQ 11: Kesselpumpe | `ZK.o_pumpe` | s16 | 04 | r | r |
| 8992 | ZWQ 12: Kesselpumpe | `ZK.o_pumpe` | s16 | 04 | r | r |
| 8993 | ZWQ 13: Kesselpumpe | `ZK.o_pumpe` | s16 | 04 | r | r |
| 8994 | ZWQ 14: Kesselpumpe | `ZK.o_pumpe` | s16 | 04 | r | r |
| 8998 | ZWQ 1: Temperatur (value) | `ZK.i_temperatur.value` | s16 | 04 | r | r |
| 8999 | ZWQ 1: Temperatur (status) | `ZK.i_temperatur.status` | s16 | 04 | r | r |
| 9000 | ZWQ 2: Temperatur (value) | `ZK.i_temperatur.value` | s16 | 04 | r | r |
| 9001 | ZWQ 2: Temperatur (status) | `ZK.i_temperatur.status` | s16 | 04 | r | r |
| 9002 | ZWQ 3: Temperatur (value) | `ZK.i_temperatur.value` | s16 | 04 | r | r |
| 9003 | ZWQ 3: Temperatur (status) | `ZK.i_temperatur.status` | s16 | 04 | r | r |
| 9004 | ZWQ 4: Temperatur (value) | `ZK.i_temperatur.value` | s16 | 04 | r | r |
| 9005 | ZWQ 4: Temperatur (status) | `ZK.i_temperatur.status` | s16 | 04 | r | r |
| 9006 | ZWQ 5: Temperatur (value) | `ZK.i_temperatur.value` | s16 | 04 | r | r |
| 9007 | ZWQ 5: Temperatur (status) | `ZK.i_temperatur.status` | s16 | 04 | r | r |
| 9008 | ZWQ 6: Temperatur (value) | `ZK.i_temperatur.value` | s16 | 04 | r | r |
| 9009 | ZWQ 6: Temperatur (status) | `ZK.i_temperatur.status` | s16 | 04 | r | r |
| 9010 | ZWQ 7: Temperatur (value) | `ZK.i_temperatur.value` | s16 | 04 | r | r |
| 9011 | ZWQ 7: Temperatur (status) | `ZK.i_temperatur.status` | s16 | 04 | r | r |
| 9012 | ZWQ 8: Temperatur (value) | `ZK.i_temperatur.value` | s16 | 04 | r | r |
| 9013 | ZWQ 8: Temperatur (status) | `ZK.i_temperatur.status` | s16 | 04 | r | r |
| 9014 | ZWQ 9: Temperatur (value) | `ZK.i_temperatur.value` | s16 | 04 | r | r |
| 9015 | ZWQ 9: Temperatur (status) | `ZK.i_temperatur.status` | s16 | 04 | r | r |
| 9016 | ZWQ 10: Temperatur (value) | `ZK.i_temperatur.value` | s16 | 04 | r | r |
| 9017 | ZWQ 10: Temperatur (status) | `ZK.i_temperatur.status` | s16 | 04 | r | r |
| 9018 | ZWQ 11: Temperatur (value) | `ZK.i_temperatur.value` | s16 | 04 | r | r |
| 9019 | ZWQ 11: Temperatur (status) | `ZK.i_temperatur.status` | s16 | 04 | r | r |
| 9020 | ZWQ 12: Temperatur (value) | `ZK.i_temperatur.value` | s16 | 04 | r | r |
| 9021 | ZWQ 12: Temperatur (status) | `ZK.i_temperatur.status` | s16 | 04 | r | r |
| 9022 | ZWQ 13: Temperatur (value) | `ZK.i_temperatur.value` | s16 | 04 | r | r |
| 9023 | ZWQ 13: Temperatur (status) | `ZK.i_temperatur.status` | s16 | 04 | r | r |
| 9024 | ZWQ 14: Temperatur (value) | `ZK.i_temperatur.value` | s16 | 04 | r | r |
| 9025 | ZWQ 14: Temperatur (status) | `ZK.i_temperatur.status` | s16 | 04 | r | r |
| 9029 | ZWQ 1: Anforderung | `ZK.o_anforderung` | s16 | 04 | r | r |
| 9030 | ZWQ 2: Anforderung | `ZK.o_anforderung` | s16 | 04 | r | r |
| 9031 | ZWQ 3: Anforderung | `ZK.o_anforderung` | s16 | 04 | r | r |
| 9032 | ZWQ 4: Anforderung | `ZK.o_anforderung` | s16 | 04 | r | r |
| 9033 | ZWQ 5: Anforderung | `ZK.o_anforderung` | s16 | 04 | r | r |
| 9034 | ZWQ 6: Anforderung | `ZK.o_anforderung` | s16 | 04 | r | r |
| 9035 | ZWQ 7: Anforderung | `ZK.o_anforderung` | s16 | 04 | r | r |
| 9036 | ZWQ 8: Anforderung | `ZK.o_anforderung` | s16 | 04 | r | r |
| 9037 | ZWQ 9: Anforderung | `ZK.o_anforderung` | s16 | 04 | r | r |
| 9038 | ZWQ 10: Anforderung | `ZK.o_anforderung` | s16 | 04 | r | r |
| 9039 | ZWQ 11: Anforderung | `ZK.o_anforderung` | s16 | 04 | r | r |
| 9040 | ZWQ 12: Anforderung | `ZK.o_anforderung` | s16 | 04 | r | r |
| 9041 | ZWQ 13: Anforderung | `ZK.o_anforderung` | s16 | 04 | r | r |
| 9042 | ZWQ 14: Anforderung | `ZK.o_anforderung` | s16 | 04 | r | r |
| 9991 | ZWQ 1: Status | `ZK.status` | s16 | 04 | r | r |
| 9992 | ZWQ 2: Status | `ZK.status` | s16 | 04 | r | r |
| 9993 | ZWQ 3: Status | `ZK.status` | s16 | 04 | r | r |
| 9994 | ZWQ 4: Status | `ZK.status` | s16 | 04 | r | r |
| 9995 | ZWQ 5: Status | `ZK.status` | s16 | 04 | r | r |
| 9996 | ZWQ 6: Status | `ZK.status` | s16 | 04 | r | r |
| 9997 | ZWQ 7: Status | `ZK.status` | s16 | 04 | r | r |
| 9998 | ZWQ 8: Status | `ZK.status` | s16 | 04 | r | r |
| 9999 | ZWQ 9: Status | `ZK.status` | s16 | 04 | r | r |
| 10000 | ZWQ 10: Status | `ZK.status` | s16 | 04 | r | r |
| 10001 | ZWQ 11: Status | `ZK.status` | s16 | 04 | r | r |
| 10002 | ZWQ 12: Status | `ZK.status` | s16 | 04 | r | r |
| 10003 | ZWQ 13: Status | `ZK.status` | s16 | 04 | r | r |
| 10004 | ZWQ 14: Status | `ZK.status` | s16 | 04 | r | r |
| 10007 | ZWQ 1: Störung | `ZK.i_stoerung` | s16 | 04 | r | r |
| 10008 | ZWQ 2: Störung | `ZK.i_stoerung` | s16 | 04 | r | r |
| 10009 | ZWQ 3: Störung | `ZK.i_stoerung` | s16 | 04 | r | r |
| 10010 | ZWQ 4: Störung | `ZK.i_stoerung` | s16 | 04 | r | r |
| 10011 | ZWQ 5: Störung | `ZK.i_stoerung` | s16 | 04 | r | r |
| 10012 | ZWQ 6: Störung | `ZK.i_stoerung` | s16 | 04 | r | r |
| 10013 | ZWQ 7: Störung | `ZK.i_stoerung` | s16 | 04 | r | r |
| 10014 | ZWQ 8: Störung | `ZK.i_stoerung` | s16 | 04 | r | r |
| 10015 | ZWQ 9: Störung | `ZK.i_stoerung` | s16 | 04 | r | r |
| 10016 | ZWQ 10: Störung | `ZK.i_stoerung` | s16 | 04 | r | r |
| 10017 | ZWQ 11: Störung | `ZK.i_stoerung` | s16 | 04 | r | r |
| 10018 | ZWQ 12: Störung | `ZK.i_stoerung` | s16 | 04 | r | r |
| 10019 | ZWQ 13: Störung | `ZK.i_stoerung` | s16 | 04 | r | r |
| 10020 | ZWQ 14: Störung | `ZK.i_stoerung` | s16 | 04 | r | r |
| 10028 | ZWQ 1: Puffertemperatur (value) | `ZK.i_puffertemp_bei_sensor_auswahl.value` | s16 | 04 | r | r |
| 10029 | ZWQ 1: Puffertemperatur (status) | `ZK.i_puffertemp_bei_sensor_auswahl.status` | s16 | 04 | r | r |
| 10030 | ZWQ 2: Puffertemperatur (value) | `ZK.i_puffertemp_bei_sensor_auswahl.value` | s16 | 04 | r | r |
| 10031 | ZWQ 2: Puffertemperatur (status) | `ZK.i_puffertemp_bei_sensor_auswahl.status` | s16 | 04 | r | r |
| 10032 | ZWQ 3: Puffertemperatur (value) | `ZK.i_puffertemp_bei_sensor_auswahl.value` | s16 | 04 | r | r |
| 10033 | ZWQ 3: Puffertemperatur (status) | `ZK.i_puffertemp_bei_sensor_auswahl.status` | s16 | 04 | r | r |
| 10034 | ZWQ 4: Puffertemperatur (value) | `ZK.i_puffertemp_bei_sensor_auswahl.value` | s16 | 04 | r | r |
| 10035 | ZWQ 4: Puffertemperatur (status) | `ZK.i_puffertemp_bei_sensor_auswahl.status` | s16 | 04 | r | r |
| 10036 | ZWQ 5: Puffertemperatur (value) | `ZK.i_puffertemp_bei_sensor_auswahl.value` | s16 | 04 | r | r |
| 10037 | ZWQ 5: Puffertemperatur (status) | `ZK.i_puffertemp_bei_sensor_auswahl.status` | s16 | 04 | r | r |
| 10038 | ZWQ 6: Puffertemperatur (value) | `ZK.i_puffertemp_bei_sensor_auswahl.value` | s16 | 04 | r | r |
| 10039 | ZWQ 6: Puffertemperatur (status) | `ZK.i_puffertemp_bei_sensor_auswahl.status` | s16 | 04 | r | r |
| 10040 | ZWQ 7: Puffertemperatur (value) | `ZK.i_puffertemp_bei_sensor_auswahl.value` | s16 | 04 | r | r |
| 10041 | ZWQ 7: Puffertemperatur (status) | `ZK.i_puffertemp_bei_sensor_auswahl.status` | s16 | 04 | r | r |
| 10042 | ZWQ 8: Puffertemperatur (value) | `ZK.i_puffertemp_bei_sensor_auswahl.value` | s16 | 04 | r | r |
| 10043 | ZWQ 8: Puffertemperatur (status) | `ZK.i_puffertemp_bei_sensor_auswahl.status` | s16 | 04 | r | r |
| 10044 | ZWQ 9: Puffertemperatur (value) | `ZK.i_puffertemp_bei_sensor_auswahl.value` | s16 | 04 | r | r |
| 10045 | ZWQ 9: Puffertemperatur (status) | `ZK.i_puffertemp_bei_sensor_auswahl.status` | s16 | 04 | r | r |
| 10046 | ZWQ 10: Puffertemperatur (value) | `ZK.i_puffertemp_bei_sensor_auswahl.value` | s16 | 04 | r | r |
| 10047 | ZWQ 10: Puffertemperatur (status) | `ZK.i_puffertemp_bei_sensor_auswahl.status` | s16 | 04 | r | r |
| 10048 | ZWQ 11: Puffertemperatur (value) | `ZK.i_puffertemp_bei_sensor_auswahl.value` | s16 | 04 | r | r |
| 10049 | ZWQ 11: Puffertemperatur (status) | `ZK.i_puffertemp_bei_sensor_auswahl.status` | s16 | 04 | r | r |
| 10050 | ZWQ 12: Puffertemperatur (value) | `ZK.i_puffertemp_bei_sensor_auswahl.value` | s16 | 04 | r | r |
| 10051 | ZWQ 12: Puffertemperatur (status) | `ZK.i_puffertemp_bei_sensor_auswahl.status` | s16 | 04 | r | r |
| 10052 | ZWQ 13: Puffertemperatur (value) | `ZK.i_puffertemp_bei_sensor_auswahl.value` | s16 | 04 | r | r |
| 10053 | ZWQ 13: Puffertemperatur (status) | `ZK.i_puffertemp_bei_sensor_auswahl.status` | s16 | 04 | r | r |
| 10054 | ZWQ 14: Puffertemperatur (value) | `ZK.i_puffertemp_bei_sensor_auswahl.value` | s16 | 04 | r | r |
| 10055 | ZWQ 14: Puffertemperatur (status) | `ZK.i_puffertemp_bei_sensor_auswahl.status` | s16 | 04 | r | r |
| 25024 | ZWQ 1: Modbus Anforderung | `ZK.modbus_anforderung` | s16 | 03 | r | rw |
| 25025 | ZWQ 2: Modbus Anforderung | `ZK.modbus_anforderung` | s16 | 03 | r | rw |
| 25026 | ZWQ 3: Modbus Anforderung | `ZK.modbus_anforderung` | s16 | 03 | r | rw |
| 25027 | ZWQ 4: Modbus Anforderung | `ZK.modbus_anforderung` | s16 | 03 | r | rw |
| 25028 | ZWQ 5: Modbus Anforderung | `ZK.modbus_anforderung` | s16 | 03 | r | rw |
| 25029 | ZWQ 6: Modbus Anforderung | `ZK.modbus_anforderung` | s16 | 03 | r | rw |
| 25030 | ZWQ 7: Modbus Anforderung | `ZK.modbus_anforderung` | s16 | 03 | r | rw |
| 25031 | ZWQ 8: Modbus Anforderung | `ZK.modbus_anforderung` | s16 | 03 | r | rw |
| 25032 | ZWQ 9: Modbus Anforderung | `ZK.modbus_anforderung` | s16 | 03 | r | rw |
| 25033 | ZWQ 10: Modbus Anforderung | `ZK.modbus_anforderung` | s16 | 03 | r | rw |
| 25034 | ZWQ 11: Modbus Anforderung | `ZK.modbus_anforderung` | s16 | 03 | r | rw |
| 25035 | ZWQ 12: Modbus Anforderung | `ZK.modbus_anforderung` | s16 | 03 | r | rw |
| 25036 | ZWQ 13: Modbus Anforderung | `ZK.modbus_anforderung` | s16 | 03 | r | rw |
| 25037 | ZWQ 14: Modbus Anforderung | `ZK.modbus_anforderung` | s16 | 03 | r | rw |
| 25042 | ZWQ 1: Puffertemperatur Max. | `ZK.puffertemperatur_max` | s16 | 03 | r | r |
| 25043 | ZWQ 2: Puffertemperatur Max. | `ZK.puffertemperatur_max` | s16 | 03 | r | r |
| 25044 | ZWQ 3: Puffertemperatur Max. | `ZK.puffertemperatur_max` | s16 | 03 | r | r |
| 25045 | ZWQ 4: Puffertemperatur Max. | `ZK.puffertemperatur_max` | s16 | 03 | r | r |
| 25046 | ZWQ 5: Puffertemperatur Max. | `ZK.puffertemperatur_max` | s16 | 03 | r | r |
| 25047 | ZWQ 6: Puffertemperatur Max. | `ZK.puffertemperatur_max` | s16 | 03 | r | r |
| 25048 | ZWQ 7: Puffertemperatur Max. | `ZK.puffertemperatur_max` | s16 | 03 | r | r |
| 25049 | ZWQ 8: Puffertemperatur Max. | `ZK.puffertemperatur_max` | s16 | 03 | r | r |
| 25050 | ZWQ 9: Puffertemperatur Max. | `ZK.puffertemperatur_max` | s16 | 03 | r | r |
| 25051 | ZWQ 10: Puffertemperatur Max. | `ZK.puffertemperatur_max` | s16 | 03 | r | r |
| 25052 | ZWQ 11: Puffertemperatur Max. | `ZK.puffertemperatur_max` | s16 | 03 | r | r |
| 25053 | ZWQ 12: Puffertemperatur Max. | `ZK.puffertemperatur_max` | s16 | 03 | r | r |
| 25054 | ZWQ 13: Puffertemperatur Max. | `ZK.puffertemperatur_max` | s16 | 03 | r | r |
| 25055 | ZWQ 14: Puffertemperatur Max. | `ZK.puffertemperatur_max` | s16 | 03 | r | r |

### Zirkulation (`circulation.json`, 60 Register)

| Adresse | Name (mit Slot) | Parameter | Typ | FC | User | Expert |
|---:|---|---|---|:---:|:---:|:---:|
| 8929 | Zirk 0: Temperatur (value) | `ZIRK.i_temperatur.value` | s16 | 04 | r | r |
| 8930 | Zirk 0: Temperatur (status) | `ZIRK.i_temperatur.status` | s16 | 04 | r | r |
| 8931 | Zirk 1: Temperatur (value) | `ZIRK.i_temperatur.value` | s16 | 04 | r | r |
| 8932 | Zirk 1: Temperatur (status) | `ZIRK.i_temperatur.status` | s16 | 04 | r | r |
| 8933 | Zirk 2: Temperatur (value) | `ZIRK.i_temperatur.value` | s16 | 04 | r | r |
| 8934 | Zirk 2: Temperatur (status) | `ZIRK.i_temperatur.status` | s16 | 04 | r | r |
| 8935 | Zirk 3: Temperatur (value) | `ZIRK.i_temperatur.value` | s16 | 04 | r | r |
| 8936 | Zirk 3: Temperatur (status) | `ZIRK.i_temperatur.status` | s16 | 04 | r | r |
| 8937 | Zirk 4: Temperatur (value) | `ZIRK.i_temperatur.value` | s16 | 04 | r | r |
| 8938 | Zirk 4: Temperatur (status) | `ZIRK.i_temperatur.status` | s16 | 04 | r | r |
| 8939 | Zirk 5: Temperatur (value) | `ZIRK.i_temperatur.value` | s16 | 04 | r | r |
| 8940 | Zirk 5: Temperatur (status) | `ZIRK.i_temperatur.status` | s16 | 04 | r | r |
| 8941 | Zirk 6: Temperatur (value) | `ZIRK.i_temperatur.value` | s16 | 04 | r | r |
| 8942 | Zirk 6: Temperatur (status) | `ZIRK.i_temperatur.status` | s16 | 04 | r | r |
| 8943 | Zirk 7: Temperatur (value) | `ZIRK.i_temperatur.value` | s16 | 04 | r | r |
| 8944 | Zirk 7: Temperatur (status) | `ZIRK.i_temperatur.status` | s16 | 04 | r | r |
| 8945 | Zirk 8: Temperatur (value) | `ZIRK.i_temperatur.value` | s16 | 04 | r | r |
| 8946 | Zirk 8: Temperatur (status) | `ZIRK.i_temperatur.status` | s16 | 04 | r | r |
| 8947 | Zirk 9: Temperatur (value) | `ZIRK.i_temperatur.value` | s16 | 04 | r | r |
| 8948 | Zirk 9: Temperatur (status) | `ZIRK.i_temperatur.status` | s16 | 04 | r | r |
| 8949 | Zirk 10: Temperatur (value) | `ZIRK.i_temperatur.value` | s16 | 04 | r | r |
| 8950 | Zirk 10: Temperatur (status) | `ZIRK.i_temperatur.status` | s16 | 04 | r | r |
| 8951 | Zirk 11: Temperatur (value) | `ZIRK.i_temperatur.value` | s16 | 04 | r | r |
| 8952 | Zirk 11: Temperatur (status) | `ZIRK.i_temperatur.status` | s16 | 04 | r | r |
| 8953 | Zirk 12: Temperatur (value) | `ZIRK.i_temperatur.value` | s16 | 04 | r | r |
| 8954 | Zirk 12: Temperatur (status) | `ZIRK.i_temperatur.status` | s16 | 04 | r | r |
| 8955 | Zirk 13: Temperatur (value) | `ZIRK.i_temperatur.value` | s16 | 04 | r | r |
| 8956 | Zirk 13: Temperatur (status) | `ZIRK.i_temperatur.status` | s16 | 04 | r | r |
| 8957 | Zirk 14: Temperatur (value) | `ZIRK.i_temperatur.value` | s16 | 04 | r | r |
| 8958 | Zirk 14: Temperatur (status) | `ZIRK.i_temperatur.status` | s16 | 04 | r | r |
| 8963 | Zirk 0: Pumpe | `ZIRK.o_pumpe` | s16 | 04 | r | r |
| 8964 | Zirk 1: Pumpe | `ZIRK.o_pumpe` | s16 | 04 | r | r |
| 8965 | Zirk 2: Pumpe | `ZIRK.o_pumpe` | s16 | 04 | r | r |
| 8966 | Zirk 3: Pumpe | `ZIRK.o_pumpe` | s16 | 04 | r | r |
| 8967 | Zirk 4: Pumpe | `ZIRK.o_pumpe` | s16 | 04 | r | r |
| 8968 | Zirk 5: Pumpe | `ZIRK.o_pumpe` | s16 | 04 | r | r |
| 8969 | Zirk 6: Pumpe | `ZIRK.o_pumpe` | s16 | 04 | r | r |
| 8970 | Zirk 7: Pumpe | `ZIRK.o_pumpe` | s16 | 04 | r | r |
| 8971 | Zirk 8: Pumpe | `ZIRK.o_pumpe` | s16 | 04 | r | r |
| 8972 | Zirk 9: Pumpe | `ZIRK.o_pumpe` | s16 | 04 | r | r |
| 8973 | Zirk 10: Pumpe | `ZIRK.o_pumpe` | s16 | 04 | r | r |
| 8974 | Zirk 11: Pumpe | `ZIRK.o_pumpe` | s16 | 04 | r | r |
| 8975 | Zirk 12: Pumpe | `ZIRK.o_pumpe` | s16 | 04 | r | r |
| 8976 | Zirk 13: Pumpe | `ZIRK.o_pumpe` | s16 | 04 | r | r |
| 8977 | Zirk 14: Pumpe | `ZIRK.o_pumpe` | s16 | 04 | r | r |
| 24828 | Zirk 0: Programm wählen | `ZIRK.programm` | s16 | 03 | rw | rw |
| 24829 | Zirk 1: Programm wählen | `ZIRK.programm` | s16 | 03 | rw | rw |
| 24830 | Zirk 2: Programm wählen | `ZIRK.programm` | s16 | 03 | rw | rw |
| 24831 | Zirk 3: Programm wählen | `ZIRK.programm` | s16 | 03 | rw | rw |
| 24832 | Zirk 4: Programm wählen | `ZIRK.programm` | s16 | 03 | rw | rw |
| 24833 | Zirk 5: Programm wählen | `ZIRK.programm` | s16 | 03 | rw | rw |
| 24834 | Zirk 6: Programm wählen | `ZIRK.programm` | s16 | 03 | rw | rw |
| 24835 | Zirk 7: Programm wählen | `ZIRK.programm` | s16 | 03 | rw | rw |
| 24836 | Zirk 8: Programm wählen | `ZIRK.programm` | s16 | 03 | rw | rw |
| 24837 | Zirk 9: Programm wählen | `ZIRK.programm` | s16 | 03 | rw | rw |
| 24838 | Zirk 10: Programm wählen | `ZIRK.programm` | s16 | 03 | rw | rw |
| 24839 | Zirk 11: Programm wählen | `ZIRK.programm` | s16 | 03 | rw | rw |
| 24840 | Zirk 12: Programm wählen | `ZIRK.programm` | s16 | 03 | rw | rw |
| 24841 | Zirk 13: Programm wählen | `ZIRK.programm` | s16 | 03 | rw | rw |
| 24842 | Zirk 14: Programm wählen | `ZIRK.programm` | s16 | 03 | rw | rw |

### Solar (`solar.json`, 406 Register)

| Adresse | Name (mit Slot) | Parameter | Typ | FC | User | Expert |
|---:|---|---|---|:---:|:---:|:---:|
| 9049 | SOL 1: Status | `SOL.status` | s16 | 04 | r | r |
| 9050 | SOL 2: Status | `SOL.status` | s16 | 04 | r | r |
| 9051 | SOL 3: Status | `SOL.status` | s16 | 04 | r | r |
| 9052 | SOL 4: Status | `SOL.status` | s16 | 04 | r | r |
| 9053 | SOL 5: Status | `SOL.status` | s16 | 04 | r | r |
| 9054 | SOL 6: Status | `SOL.status` | s16 | 04 | r | r |
| 9055 | SOL 7: Status | `SOL.status` | s16 | 04 | r | r |
| 9056 | SOL 8: Status | `SOL.status` | s16 | 04 | r | r |
| 9057 | SOL 9: Status | `SOL.status` | s16 | 04 | r | r |
| 9058 | SOL 10: Status | `SOL.status` | s16 | 04 | r | r |
| 9059 | SOL 11: Status | `SOL.status` | s16 | 04 | r | r |
| 9060 | SOL 12: Status | `SOL.status` | s16 | 04 | r | r |
| 9061 | SOL 13: Status | `SOL.status` | s16 | 04 | r | r |
| 9062 | SOL 14: Status | `SOL.status` | s16 | 04 | r | r |
| 9064 | SOL 1: Statusursache | `SOL.status_ursache` | s16 | 04 | r | r |
| 9065 | SOL 2: Statusursache | `SOL.status_ursache` | s16 | 04 | r | r |
| 9066 | SOL 3: Statusursache | `SOL.status_ursache` | s16 | 04 | r | r |
| 9067 | SOL 4: Statusursache | `SOL.status_ursache` | s16 | 04 | r | r |
| 9068 | SOL 5: Statusursache | `SOL.status_ursache` | s16 | 04 | r | r |
| 9069 | SOL 6: Statusursache | `SOL.status_ursache` | s16 | 04 | r | r |
| 9070 | SOL 7: Statusursache | `SOL.status_ursache` | s16 | 04 | r | r |
| 9071 | SOL 8: Statusursache | `SOL.status_ursache` | s16 | 04 | r | r |
| 9072 | SOL 9: Statusursache | `SOL.status_ursache` | s16 | 04 | r | r |
| 9073 | SOL 10: Statusursache | `SOL.status_ursache` | s16 | 04 | r | r |
| 9074 | SOL 11: Statusursache | `SOL.status_ursache` | s16 | 04 | r | r |
| 9075 | SOL 12: Statusursache | `SOL.status_ursache` | s16 | 04 | r | r |
| 9076 | SOL 13: Statusursache | `SOL.status_ursache` | s16 | 04 | r | r |
| 9077 | SOL 14: Statusursache | `SOL.status_ursache` | s16 | 04 | r | r |
| 9080 | SOL 1: Kollektortemperatur (value) | `SOL.i_kollektor_temperatur.value` | s16 | 04 | r | r |
| 9081 | SOL 1: Kollektortemperatur (status) | `SOL.i_kollektor_temperatur.status` | s16 | 04 | r | r |
| 9082 | SOL 2: Kollektortemperatur (value) | `SOL.i_kollektor_temperatur.value` | s16 | 04 | r | r |
| 9083 | SOL 2: Kollektortemperatur (status) | `SOL.i_kollektor_temperatur.status` | s16 | 04 | r | r |
| 9084 | SOL 3: Kollektortemperatur (value) | `SOL.i_kollektor_temperatur.value` | s16 | 04 | r | r |
| 9085 | SOL 3: Kollektortemperatur (status) | `SOL.i_kollektor_temperatur.status` | s16 | 04 | r | r |
| 9086 | SOL 4: Kollektortemperatur (value) | `SOL.i_kollektor_temperatur.value` | s16 | 04 | r | r |
| 9087 | SOL 4: Kollektortemperatur (status) | `SOL.i_kollektor_temperatur.status` | s16 | 04 | r | r |
| 9088 | SOL 5: Kollektortemperatur (value) | `SOL.i_kollektor_temperatur.value` | s16 | 04 | r | r |
| 9089 | SOL 5: Kollektortemperatur (status) | `SOL.i_kollektor_temperatur.status` | s16 | 04 | r | r |
| 9090 | SOL 6: Kollektortemperatur (value) | `SOL.i_kollektor_temperatur.value` | s16 | 04 | r | r |
| 9091 | SOL 6: Kollektortemperatur (status) | `SOL.i_kollektor_temperatur.status` | s16 | 04 | r | r |
| 9092 | SOL 7: Kollektortemperatur (value) | `SOL.i_kollektor_temperatur.value` | s16 | 04 | r | r |
| 9093 | SOL 7: Kollektortemperatur (status) | `SOL.i_kollektor_temperatur.status` | s16 | 04 | r | r |
| 9094 | SOL 8: Kollektortemperatur (value) | `SOL.i_kollektor_temperatur.value` | s16 | 04 | r | r |
| 9095 | SOL 8: Kollektortemperatur (status) | `SOL.i_kollektor_temperatur.status` | s16 | 04 | r | r |
| 9096 | SOL 9: Kollektortemperatur (value) | `SOL.i_kollektor_temperatur.value` | s16 | 04 | r | r |
| 9097 | SOL 9: Kollektortemperatur (status) | `SOL.i_kollektor_temperatur.status` | s16 | 04 | r | r |
| 9098 | SOL 10: Kollektortemperatur (value) | `SOL.i_kollektor_temperatur.value` | s16 | 04 | r | r |
| 9099 | SOL 10: Kollektortemperatur (status) | `SOL.i_kollektor_temperatur.status` | s16 | 04 | r | r |
| 9100 | SOL 11: Kollektortemperatur (value) | `SOL.i_kollektor_temperatur.value` | s16 | 04 | r | r |
| 9101 | SOL 11: Kollektortemperatur (status) | `SOL.i_kollektor_temperatur.status` | s16 | 04 | r | r |
| 9102 | SOL 12: Kollektortemperatur (value) | `SOL.i_kollektor_temperatur.value` | s16 | 04 | r | r |
| 9103 | SOL 12: Kollektortemperatur (status) | `SOL.i_kollektor_temperatur.status` | s16 | 04 | r | r |
| 9104 | SOL 13: Kollektortemperatur (value) | `SOL.i_kollektor_temperatur.value` | s16 | 04 | r | r |
| 9105 | SOL 13: Kollektortemperatur (status) | `SOL.i_kollektor_temperatur.status` | s16 | 04 | r | r |
| 9106 | SOL 14: Kollektortemperatur (value) | `SOL.i_kollektor_temperatur.value` | s16 | 04 | r | r |
| 9107 | SOL 14: Kollektortemperatur (status) | `SOL.i_kollektor_temperatur.status` | s16 | 04 | r | r |
| 9110 | SOL 1: Temperatur Speicher 1 (value) | `SOL.i_ist_temperatur_speicher_1.value` | s16 | 04 | r | r |
| 9111 | SOL 1: Temperatur Speicher 1 (status) | `SOL.i_ist_temperatur_speicher_1.status` | s16 | 04 | r | r |
| 9112 | SOL 2: Temperatur Speicher 1 (value) | `SOL.i_ist_temperatur_speicher_1.value` | s16 | 04 | r | r |
| 9113 | SOL 2: Temperatur Speicher 1 (status) | `SOL.i_ist_temperatur_speicher_1.status` | s16 | 04 | r | r |
| 9114 | SOL 3: Temperatur Speicher 1 (value) | `SOL.i_ist_temperatur_speicher_1.value` | s16 | 04 | r | r |
| 9115 | SOL 3: Temperatur Speicher 1 (status) | `SOL.i_ist_temperatur_speicher_1.status` | s16 | 04 | r | r |
| 9116 | SOL 4: Temperatur Speicher 1 (value) | `SOL.i_ist_temperatur_speicher_1.value` | s16 | 04 | r | r |
| 9117 | SOL 4: Temperatur Speicher 1 (status) | `SOL.i_ist_temperatur_speicher_1.status` | s16 | 04 | r | r |
| 9118 | SOL 5: Temperatur Speicher 1 (value) | `SOL.i_ist_temperatur_speicher_1.value` | s16 | 04 | r | r |
| 9119 | SOL 5: Temperatur Speicher 1 (status) | `SOL.i_ist_temperatur_speicher_1.status` | s16 | 04 | r | r |
| 9120 | SOL 6: Temperatur Speicher 1 (value) | `SOL.i_ist_temperatur_speicher_1.value` | s16 | 04 | r | r |
| 9121 | SOL 6: Temperatur Speicher 1 (status) | `SOL.i_ist_temperatur_speicher_1.status` | s16 | 04 | r | r |
| 9122 | SOL 7: Temperatur Speicher 1 (value) | `SOL.i_ist_temperatur_speicher_1.value` | s16 | 04 | r | r |
| 9123 | SOL 7: Temperatur Speicher 1 (status) | `SOL.i_ist_temperatur_speicher_1.status` | s16 | 04 | r | r |
| 9124 | SOL 8: Temperatur Speicher 1 (value) | `SOL.i_ist_temperatur_speicher_1.value` | s16 | 04 | r | r |
| 9125 | SOL 8: Temperatur Speicher 1 (status) | `SOL.i_ist_temperatur_speicher_1.status` | s16 | 04 | r | r |
| 9126 | SOL 9: Temperatur Speicher 1 (value) | `SOL.i_ist_temperatur_speicher_1.value` | s16 | 04 | r | r |
| 9127 | SOL 9: Temperatur Speicher 1 (status) | `SOL.i_ist_temperatur_speicher_1.status` | s16 | 04 | r | r |
| 9128 | SOL 10: Temperatur Speicher 1 (value) | `SOL.i_ist_temperatur_speicher_1.value` | s16 | 04 | r | r |
| 9129 | SOL 10: Temperatur Speicher 1 (status) | `SOL.i_ist_temperatur_speicher_1.status` | s16 | 04 | r | r |
| 9130 | SOL 11: Temperatur Speicher 1 (value) | `SOL.i_ist_temperatur_speicher_1.value` | s16 | 04 | r | r |
| 9131 | SOL 11: Temperatur Speicher 1 (status) | `SOL.i_ist_temperatur_speicher_1.status` | s16 | 04 | r | r |
| 9132 | SOL 12: Temperatur Speicher 1 (value) | `SOL.i_ist_temperatur_speicher_1.value` | s16 | 04 | r | r |
| 9133 | SOL 12: Temperatur Speicher 1 (status) | `SOL.i_ist_temperatur_speicher_1.status` | s16 | 04 | r | r |
| 9134 | SOL 13: Temperatur Speicher 1 (value) | `SOL.i_ist_temperatur_speicher_1.value` | s16 | 04 | r | r |
| 9135 | SOL 13: Temperatur Speicher 1 (status) | `SOL.i_ist_temperatur_speicher_1.status` | s16 | 04 | r | r |
| 9136 | SOL 14: Temperatur Speicher 1 (value) | `SOL.i_ist_temperatur_speicher_1.value` | s16 | 04 | r | r |
| 9137 | SOL 14: Temperatur Speicher 1 (status) | `SOL.i_ist_temperatur_speicher_1.status` | s16 | 04 | r | r |
| 9140 | SOL 1: Temperatur Speicher 2 (value) | `SOL.i_ist_temperatur_speicher_2.value` | s16 | 04 | r | r |
| 9141 | SOL 1: Temperatur Speicher 2 (status) | `SOL.i_ist_temperatur_speicher_2.status` | s16 | 04 | r | r |
| 9142 | SOL 2: Temperatur Speicher 2 (value) | `SOL.i_ist_temperatur_speicher_2.value` | s16 | 04 | r | r |
| 9143 | SOL 2: Temperatur Speicher 2 (status) | `SOL.i_ist_temperatur_speicher_2.status` | s16 | 04 | r | r |
| 9144 | SOL 3: Temperatur Speicher 2 (value) | `SOL.i_ist_temperatur_speicher_2.value` | s16 | 04 | r | r |
| 9145 | SOL 3: Temperatur Speicher 2 (status) | `SOL.i_ist_temperatur_speicher_2.status` | s16 | 04 | r | r |
| 9146 | SOL 4: Temperatur Speicher 2 (value) | `SOL.i_ist_temperatur_speicher_2.value` | s16 | 04 | r | r |
| 9147 | SOL 4: Temperatur Speicher 2 (status) | `SOL.i_ist_temperatur_speicher_2.status` | s16 | 04 | r | r |
| 9148 | SOL 5: Temperatur Speicher 2 (value) | `SOL.i_ist_temperatur_speicher_2.value` | s16 | 04 | r | r |
| 9149 | SOL 5: Temperatur Speicher 2 (status) | `SOL.i_ist_temperatur_speicher_2.status` | s16 | 04 | r | r |
| 9150 | SOL 6: Temperatur Speicher 2 (value) | `SOL.i_ist_temperatur_speicher_2.value` | s16 | 04 | r | r |
| 9151 | SOL 6: Temperatur Speicher 2 (status) | `SOL.i_ist_temperatur_speicher_2.status` | s16 | 04 | r | r |
| 9152 | SOL 7: Temperatur Speicher 2 (value) | `SOL.i_ist_temperatur_speicher_2.value` | s16 | 04 | r | r |
| 9153 | SOL 7: Temperatur Speicher 2 (status) | `SOL.i_ist_temperatur_speicher_2.status` | s16 | 04 | r | r |
| 9154 | SOL 8: Temperatur Speicher 2 (value) | `SOL.i_ist_temperatur_speicher_2.value` | s16 | 04 | r | r |
| 9155 | SOL 8: Temperatur Speicher 2 (status) | `SOL.i_ist_temperatur_speicher_2.status` | s16 | 04 | r | r |
| 9156 | SOL 9: Temperatur Speicher 2 (value) | `SOL.i_ist_temperatur_speicher_2.value` | s16 | 04 | r | r |
| 9157 | SOL 9: Temperatur Speicher 2 (status) | `SOL.i_ist_temperatur_speicher_2.status` | s16 | 04 | r | r |
| 9158 | SOL 10: Temperatur Speicher 2 (value) | `SOL.i_ist_temperatur_speicher_2.value` | s16 | 04 | r | r |
| 9159 | SOL 10: Temperatur Speicher 2 (status) | `SOL.i_ist_temperatur_speicher_2.status` | s16 | 04 | r | r |
| 9160 | SOL 11: Temperatur Speicher 2 (value) | `SOL.i_ist_temperatur_speicher_2.value` | s16 | 04 | r | r |
| 9161 | SOL 11: Temperatur Speicher 2 (status) | `SOL.i_ist_temperatur_speicher_2.status` | s16 | 04 | r | r |
| 9162 | SOL 12: Temperatur Speicher 2 (value) | `SOL.i_ist_temperatur_speicher_2.value` | s16 | 04 | r | r |
| 9163 | SOL 12: Temperatur Speicher 2 (status) | `SOL.i_ist_temperatur_speicher_2.status` | s16 | 04 | r | r |
| 9164 | SOL 13: Temperatur Speicher 2 (value) | `SOL.i_ist_temperatur_speicher_2.value` | s16 | 04 | r | r |
| 9165 | SOL 13: Temperatur Speicher 2 (status) | `SOL.i_ist_temperatur_speicher_2.status` | s16 | 04 | r | r |
| 9166 | SOL 14: Temperatur Speicher 2 (value) | `SOL.i_ist_temperatur_speicher_2.value` | s16 | 04 | r | r |
| 9167 | SOL 14: Temperatur Speicher 2 (status) | `SOL.i_ist_temperatur_speicher_2.status` | s16 | 04 | r | r |
| 9169 | SOL 1: Pumpe 1 | `SOL.o_pumpe_1` | s16 | 04 | r | r |
| 9170 | SOL 2: Pumpe 1 | `SOL.o_pumpe_1` | s16 | 04 | r | r |
| 9171 | SOL 3: Pumpe 1 | `SOL.o_pumpe_1` | s16 | 04 | r | r |
| 9172 | SOL 4: Pumpe 1 | `SOL.o_pumpe_1` | s16 | 04 | r | r |
| 9173 | SOL 5: Pumpe 1 | `SOL.o_pumpe_1` | s16 | 04 | r | r |
| 9174 | SOL 6: Pumpe 1 | `SOL.o_pumpe_1` | s16 | 04 | r | r |
| 9175 | SOL 7: Pumpe 1 | `SOL.o_pumpe_1` | s16 | 04 | r | r |
| 9176 | SOL 8: Pumpe 1 | `SOL.o_pumpe_1` | s16 | 04 | r | r |
| 9177 | SOL 9: Pumpe 1 | `SOL.o_pumpe_1` | s16 | 04 | r | r |
| 9178 | SOL 10: Pumpe 1 | `SOL.o_pumpe_1` | s16 | 04 | r | r |
| 9179 | SOL 11: Pumpe 1 | `SOL.o_pumpe_1` | s16 | 04 | r | r |
| 9180 | SOL 12: Pumpe 1 | `SOL.o_pumpe_1` | s16 | 04 | r | r |
| 9181 | SOL 13: Pumpe 1 | `SOL.o_pumpe_1` | s16 | 04 | r | r |
| 9182 | SOL 14: Pumpe 1 | `SOL.o_pumpe_1` | s16 | 04 | r | r |
| 9184 | SOL 1: Pumpe 2 | `SOL.o_pumpe_2` | s16 | 04 | r | r |
| 9185 | SOL 2: Pumpe 2 | `SOL.o_pumpe_2` | s16 | 04 | r | r |
| 9186 | SOL 3: Pumpe 2 | `SOL.o_pumpe_2` | s16 | 04 | r | r |
| 9187 | SOL 4: Pumpe 2 | `SOL.o_pumpe_2` | s16 | 04 | r | r |
| 9188 | SOL 5: Pumpe 2 | `SOL.o_pumpe_2` | s16 | 04 | r | r |
| 9189 | SOL 6: Pumpe 2 | `SOL.o_pumpe_2` | s16 | 04 | r | r |
| 9190 | SOL 7: Pumpe 2 | `SOL.o_pumpe_2` | s16 | 04 | r | r |
| 9191 | SOL 8: Pumpe 2 | `SOL.o_pumpe_2` | s16 | 04 | r | r |
| 9192 | SOL 9: Pumpe 2 | `SOL.o_pumpe_2` | s16 | 04 | r | r |
| 9193 | SOL 10: Pumpe 2 | `SOL.o_pumpe_2` | s16 | 04 | r | r |
| 9194 | SOL 11: Pumpe 2 | `SOL.o_pumpe_2` | s16 | 04 | r | r |
| 9195 | SOL 12: Pumpe 2 | `SOL.o_pumpe_2` | s16 | 04 | r | r |
| 9196 | SOL 13: Pumpe 2 | `SOL.o_pumpe_2` | s16 | 04 | r | r |
| 9197 | SOL 14: Pumpe 2 | `SOL.o_pumpe_2` | s16 | 04 | r | r |
| 9199 | SOL 1: Umschaltventil | `SOL.o_umschaltventil` | s16 | 04 | r | r |
| 9200 | SOL 2: Umschaltventil | `SOL.o_umschaltventil` | s16 | 04 | r | r |
| 9201 | SOL 3: Umschaltventil | `SOL.o_umschaltventil` | s16 | 04 | r | r |
| 9202 | SOL 4: Umschaltventil | `SOL.o_umschaltventil` | s16 | 04 | r | r |
| 9203 | SOL 5: Umschaltventil | `SOL.o_umschaltventil` | s16 | 04 | r | r |
| 9204 | SOL 6: Umschaltventil | `SOL.o_umschaltventil` | s16 | 04 | r | r |
| 9205 | SOL 7: Umschaltventil | `SOL.o_umschaltventil` | s16 | 04 | r | r |
| 9206 | SOL 8: Umschaltventil | `SOL.o_umschaltventil` | s16 | 04 | r | r |
| 9207 | SOL 9: Umschaltventil | `SOL.o_umschaltventil` | s16 | 04 | r | r |
| 9208 | SOL 10: Umschaltventil | `SOL.o_umschaltventil` | s16 | 04 | r | r |
| 9209 | SOL 11: Umschaltventil | `SOL.o_umschaltventil` | s16 | 04 | r | r |
| 9210 | SOL 12: Umschaltventil | `SOL.o_umschaltventil` | s16 | 04 | r | r |
| 9211 | SOL 13: Umschaltventil | `SOL.o_umschaltventil` | s16 | 04 | r | r |
| 9212 | SOL 14: Umschaltventil | `SOL.o_umschaltventil` | s16 | 04 | r | r |
| 9215 | SOL 1: Wärmeleistung | `SOL.waermeleistung` | u32 | 04 | r | r |
| 9217 | SOL 2: Wärmeleistung | `SOL.waermeleistung` | u32 | 04 | r | r |
| 9219 | SOL 3: Wärmeleistung | `SOL.waermeleistung` | u32 | 04 | r | r |
| 9221 | SOL 4: Wärmeleistung | `SOL.waermeleistung` | u32 | 04 | r | r |
| 9223 | SOL 5: Wärmeleistung | `SOL.waermeleistung` | u32 | 04 | r | r |
| 9225 | SOL 6: Wärmeleistung | `SOL.waermeleistung` | u32 | 04 | r | r |
| 9227 | SOL 7: Wärmeleistung | `SOL.waermeleistung` | u32 | 04 | r | r |
| 9229 | SOL 8: Wärmeleistung | `SOL.waermeleistung` | u32 | 04 | r | r |
| 9231 | SOL 9: Wärmeleistung | `SOL.waermeleistung` | u32 | 04 | r | r |
| 9233 | SOL 10: Wärmeleistung | `SOL.waermeleistung` | u32 | 04 | r | r |
| 9235 | SOL 11: Wärmeleistung | `SOL.waermeleistung` | u32 | 04 | r | r |
| 9237 | SOL 12: Wärmeleistung | `SOL.waermeleistung` | u32 | 04 | r | r |
| 9239 | SOL 13: Wärmeleistung | `SOL.waermeleistung` | u32 | 04 | r | r |
| 9241 | SOL 14: Wärmeleistung | `SOL.waermeleistung` | u32 | 04 | r | r |
| 9245 | SOL 1: Wärmemenge Tag | `SOL.waermemenge_tag` | u32 | 04 | r | r |
| 9247 | SOL 2: Wärmemenge Tag | `SOL.waermemenge_tag` | u32 | 04 | r | r |
| 9249 | SOL 3: Wärmemenge Tag | `SOL.waermemenge_tag` | u32 | 04 | r | r |
| 9251 | SOL 4: Wärmemenge Tag | `SOL.waermemenge_tag` | u32 | 04 | r | r |
| 9253 | SOL 5: Wärmemenge Tag | `SOL.waermemenge_tag` | u32 | 04 | r | r |
| 9255 | SOL 6: Wärmemenge Tag | `SOL.waermemenge_tag` | u32 | 04 | r | r |
| 9257 | SOL 7: Wärmemenge Tag | `SOL.waermemenge_tag` | u32 | 04 | r | r |
| 9259 | SOL 8: Wärmemenge Tag | `SOL.waermemenge_tag` | u32 | 04 | r | r |
| 9261 | SOL 9: Wärmemenge Tag | `SOL.waermemenge_tag` | u32 | 04 | r | r |
| 9263 | SOL 10: Wärmemenge Tag | `SOL.waermemenge_tag` | u32 | 04 | r | r |
| 9265 | SOL 11: Wärmemenge Tag | `SOL.waermemenge_tag` | u32 | 04 | r | r |
| 9267 | SOL 12: Wärmemenge Tag | `SOL.waermemenge_tag` | u32 | 04 | r | r |
| 9269 | SOL 13: Wärmemenge Tag | `SOL.waermemenge_tag` | u32 | 04 | r | r |
| 9271 | SOL 14: Wärmemenge Tag | `SOL.waermemenge_tag` | u32 | 04 | r | r |
| 9275 | SOL 1: Wärmemenge gesamt | `SOL.waermemenge_gesamt_kwh` | u32 | 04 | r | r |
| 9277 | SOL 2: Wärmemenge gesamt | `SOL.waermemenge_gesamt_kwh` | u32 | 04 | r | r |
| 9279 | SOL 3: Wärmemenge gesamt | `SOL.waermemenge_gesamt_kwh` | u32 | 04 | r | r |
| 9281 | SOL 4: Wärmemenge gesamt | `SOL.waermemenge_gesamt_kwh` | u32 | 04 | r | r |
| 9283 | SOL 5: Wärmemenge gesamt | `SOL.waermemenge_gesamt_kwh` | u32 | 04 | r | r |
| 9285 | SOL 6: Wärmemenge gesamt | `SOL.waermemenge_gesamt_kwh` | u32 | 04 | r | r |
| 9287 | SOL 7: Wärmemenge gesamt | `SOL.waermemenge_gesamt_kwh` | u32 | 04 | r | r |
| 9289 | SOL 8: Wärmemenge gesamt | `SOL.waermemenge_gesamt_kwh` | u32 | 04 | r | r |
| 9291 | SOL 9: Wärmemenge gesamt | `SOL.waermemenge_gesamt_kwh` | u32 | 04 | r | r |
| 9293 | SOL 10: Wärmemenge gesamt | `SOL.waermemenge_gesamt_kwh` | u32 | 04 | r | r |
| 9295 | SOL 11: Wärmemenge gesamt | `SOL.waermemenge_gesamt_kwh` | u32 | 04 | r | r |
| 9297 | SOL 12: Wärmemenge gesamt | `SOL.waermemenge_gesamt_kwh` | u32 | 04 | r | r |
| 9299 | SOL 13: Wärmemenge gesamt | `SOL.waermemenge_gesamt_kwh` | u32 | 04 | r | r |
| 9301 | SOL 14: Wärmemenge gesamt | `SOL.waermemenge_gesamt_kwh` | u32 | 04 | r | r |
| 9305 | SOL 1: Kollektor Vorlauftemperatur (value) | `SOL.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 9306 | SOL 1: Kollektor Vorlauftemperatur (status) | `SOL.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 9307 | SOL 2: Kollektor Vorlauftemperatur (value) | `SOL.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 9308 | SOL 2: Kollektor Vorlauftemperatur (status) | `SOL.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 9309 | SOL 3: Kollektor Vorlauftemperatur (value) | `SOL.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 9310 | SOL 3: Kollektor Vorlauftemperatur (status) | `SOL.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 9311 | SOL 4: Kollektor Vorlauftemperatur (value) | `SOL.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 9312 | SOL 4: Kollektor Vorlauftemperatur (status) | `SOL.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 9313 | SOL 5: Kollektor Vorlauftemperatur (value) | `SOL.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 9314 | SOL 5: Kollektor Vorlauftemperatur (status) | `SOL.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 9315 | SOL 6: Kollektor Vorlauftemperatur (value) | `SOL.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 9316 | SOL 6: Kollektor Vorlauftemperatur (status) | `SOL.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 9317 | SOL 7: Kollektor Vorlauftemperatur (value) | `SOL.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 9318 | SOL 7: Kollektor Vorlauftemperatur (status) | `SOL.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 9319 | SOL 8: Kollektor Vorlauftemperatur (value) | `SOL.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 9320 | SOL 8: Kollektor Vorlauftemperatur (status) | `SOL.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 9321 | SOL 9: Kollektor Vorlauftemperatur (value) | `SOL.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 9322 | SOL 9: Kollektor Vorlauftemperatur (status) | `SOL.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 9323 | SOL 10: Kollektor Vorlauftemperatur (value) | `SOL.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 9324 | SOL 10: Kollektor Vorlauftemperatur (status) | `SOL.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 9325 | SOL 11: Kollektor Vorlauftemperatur (value) | `SOL.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 9326 | SOL 11: Kollektor Vorlauftemperatur (status) | `SOL.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 9327 | SOL 12: Kollektor Vorlauftemperatur (value) | `SOL.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 9328 | SOL 12: Kollektor Vorlauftemperatur (status) | `SOL.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 9329 | SOL 13: Kollektor Vorlauftemperatur (value) | `SOL.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 9330 | SOL 13: Kollektor Vorlauftemperatur (status) | `SOL.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 9331 | SOL 14: Kollektor Vorlauftemperatur (value) | `SOL.i_vorlauf_temperatur.value` | s16 | 04 | r | r |
| 9332 | SOL 14: Kollektor Vorlauftemperatur (status) | `SOL.i_vorlauf_temperatur.status` | s16 | 04 | r | r |
| 9335 | SOL 1: Kollektor Rücklauftemperatur (value) | `SOL.i_kollektor_ruecklauf_temperatur.value` | s16 | 04 | r | r |
| 9336 | SOL 1: Kollektor Rücklauftemperatur (status) | `SOL.i_kollektor_ruecklauf_temperatur.status` | s16 | 04 | r | r |
| 9337 | SOL 2: Kollektor Rücklauftemperatur (value) | `SOL.i_kollektor_ruecklauf_temperatur.value` | s16 | 04 | r | r |
| 9338 | SOL 2: Kollektor Rücklauftemperatur (status) | `SOL.i_kollektor_ruecklauf_temperatur.status` | s16 | 04 | r | r |
| 9339 | SOL 3: Kollektor Rücklauftemperatur (value) | `SOL.i_kollektor_ruecklauf_temperatur.value` | s16 | 04 | r | r |
| 9340 | SOL 3: Kollektor Rücklauftemperatur (status) | `SOL.i_kollektor_ruecklauf_temperatur.status` | s16 | 04 | r | r |
| 9341 | SOL 4: Kollektor Rücklauftemperatur (value) | `SOL.i_kollektor_ruecklauf_temperatur.value` | s16 | 04 | r | r |
| 9342 | SOL 4: Kollektor Rücklauftemperatur (status) | `SOL.i_kollektor_ruecklauf_temperatur.status` | s16 | 04 | r | r |
| 9343 | SOL 5: Kollektor Rücklauftemperatur (value) | `SOL.i_kollektor_ruecklauf_temperatur.value` | s16 | 04 | r | r |
| 9344 | SOL 5: Kollektor Rücklauftemperatur (status) | `SOL.i_kollektor_ruecklauf_temperatur.status` | s16 | 04 | r | r |
| 9345 | SOL 6: Kollektor Rücklauftemperatur (value) | `SOL.i_kollektor_ruecklauf_temperatur.value` | s16 | 04 | r | r |
| 9346 | SOL 6: Kollektor Rücklauftemperatur (status) | `SOL.i_kollektor_ruecklauf_temperatur.status` | s16 | 04 | r | r |
| 9347 | SOL 7: Kollektor Rücklauftemperatur (value) | `SOL.i_kollektor_ruecklauf_temperatur.value` | s16 | 04 | r | r |
| 9348 | SOL 7: Kollektor Rücklauftemperatur (status) | `SOL.i_kollektor_ruecklauf_temperatur.status` | s16 | 04 | r | r |
| 9349 | SOL 8: Kollektor Rücklauftemperatur (value) | `SOL.i_kollektor_ruecklauf_temperatur.value` | s16 | 04 | r | r |
| 9350 | SOL 8: Kollektor Rücklauftemperatur (status) | `SOL.i_kollektor_ruecklauf_temperatur.status` | s16 | 04 | r | r |
| 9351 | SOL 9: Kollektor Rücklauftemperatur (value) | `SOL.i_kollektor_ruecklauf_temperatur.value` | s16 | 04 | r | r |
| 9352 | SOL 9: Kollektor Rücklauftemperatur (status) | `SOL.i_kollektor_ruecklauf_temperatur.status` | s16 | 04 | r | r |
| 9353 | SOL 10: Kollektor Rücklauftemperatur (value) | `SOL.i_kollektor_ruecklauf_temperatur.value` | s16 | 04 | r | r |
| 9354 | SOL 10: Kollektor Rücklauftemperatur (status) | `SOL.i_kollektor_ruecklauf_temperatur.status` | s16 | 04 | r | r |
| 9355 | SOL 11: Kollektor Rücklauftemperatur (value) | `SOL.i_kollektor_ruecklauf_temperatur.value` | s16 | 04 | r | r |
| 9356 | SOL 11: Kollektor Rücklauftemperatur (status) | `SOL.i_kollektor_ruecklauf_temperatur.status` | s16 | 04 | r | r |
| 9357 | SOL 12: Kollektor Rücklauftemperatur (value) | `SOL.i_kollektor_ruecklauf_temperatur.value` | s16 | 04 | r | r |
| 9358 | SOL 12: Kollektor Rücklauftemperatur (status) | `SOL.i_kollektor_ruecklauf_temperatur.status` | s16 | 04 | r | r |
| 9359 | SOL 13: Kollektor Rücklauftemperatur (value) | `SOL.i_kollektor_ruecklauf_temperatur.value` | s16 | 04 | r | r |
| 9360 | SOL 13: Kollektor Rücklauftemperatur (status) | `SOL.i_kollektor_ruecklauf_temperatur.status` | s16 | 04 | r | r |
| 9361 | SOL 14: Kollektor Rücklauftemperatur (value) | `SOL.i_kollektor_ruecklauf_temperatur.value` | s16 | 04 | r | r |
| 9362 | SOL 14: Kollektor Rücklauftemperatur (status) | `SOL.i_kollektor_ruecklauf_temperatur.status` | s16 | 04 | r | r |
| 9365 | SOL 1: Durchfluss (value) | `SOL.i_kollektor_durchfluss.value` | s16 | 04 | r | r |
| 9366 | SOL 1: Durchfluss (status) | `SOL.i_kollektor_durchfluss.status` | s16 | 04 | r | r |
| 9367 | SOL 2: Durchfluss (value) | `SOL.i_kollektor_durchfluss.value` | s16 | 04 | r | r |
| 9368 | SOL 2: Durchfluss (status) | `SOL.i_kollektor_durchfluss.status` | s16 | 04 | r | r |
| 9369 | SOL 3: Durchfluss (value) | `SOL.i_kollektor_durchfluss.value` | s16 | 04 | r | r |
| 9370 | SOL 3: Durchfluss (status) | `SOL.i_kollektor_durchfluss.status` | s16 | 04 | r | r |
| 9371 | SOL 4: Durchfluss (value) | `SOL.i_kollektor_durchfluss.value` | s16 | 04 | r | r |
| 9372 | SOL 4: Durchfluss (status) | `SOL.i_kollektor_durchfluss.status` | s16 | 04 | r | r |
| 9373 | SOL 5: Durchfluss (value) | `SOL.i_kollektor_durchfluss.value` | s16 | 04 | r | r |
| 9374 | SOL 5: Durchfluss (status) | `SOL.i_kollektor_durchfluss.status` | s16 | 04 | r | r |
| 9375 | SOL 6: Durchfluss (value) | `SOL.i_kollektor_durchfluss.value` | s16 | 04 | r | r |
| 9376 | SOL 6: Durchfluss (status) | `SOL.i_kollektor_durchfluss.status` | s16 | 04 | r | r |
| 9377 | SOL 7: Durchfluss (value) | `SOL.i_kollektor_durchfluss.value` | s16 | 04 | r | r |
| 9378 | SOL 7: Durchfluss (status) | `SOL.i_kollektor_durchfluss.status` | s16 | 04 | r | r |
| 9379 | SOL 8: Durchfluss (value) | `SOL.i_kollektor_durchfluss.value` | s16 | 04 | r | r |
| 9380 | SOL 8: Durchfluss (status) | `SOL.i_kollektor_durchfluss.status` | s16 | 04 | r | r |
| 9381 | SOL 9: Durchfluss (value) | `SOL.i_kollektor_durchfluss.value` | s16 | 04 | r | r |
| 9382 | SOL 9: Durchfluss (status) | `SOL.i_kollektor_durchfluss.status` | s16 | 04 | r | r |
| 9383 | SOL 10: Durchfluss (value) | `SOL.i_kollektor_durchfluss.value` | s16 | 04 | r | r |
| 9384 | SOL 10: Durchfluss (status) | `SOL.i_kollektor_durchfluss.status` | s16 | 04 | r | r |
| 9385 | SOL 11: Durchfluss (value) | `SOL.i_kollektor_durchfluss.value` | s16 | 04 | r | r |
| 9386 | SOL 11: Durchfluss (status) | `SOL.i_kollektor_durchfluss.status` | s16 | 04 | r | r |
| 9387 | SOL 12: Durchfluss (value) | `SOL.i_kollektor_durchfluss.value` | s16 | 04 | r | r |
| 9388 | SOL 12: Durchfluss (status) | `SOL.i_kollektor_durchfluss.status` | s16 | 04 | r | r |
| 9389 | SOL 13: Durchfluss (value) | `SOL.i_kollektor_durchfluss.value` | s16 | 04 | r | r |
| 9390 | SOL 13: Durchfluss (status) | `SOL.i_kollektor_durchfluss.status` | s16 | 04 | r | r |
| 9391 | SOL 14: Durchfluss (value) | `SOL.i_kollektor_durchfluss.value` | s16 | 04 | r | r |
| 9392 | SOL 14: Durchfluss (status) | `SOL.i_kollektor_durchfluss.status` | s16 | 04 | r | r |
| 9466 | SOL 1: Pumpe 1 | `SOL.pumpe_1_steuerstufe` | u16 | 04 | r | r |
| 9467 | SOL 2: Pumpe 1 | `SOL.pumpe_1_steuerstufe` | u16 | 04 | r | r |
| 9468 | SOL 3: Pumpe 1 | `SOL.pumpe_1_steuerstufe` | u16 | 04 | r | r |
| 9469 | SOL 4: Pumpe 1 | `SOL.pumpe_1_steuerstufe` | u16 | 04 | r | r |
| 9470 | SOL 5: Pumpe 1 | `SOL.pumpe_1_steuerstufe` | u16 | 04 | r | r |
| 9471 | SOL 6: Pumpe 1 | `SOL.pumpe_1_steuerstufe` | u16 | 04 | r | r |
| 9472 | SOL 7: Pumpe 1 | `SOL.pumpe_1_steuerstufe` | u16 | 04 | r | r |
| 9473 | SOL 8: Pumpe 1 | `SOL.pumpe_1_steuerstufe` | u16 | 04 | r | r |
| 9474 | SOL 9: Pumpe 1 | `SOL.pumpe_1_steuerstufe` | u16 | 04 | r | r |
| 9475 | SOL 10: Pumpe 1 | `SOL.pumpe_1_steuerstufe` | u16 | 04 | r | r |
| 9476 | SOL 11: Pumpe 1 | `SOL.pumpe_1_steuerstufe` | u16 | 04 | r | r |
| 9477 | SOL 12: Pumpe 1 | `SOL.pumpe_1_steuerstufe` | u16 | 04 | r | r |
| 9478 | SOL 13: Pumpe 1 | `SOL.pumpe_1_steuerstufe` | u16 | 04 | r | r |
| 9479 | SOL 14: Pumpe 1 | `SOL.pumpe_1_steuerstufe` | u16 | 04 | r | r |
| 9481 | SOL 1: Pumpe 2 | `SOL.pumpe_2_steuerstufe` | u16 | 04 | r | r |
| 9482 | SOL 2: Pumpe 2 | `SOL.pumpe_2_steuerstufe` | u16 | 04 | r | r |
| 9483 | SOL 3: Pumpe 2 | `SOL.pumpe_2_steuerstufe` | u16 | 04 | r | r |
| 9484 | SOL 4: Pumpe 2 | `SOL.pumpe_2_steuerstufe` | u16 | 04 | r | r |
| 9485 | SOL 5: Pumpe 2 | `SOL.pumpe_2_steuerstufe` | u16 | 04 | r | r |
| 9486 | SOL 6: Pumpe 2 | `SOL.pumpe_2_steuerstufe` | u16 | 04 | r | r |
| 9487 | SOL 7: Pumpe 2 | `SOL.pumpe_2_steuerstufe` | u16 | 04 | r | r |
| 9488 | SOL 8: Pumpe 2 | `SOL.pumpe_2_steuerstufe` | u16 | 04 | r | r |
| 9489 | SOL 9: Pumpe 2 | `SOL.pumpe_2_steuerstufe` | u16 | 04 | r | r |
| 9490 | SOL 10: Pumpe 2 | `SOL.pumpe_2_steuerstufe` | u16 | 04 | r | r |
| 9491 | SOL 11: Pumpe 2 | `SOL.pumpe_2_steuerstufe` | u16 | 04 | r | r |
| 9492 | SOL 12: Pumpe 2 | `SOL.pumpe_2_steuerstufe` | u16 | 04 | r | r |
| 9493 | SOL 13: Pumpe 2 | `SOL.pumpe_2_steuerstufe` | u16 | 04 | r | r |
| 9494 | SOL 14: Pumpe 2 | `SOL.pumpe_2_steuerstufe` | u16 | 04 | r | r |
| 9882 | SOL 1: Vorlauftemperatur Sekundär (value) | `SOL.i_vorlauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9883 | SOL 1: Vorlauftemperatur Sekundär (status) | `SOL.i_vorlauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9884 | SOL 2: Vorlauftemperatur Sekundär (value) | `SOL.i_vorlauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9885 | SOL 2: Vorlauftemperatur Sekundär (status) | `SOL.i_vorlauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9886 | SOL 3: Vorlauftemperatur Sekundär (value) | `SOL.i_vorlauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9887 | SOL 3: Vorlauftemperatur Sekundär (status) | `SOL.i_vorlauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9888 | SOL 4: Vorlauftemperatur Sekundär (value) | `SOL.i_vorlauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9889 | SOL 4: Vorlauftemperatur Sekundär (status) | `SOL.i_vorlauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9890 | SOL 5: Vorlauftemperatur Sekundär (value) | `SOL.i_vorlauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9891 | SOL 5: Vorlauftemperatur Sekundär (status) | `SOL.i_vorlauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9892 | SOL 6: Vorlauftemperatur Sekundär (value) | `SOL.i_vorlauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9893 | SOL 6: Vorlauftemperatur Sekundär (status) | `SOL.i_vorlauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9894 | SOL 7: Vorlauftemperatur Sekundär (value) | `SOL.i_vorlauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9895 | SOL 7: Vorlauftemperatur Sekundär (status) | `SOL.i_vorlauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9896 | SOL 8: Vorlauftemperatur Sekundär (value) | `SOL.i_vorlauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9897 | SOL 8: Vorlauftemperatur Sekundär (status) | `SOL.i_vorlauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9898 | SOL 9: Vorlauftemperatur Sekundär (value) | `SOL.i_vorlauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9899 | SOL 9: Vorlauftemperatur Sekundär (status) | `SOL.i_vorlauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9900 | SOL 10: Vorlauftemperatur Sekundär (value) | `SOL.i_vorlauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9901 | SOL 10: Vorlauftemperatur Sekundär (status) | `SOL.i_vorlauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9902 | SOL 11: Vorlauftemperatur Sekundär (value) | `SOL.i_vorlauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9903 | SOL 11: Vorlauftemperatur Sekundär (status) | `SOL.i_vorlauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9904 | SOL 12: Vorlauftemperatur Sekundär (value) | `SOL.i_vorlauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9905 | SOL 12: Vorlauftemperatur Sekundär (status) | `SOL.i_vorlauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9906 | SOL 13: Vorlauftemperatur Sekundär (value) | `SOL.i_vorlauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9907 | SOL 13: Vorlauftemperatur Sekundär (status) | `SOL.i_vorlauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9908 | SOL 14: Vorlauftemperatur Sekundär (value) | `SOL.i_vorlauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9909 | SOL 14: Vorlauftemperatur Sekundär (status) | `SOL.i_vorlauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9912 | SOL 1: Rücklauftemperatur Sekundär (value) | `SOL.i_ruecklauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9913 | SOL 1: Rücklauftemperatur Sekundär (status) | `SOL.i_ruecklauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9914 | SOL 2: Rücklauftemperatur Sekundär (value) | `SOL.i_ruecklauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9915 | SOL 2: Rücklauftemperatur Sekundär (status) | `SOL.i_ruecklauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9916 | SOL 3: Rücklauftemperatur Sekundär (value) | `SOL.i_ruecklauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9917 | SOL 3: Rücklauftemperatur Sekundär (status) | `SOL.i_ruecklauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9918 | SOL 4: Rücklauftemperatur Sekundär (value) | `SOL.i_ruecklauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9919 | SOL 4: Rücklauftemperatur Sekundär (status) | `SOL.i_ruecklauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9920 | SOL 5: Rücklauftemperatur Sekundär (value) | `SOL.i_ruecklauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9921 | SOL 5: Rücklauftemperatur Sekundär (status) | `SOL.i_ruecklauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9922 | SOL 6: Rücklauftemperatur Sekundär (value) | `SOL.i_ruecklauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9923 | SOL 6: Rücklauftemperatur Sekundär (status) | `SOL.i_ruecklauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9924 | SOL 7: Rücklauftemperatur Sekundär (value) | `SOL.i_ruecklauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9925 | SOL 7: Rücklauftemperatur Sekundär (status) | `SOL.i_ruecklauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9926 | SOL 8: Rücklauftemperatur Sekundär (value) | `SOL.i_ruecklauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9927 | SOL 8: Rücklauftemperatur Sekundär (status) | `SOL.i_ruecklauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9928 | SOL 9: Rücklauftemperatur Sekundär (value) | `SOL.i_ruecklauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9929 | SOL 9: Rücklauftemperatur Sekundär (status) | `SOL.i_ruecklauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9930 | SOL 10: Rücklauftemperatur Sekundär (value) | `SOL.i_ruecklauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9931 | SOL 10: Rücklauftemperatur Sekundär (status) | `SOL.i_ruecklauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9932 | SOL 11: Rücklauftemperatur Sekundär (value) | `SOL.i_ruecklauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9933 | SOL 11: Rücklauftemperatur Sekundär (status) | `SOL.i_ruecklauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9934 | SOL 12: Rücklauftemperatur Sekundär (value) | `SOL.i_ruecklauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9935 | SOL 12: Rücklauftemperatur Sekundär (status) | `SOL.i_ruecklauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9936 | SOL 13: Rücklauftemperatur Sekundär (value) | `SOL.i_ruecklauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9937 | SOL 13: Rücklauftemperatur Sekundär (status) | `SOL.i_ruecklauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9938 | SOL 14: Rücklauftemperatur Sekundär (value) | `SOL.i_ruecklauf_temperatur_sekundaer.value` | s16 | 04 | r | r |
| 9939 | SOL 14: Rücklauftemperatur Sekundär (status) | `SOL.i_ruecklauf_temperatur_sekundaer.status` | s16 | 04 | r | r |
| 9942 | SOL 1: Rücklauftemperatur Primär (value) | `SOL.i_ruecklauf_temperatur_primaer.value` | s16 | 04 | r | r |
| 9943 | SOL 1: Rücklauftemperatur Primär (status) | `SOL.i_ruecklauf_temperatur_primaer.status` | s16 | 04 | r | r |
| 9944 | SOL 2: Rücklauftemperatur Primär (value) | `SOL.i_ruecklauf_temperatur_primaer.value` | s16 | 04 | r | r |
| 9945 | SOL 2: Rücklauftemperatur Primär (status) | `SOL.i_ruecklauf_temperatur_primaer.status` | s16 | 04 | r | r |
| 9946 | SOL 3: Rücklauftemperatur Primär (value) | `SOL.i_ruecklauf_temperatur_primaer.value` | s16 | 04 | r | r |
| 9947 | SOL 3: Rücklauftemperatur Primär (status) | `SOL.i_ruecklauf_temperatur_primaer.status` | s16 | 04 | r | r |
| 9948 | SOL 4: Rücklauftemperatur Primär (value) | `SOL.i_ruecklauf_temperatur_primaer.value` | s16 | 04 | r | r |
| 9949 | SOL 4: Rücklauftemperatur Primär (status) | `SOL.i_ruecklauf_temperatur_primaer.status` | s16 | 04 | r | r |
| 9950 | SOL 5: Rücklauftemperatur Primär (value) | `SOL.i_ruecklauf_temperatur_primaer.value` | s16 | 04 | r | r |
| 9951 | SOL 5: Rücklauftemperatur Primär (status) | `SOL.i_ruecklauf_temperatur_primaer.status` | s16 | 04 | r | r |
| 9952 | SOL 6: Rücklauftemperatur Primär (value) | `SOL.i_ruecklauf_temperatur_primaer.value` | s16 | 04 | r | r |
| 9953 | SOL 6: Rücklauftemperatur Primär (status) | `SOL.i_ruecklauf_temperatur_primaer.status` | s16 | 04 | r | r |
| 9954 | SOL 7: Rücklauftemperatur Primär (value) | `SOL.i_ruecklauf_temperatur_primaer.value` | s16 | 04 | r | r |
| 9955 | SOL 7: Rücklauftemperatur Primär (status) | `SOL.i_ruecklauf_temperatur_primaer.status` | s16 | 04 | r | r |
| 9956 | SOL 8: Rücklauftemperatur Primär (value) | `SOL.i_ruecklauf_temperatur_primaer.value` | s16 | 04 | r | r |
| 9957 | SOL 8: Rücklauftemperatur Primär (status) | `SOL.i_ruecklauf_temperatur_primaer.status` | s16 | 04 | r | r |
| 9958 | SOL 9: Rücklauftemperatur Primär (value) | `SOL.i_ruecklauf_temperatur_primaer.value` | s16 | 04 | r | r |
| 9959 | SOL 9: Rücklauftemperatur Primär (status) | `SOL.i_ruecklauf_temperatur_primaer.status` | s16 | 04 | r | r |
| 9960 | SOL 10: Rücklauftemperatur Primär (value) | `SOL.i_ruecklauf_temperatur_primaer.value` | s16 | 04 | r | r |
| 9961 | SOL 10: Rücklauftemperatur Primär (status) | `SOL.i_ruecklauf_temperatur_primaer.status` | s16 | 04 | r | r |
| 9962 | SOL 11: Rücklauftemperatur Primär (value) | `SOL.i_ruecklauf_temperatur_primaer.value` | s16 | 04 | r | r |
| 9963 | SOL 11: Rücklauftemperatur Primär (status) | `SOL.i_ruecklauf_temperatur_primaer.status` | s16 | 04 | r | r |
| 9964 | SOL 12: Rücklauftemperatur Primär (value) | `SOL.i_ruecklauf_temperatur_primaer.value` | s16 | 04 | r | r |
| 9965 | SOL 12: Rücklauftemperatur Primär (status) | `SOL.i_ruecklauf_temperatur_primaer.status` | s16 | 04 | r | r |
| 9966 | SOL 13: Rücklauftemperatur Primär (value) | `SOL.i_ruecklauf_temperatur_primaer.value` | s16 | 04 | r | r |
| 9967 | SOL 13: Rücklauftemperatur Primär (status) | `SOL.i_ruecklauf_temperatur_primaer.status` | s16 | 04 | r | r |
| 9968 | SOL 14: Rücklauftemperatur Primär (value) | `SOL.i_ruecklauf_temperatur_primaer.value` | s16 | 04 | r | r |
| 9969 | SOL 14: Rücklauftemperatur Primär (status) | `SOL.i_ruecklauf_temperatur_primaer.status` | s16 | 04 | r | r |
| 25009 | SOL 1: Modbus Vorlauftemp. Soll | `SOL.modbus_vorlauf_temperatur_soll` | s16 | 03 | r | rw |
| 25010 | SOL 2: Modbus Vorlauftemp. Soll | `SOL.modbus_vorlauf_temperatur_soll` | s16 | 03 | r | rw |
| 25011 | SOL 3: Modbus Vorlauftemp. Soll | `SOL.modbus_vorlauf_temperatur_soll` | s16 | 03 | r | rw |
| 25012 | SOL 4: Modbus Vorlauftemp. Soll | `SOL.modbus_vorlauf_temperatur_soll` | s16 | 03 | r | rw |
| 25013 | SOL 5: Modbus Vorlauftemp. Soll | `SOL.modbus_vorlauf_temperatur_soll` | s16 | 03 | r | rw |
| 25014 | SOL 6: Modbus Vorlauftemp. Soll | `SOL.modbus_vorlauf_temperatur_soll` | s16 | 03 | r | rw |
| 25015 | SOL 7: Modbus Vorlauftemp. Soll | `SOL.modbus_vorlauf_temperatur_soll` | s16 | 03 | r | rw |
| 25016 | SOL 8: Modbus Vorlauftemp. Soll | `SOL.modbus_vorlauf_temperatur_soll` | s16 | 03 | r | rw |
| 25017 | SOL 9: Modbus Vorlauftemp. Soll | `SOL.modbus_vorlauf_temperatur_soll` | s16 | 03 | r | rw |
| 25018 | SOL 10: Modbus Vorlauftemp. Soll | `SOL.modbus_vorlauf_temperatur_soll` | s16 | 03 | r | rw |
| 25019 | SOL 11: Modbus Vorlauftemp. Soll | `SOL.modbus_vorlauf_temperatur_soll` | s16 | 03 | r | rw |
| 25020 | SOL 12: Modbus Vorlauftemp. Soll | `SOL.modbus_vorlauf_temperatur_soll` | s16 | 03 | r | rw |
| 25021 | SOL 13: Modbus Vorlauftemp. Soll | `SOL.modbus_vorlauf_temperatur_soll` | s16 | 03 | r | rw |
| 25022 | SOL 14: Modbus Vorlauftemp. Soll | `SOL.modbus_vorlauf_temperatur_soll` | s16 | 03 | r | rw |

### Kesselfolgeschaltung (`boiler_sequence.json`, 45 Register)

| Adresse | Name (mit Slot) | Parameter | Typ | FC | User | Expert |
|---:|---|---|---|:---:|:---:|:---:|
| 9394 | Mittlere Puffertemp. | `KFS.mittlere_puffertemperatur` | s16 | 04 | r | r |
| 9395 | Pufferfüllgrad | `KFS.puffer_fuellgrad` | s16 | 04 | r | r |
| 9396 | Netzvorlauf (value) | `KFS.netz_vorlauf.value` | s16 | 04 | r | r |
| 9397 | Netzvorlauf (status) | `KFS.netz_vorlauf.status` | s16 | 04 | r | r |
| 9398 | Netzrücklauf (value) | `KFS.netz_ruecklauf.value` | s16 | 04 | r | r |
| 9399 | Netzrücklauf (status) | `KFS.netz_ruecklauf.status` | s16 | 04 | r | r |
| 9400 | Anf. Spitzenlastkessel | `KFS.o_anforderung_spitzenlastkessel` | s16 | 04 | r | r |
| 9402 | KFK 1: Anforderung | `KFK.o_anforderung` | s16 | 04 | r | r |
| 9403 | KFK 2: Anforderung | `KFK.o_anforderung` | s16 | 04 | r | r |
| 9404 | KFK 3: Anforderung | `KFK.o_anforderung` | s16 | 04 | r | r |
| 9405 | KFK 4: Anforderung | `KFK.o_anforderung` | s16 | 04 | r | r |
| 9406 | KFK 5: Anforderung | `KFK.o_anforderung` | s16 | 04 | r | r |
| 9407 | KFK 6: Anforderung | `KFK.o_anforderung` | s16 | 04 | r | r |
| 9408 | KFK 7: Anforderung | `KFK.o_anforderung` | s16 | 04 | r | r |
| 9409 | KFK 8: Anforderung | `KFK.o_anforderung` | s16 | 04 | r | r |
| 9422 | KFK 1: Störung | `KFK.i_stoerung` | s16 | 04 | r | r |
| 9423 | KFK 2: Störung | `KFK.i_stoerung` | s16 | 04 | r | r |
| 9424 | KFK 3: Störung | `KFK.i_stoerung` | s16 | 04 | r | r |
| 9425 | KFK 4: Störung | `KFK.i_stoerung` | s16 | 04 | r | r |
| 9426 | KFK 5: Störung | `KFK.i_stoerung` | s16 | 04 | r | r |
| 9427 | KFK 6: Störung | `KFK.i_stoerung` | s16 | 04 | r | r |
| 9428 | KFK 7: Störung | `KFK.i_stoerung` | s16 | 04 | r | r |
| 9429 | KFK 8: Störung | `KFK.i_stoerung` | s16 | 04 | r | r |
| 9499 | Anlagen | `KFS.anzahl_kessel` | u8 | 04 | r | r |
| 9500 | Anlagen angefordert | `KFS.anzahl_angeforderte_kessel` | s16 | 04 | r | r |
| 9501 | Puffersolltemperatur | `KFS.puffer_solltemperatur_anzeige` | s16 | 04 | r | r |
| 9502 | Puffer Temperatur 1 (value) | `KFS.puffer_temperatur_1.value` | s16 | 04 | r | r |
| 9503 | Puffer Temperatur 1 (status) | `KFS.puffer_temperatur_1.status` | s16 | 04 | r | r |
| 9504 | Puffer Temperatur 2 (value) | `KFS.puffer_temperatur_2.value` | s16 | 04 | r | r |
| 9505 | Puffer Temperatur 2 (status) | `KFS.puffer_temperatur_2.status` | s16 | 04 | r | r |
| 9506 | Puffer Temperatur 3 (value) | `KFS.puffer_temperatur_3.value` | s16 | 04 | r | r |
| 9507 | Puffer Temperatur 3 (status) | `KFS.puffer_temperatur_3.status` | s16 | 04 | r | r |
| 9508 | Puffer Temperatur 4 (value) | `KFS.puffer_temperatur_4.value` | s16 | 04 | r | r |
| 9509 | Puffer Temperatur 4 (status) | `KFS.puffer_temperatur_4.status` | s16 | 04 | r | r |
| 9510 | Puffer Temperatur 5 (value) | `KFS.puffer_temperatur_5.value` | s16 | 04 | r | r |
| 9511 | Puffer Temperatur 5 (status) | `KFS.puffer_temperatur_5.status` | s16 | 04 | r | r |
| 9512 | Außentemperatur gemittelt (value) | `KFS.i_aussen_temperatur_mittelwert.value` | s16 | 04 | r | r |
| 9513 | Außentemperatur gemittelt (status) | `KFS.i_aussen_temperatur_mittelwert.status` | s16 | 04 | r | r |
| 9514 | Störkontakt Dauer | `KFS.o_stoerung_dauer` | s16 | 04 | r | r |
| 9515 | Mittlere Durchladetemp. | `KFS.mittlere_durchladetemperatur` | s16 | 04 | r | r |
| 9516 | Pufferdurchladegrad | `KFS.puffer_durchladegrad` | s16 | 04 | r | r |
| 24848 | Puffersolltemperatur Winter | `KFS.puffer_solltemperatur_winter` | s16 | 03 | rw | rw |
| 24929 | Kesselfolgeschaltung | `KFS.anlage_ein` | s16 | 03 | rw | rw |
| 24930 | Aktives Profil | `KFS.active_profile` | s16 | 03 | rw | rw |
| 24931 | Puffersolltemperatur Sommer | `KFS.puffer_solltemperatur_sommer` | s16 | 03 | rw | rw |

### Wärmemengenzähler (`heat_meters.json`, 216 Register)

| Adresse | Name (mit Slot) | Parameter | Typ | FC | User | Expert |
|---:|---|---|---|:---:|:---:|:---:|
| 9517 | WMZ 0: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9519 | WMZ 1: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9521 | WMZ 2: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9523 | WMZ 3: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9525 | WMZ 4: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9527 | WMZ 5: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9529 | WMZ 6: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9531 | WMZ 7: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9533 | WMZ 8: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9535 | WMZ 9: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9537 | WMZ 10: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9539 | WMZ 11: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9541 | WMZ 12: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9543 | WMZ 13: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9545 | WMZ 14: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9547 | WMZ 15: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9549 | WMZ 16: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9551 | WMZ 17: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9553 | WMZ 18: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9555 | WMZ 19: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9557 | WMZ 20: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9559 | WMZ 21: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9561 | WMZ 22: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9563 | WMZ 23: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9565 | WMZ 24: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9567 | WMZ 25: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9569 | WMZ 26: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9571 | WMZ 27: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9573 | WMZ 28: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9575 | WMZ 29: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9577 | WMZ 30: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9579 | WMZ 31: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9581 | WMZ 32: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9583 | WMZ 33: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9585 | WMZ 34: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9587 | WMZ 35: Leistung | `MBUS.leistung` | s32 | 04 | r | r |
| 9589 | WMZ 0: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9590 | WMZ 1: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9591 | WMZ 2: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9592 | WMZ 3: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9593 | WMZ 4: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9594 | WMZ 5: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9595 | WMZ 6: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9596 | WMZ 7: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9597 | WMZ 8: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9598 | WMZ 9: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9599 | WMZ 10: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9600 | WMZ 11: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9601 | WMZ 12: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9602 | WMZ 13: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9603 | WMZ 14: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9604 | WMZ 15: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9605 | WMZ 16: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9606 | WMZ 17: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9607 | WMZ 18: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9608 | WMZ 19: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9609 | WMZ 20: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9610 | WMZ 21: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9611 | WMZ 22: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9612 | WMZ 23: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9613 | WMZ 24: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9614 | WMZ 25: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9615 | WMZ 26: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9616 | WMZ 27: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9617 | WMZ 28: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9618 | WMZ 29: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9619 | WMZ 30: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9620 | WMZ 31: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9621 | WMZ 32: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9622 | WMZ 33: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9623 | WMZ 34: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9624 | WMZ 35: Vorlauf | `MBUS.vorlauftemp` | s16 | 04 | r | r |
| 9625 | WMZ 0: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9626 | WMZ 1: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9627 | WMZ 2: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9628 | WMZ 3: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9629 | WMZ 4: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9630 | WMZ 5: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9631 | WMZ 6: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9632 | WMZ 7: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9633 | WMZ 8: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9634 | WMZ 9: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9635 | WMZ 10: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9636 | WMZ 11: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9637 | WMZ 12: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9638 | WMZ 13: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9639 | WMZ 14: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9640 | WMZ 15: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9641 | WMZ 16: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9642 | WMZ 17: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9643 | WMZ 18: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9644 | WMZ 19: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9645 | WMZ 20: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9646 | WMZ 21: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9647 | WMZ 22: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9648 | WMZ 23: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9649 | WMZ 24: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9650 | WMZ 25: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9651 | WMZ 26: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9652 | WMZ 27: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9653 | WMZ 28: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9654 | WMZ 29: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9655 | WMZ 30: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9656 | WMZ 31: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9657 | WMZ 32: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9658 | WMZ 33: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9659 | WMZ 34: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9660 | WMZ 35: Rücklauf | `MBUS.ruecklauftemp` | s16 | 04 | r | r |
| 9661 | WMZ 0: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9663 | WMZ 1: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9665 | WMZ 2: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9667 | WMZ 3: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9669 | WMZ 4: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9671 | WMZ 5: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9673 | WMZ 6: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9675 | WMZ 7: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9677 | WMZ 8: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9679 | WMZ 9: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9681 | WMZ 10: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9683 | WMZ 11: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9685 | WMZ 12: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9687 | WMZ 13: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9689 | WMZ 14: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9691 | WMZ 15: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9693 | WMZ 16: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9695 | WMZ 17: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9697 | WMZ 18: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9699 | WMZ 19: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9701 | WMZ 20: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9703 | WMZ 21: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9705 | WMZ 22: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9707 | WMZ 23: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9709 | WMZ 24: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9711 | WMZ 25: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9713 | WMZ 26: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9715 | WMZ 27: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9717 | WMZ 28: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9719 | WMZ 29: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9721 | WMZ 30: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9723 | WMZ 31: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9725 | WMZ 32: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9727 | WMZ 33: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9729 | WMZ 34: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9731 | WMZ 35: Energie | `MBUS.energie` | u32 | 04 | r | r |
| 9733 | WMZ 0: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9735 | WMZ 1: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9737 | WMZ 2: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9739 | WMZ 3: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9741 | WMZ 4: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9743 | WMZ 5: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9745 | WMZ 6: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9747 | WMZ 7: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9749 | WMZ 8: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9751 | WMZ 9: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9753 | WMZ 10: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9755 | WMZ 11: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9757 | WMZ 12: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9759 | WMZ 13: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9761 | WMZ 14: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9763 | WMZ 15: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9765 | WMZ 16: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9767 | WMZ 17: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9769 | WMZ 18: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9771 | WMZ 19: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9773 | WMZ 20: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9775 | WMZ 21: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9777 | WMZ 22: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9779 | WMZ 23: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9781 | WMZ 24: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9783 | WMZ 25: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9785 | WMZ 26: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9787 | WMZ 27: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9789 | WMZ 28: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9791 | WMZ 29: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9793 | WMZ 30: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9795 | WMZ 31: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9797 | WMZ 32: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9799 | WMZ 33: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9801 | WMZ 34: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9803 | WMZ 35: Volumen akt. | `MBUS.vol_akt` | s32 | 04 | r | r |
| 9805 | WMZ 0: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9807 | WMZ 1: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9809 | WMZ 2: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9811 | WMZ 3: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9813 | WMZ 4: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9815 | WMZ 5: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9817 | WMZ 6: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9819 | WMZ 7: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9821 | WMZ 8: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9823 | WMZ 9: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9825 | WMZ 10: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9827 | WMZ 11: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9829 | WMZ 12: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9831 | WMZ 13: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9833 | WMZ 14: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9835 | WMZ 15: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9837 | WMZ 16: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9839 | WMZ 17: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9841 | WMZ 18: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9843 | WMZ 19: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9845 | WMZ 20: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9847 | WMZ 21: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9849 | WMZ 22: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9851 | WMZ 23: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9853 | WMZ 24: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9855 | WMZ 25: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9857 | WMZ 26: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9859 | WMZ 27: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9861 | WMZ 28: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9863 | WMZ 29: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9865 | WMZ 30: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9867 | WMZ 31: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9869 | WMZ 32: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9871 | WMZ 33: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9873 | WMZ 34: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |
| 9875 | WMZ 35: Volumen ges. | `MBUS.vol_ges` | s32 | 04 | r | r |

### Übergabestation (`transfer_station.json`, 168 Register)

| Adresse | Name (mit Slot) | Parameter | Typ | FC | User | Expert |
|---:|---|---|---|:---:|:---:|:---:|
| 10463 | ÜGS 1: Status | `UEBERGABE.uegs_status` | s16 | 04 | r | r |
| 10464 | ÜGS 2: Status | `UEBERGABE.uegs_status` | s16 | 04 | r | r |
| 10465 | ÜGS 3: Status | `UEBERGABE.uegs_status` | s16 | 04 | r | r |
| 10466 | ÜGS 4: Status | `UEBERGABE.uegs_status` | s16 | 04 | r | r |
| 10467 | ÜGS 5: Status | `UEBERGABE.uegs_status` | s16 | 04 | r | r |
| 10468 | ÜGS 6: Status | `UEBERGABE.uegs_status` | s16 | 04 | r | r |
| 10469 | ÜGS 7: Status | `UEBERGABE.uegs_status` | s16 | 04 | r | r |
| 10470 | ÜGS 8: Status | `UEBERGABE.uegs_status` | s16 | 04 | r | r |
| 10471 | ÜGS 9: Status | `UEBERGABE.uegs_status` | s16 | 04 | r | r |
| 10472 | ÜGS 10: Status | `UEBERGABE.uegs_status` | s16 | 04 | r | r |
| 10473 | ÜGS 11: Status | `UEBERGABE.uegs_status` | s16 | 04 | r | r |
| 10474 | ÜGS 12: Status | `UEBERGABE.uegs_status` | s16 | 04 | r | r |
| 10475 | ÜGS 13: Status | `UEBERGABE.uegs_status` | s16 | 04 | r | r |
| 10476 | ÜGS 14: Status | `UEBERGABE.uegs_status` | s16 | 04 | r | r |
| 10479 | ÜGS 1: Vorlauftemperatur Sekundär (value) | `UEBERGABE.vorlauftemp_sekundaer_ist.value` | s16 | 04 | r | r |
| 10480 | ÜGS 1: Vorlauftemperatur Sekundär (status) | `UEBERGABE.vorlauftemp_sekundaer_ist.status` | s16 | 04 | r | r |
| 10481 | ÜGS 2: Vorlauftemperatur Sekundär (value) | `UEBERGABE.vorlauftemp_sekundaer_ist.value` | s16 | 04 | r | r |
| 10482 | ÜGS 2: Vorlauftemperatur Sekundär (status) | `UEBERGABE.vorlauftemp_sekundaer_ist.status` | s16 | 04 | r | r |
| 10483 | ÜGS 3: Vorlauftemperatur Sekundär (value) | `UEBERGABE.vorlauftemp_sekundaer_ist.value` | s16 | 04 | r | r |
| 10484 | ÜGS 3: Vorlauftemperatur Sekundär (status) | `UEBERGABE.vorlauftemp_sekundaer_ist.status` | s16 | 04 | r | r |
| 10485 | ÜGS 4: Vorlauftemperatur Sekundär (value) | `UEBERGABE.vorlauftemp_sekundaer_ist.value` | s16 | 04 | r | r |
| 10486 | ÜGS 4: Vorlauftemperatur Sekundär (status) | `UEBERGABE.vorlauftemp_sekundaer_ist.status` | s16 | 04 | r | r |
| 10487 | ÜGS 5: Vorlauftemperatur Sekundär (value) | `UEBERGABE.vorlauftemp_sekundaer_ist.value` | s16 | 04 | r | r |
| 10488 | ÜGS 5: Vorlauftemperatur Sekundär (status) | `UEBERGABE.vorlauftemp_sekundaer_ist.status` | s16 | 04 | r | r |
| 10489 | ÜGS 6: Vorlauftemperatur Sekundär (value) | `UEBERGABE.vorlauftemp_sekundaer_ist.value` | s16 | 04 | r | r |
| 10490 | ÜGS 6: Vorlauftemperatur Sekundär (status) | `UEBERGABE.vorlauftemp_sekundaer_ist.status` | s16 | 04 | r | r |
| 10491 | ÜGS 7: Vorlauftemperatur Sekundär (value) | `UEBERGABE.vorlauftemp_sekundaer_ist.value` | s16 | 04 | r | r |
| 10492 | ÜGS 7: Vorlauftemperatur Sekundär (status) | `UEBERGABE.vorlauftemp_sekundaer_ist.status` | s16 | 04 | r | r |
| 10493 | ÜGS 8: Vorlauftemperatur Sekundär (value) | `UEBERGABE.vorlauftemp_sekundaer_ist.value` | s16 | 04 | r | r |
| 10494 | ÜGS 8: Vorlauftemperatur Sekundär (status) | `UEBERGABE.vorlauftemp_sekundaer_ist.status` | s16 | 04 | r | r |
| 10495 | ÜGS 9: Vorlauftemperatur Sekundär (value) | `UEBERGABE.vorlauftemp_sekundaer_ist.value` | s16 | 04 | r | r |
| 10496 | ÜGS 9: Vorlauftemperatur Sekundär (status) | `UEBERGABE.vorlauftemp_sekundaer_ist.status` | s16 | 04 | r | r |
| 10497 | ÜGS 10: Vorlauftemperatur Sekundär (value) | `UEBERGABE.vorlauftemp_sekundaer_ist.value` | s16 | 04 | r | r |
| 10498 | ÜGS 10: Vorlauftemperatur Sekundär (status) | `UEBERGABE.vorlauftemp_sekundaer_ist.status` | s16 | 04 | r | r |
| 10499 | ÜGS 11: Vorlauftemperatur Sekundär (value) | `UEBERGABE.vorlauftemp_sekundaer_ist.value` | s16 | 04 | r | r |
| 10500 | ÜGS 11: Vorlauftemperatur Sekundär (status) | `UEBERGABE.vorlauftemp_sekundaer_ist.status` | s16 | 04 | r | r |
| 10501 | ÜGS 12: Vorlauftemperatur Sekundär (value) | `UEBERGABE.vorlauftemp_sekundaer_ist.value` | s16 | 04 | r | r |
| 10502 | ÜGS 12: Vorlauftemperatur Sekundär (status) | `UEBERGABE.vorlauftemp_sekundaer_ist.status` | s16 | 04 | r | r |
| 10503 | ÜGS 13: Vorlauftemperatur Sekundär (value) | `UEBERGABE.vorlauftemp_sekundaer_ist.value` | s16 | 04 | r | r |
| 10504 | ÜGS 13: Vorlauftemperatur Sekundär (status) | `UEBERGABE.vorlauftemp_sekundaer_ist.status` | s16 | 04 | r | r |
| 10505 | ÜGS 14: Vorlauftemperatur Sekundär (value) | `UEBERGABE.vorlauftemp_sekundaer_ist.value` | s16 | 04 | r | r |
| 10506 | ÜGS 14: Vorlauftemperatur Sekundär (status) | `UEBERGABE.vorlauftemp_sekundaer_ist.status` | s16 | 04 | r | r |
| 10508 | ÜGS 1: Vorlauftemperatur Soll | `UEBERGABE.vorlauftemp_sekundaer_soll` | s16 | 04 | r | r |
| 10509 | ÜGS 2: Vorlauftemperatur Soll | `UEBERGABE.vorlauftemp_sekundaer_soll` | s16 | 04 | r | r |
| 10510 | ÜGS 3: Vorlauftemperatur Soll | `UEBERGABE.vorlauftemp_sekundaer_soll` | s16 | 04 | r | r |
| 10511 | ÜGS 4: Vorlauftemperatur Soll | `UEBERGABE.vorlauftemp_sekundaer_soll` | s16 | 04 | r | r |
| 10512 | ÜGS 5: Vorlauftemperatur Soll | `UEBERGABE.vorlauftemp_sekundaer_soll` | s16 | 04 | r | r |
| 10513 | ÜGS 6: Vorlauftemperatur Soll | `UEBERGABE.vorlauftemp_sekundaer_soll` | s16 | 04 | r | r |
| 10514 | ÜGS 7: Vorlauftemperatur Soll | `UEBERGABE.vorlauftemp_sekundaer_soll` | s16 | 04 | r | r |
| 10515 | ÜGS 8: Vorlauftemperatur Soll | `UEBERGABE.vorlauftemp_sekundaer_soll` | s16 | 04 | r | r |
| 10516 | ÜGS 9: Vorlauftemperatur Soll | `UEBERGABE.vorlauftemp_sekundaer_soll` | s16 | 04 | r | r |
| 10517 | ÜGS 10: Vorlauftemperatur Soll | `UEBERGABE.vorlauftemp_sekundaer_soll` | s16 | 04 | r | r |
| 10518 | ÜGS 11: Vorlauftemperatur Soll | `UEBERGABE.vorlauftemp_sekundaer_soll` | s16 | 04 | r | r |
| 10519 | ÜGS 12: Vorlauftemperatur Soll | `UEBERGABE.vorlauftemp_sekundaer_soll` | s16 | 04 | r | r |
| 10520 | ÜGS 13: Vorlauftemperatur Soll | `UEBERGABE.vorlauftemp_sekundaer_soll` | s16 | 04 | r | r |
| 10521 | ÜGS 14: Vorlauftemperatur Soll | `UEBERGABE.vorlauftemp_sekundaer_soll` | s16 | 04 | r | r |
| 10524 | ÜGS 1: Vorlauftemperatur Primär (value) | `UEBERGABE.vorlauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10525 | ÜGS 1: Vorlauftemperatur Primär (status) | `UEBERGABE.vorlauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10526 | ÜGS 2: Vorlauftemperatur Primär (value) | `UEBERGABE.vorlauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10527 | ÜGS 2: Vorlauftemperatur Primär (status) | `UEBERGABE.vorlauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10528 | ÜGS 3: Vorlauftemperatur Primär (value) | `UEBERGABE.vorlauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10529 | ÜGS 3: Vorlauftemperatur Primär (status) | `UEBERGABE.vorlauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10530 | ÜGS 4: Vorlauftemperatur Primär (value) | `UEBERGABE.vorlauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10531 | ÜGS 4: Vorlauftemperatur Primär (status) | `UEBERGABE.vorlauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10532 | ÜGS 5: Vorlauftemperatur Primär (value) | `UEBERGABE.vorlauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10533 | ÜGS 5: Vorlauftemperatur Primär (status) | `UEBERGABE.vorlauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10534 | ÜGS 6: Vorlauftemperatur Primär (value) | `UEBERGABE.vorlauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10535 | ÜGS 6: Vorlauftemperatur Primär (status) | `UEBERGABE.vorlauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10536 | ÜGS 7: Vorlauftemperatur Primär (value) | `UEBERGABE.vorlauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10537 | ÜGS 7: Vorlauftemperatur Primär (status) | `UEBERGABE.vorlauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10538 | ÜGS 8: Vorlauftemperatur Primär (value) | `UEBERGABE.vorlauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10539 | ÜGS 8: Vorlauftemperatur Primär (status) | `UEBERGABE.vorlauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10540 | ÜGS 9: Vorlauftemperatur Primär (value) | `UEBERGABE.vorlauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10541 | ÜGS 9: Vorlauftemperatur Primär (status) | `UEBERGABE.vorlauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10542 | ÜGS 10: Vorlauftemperatur Primär (value) | `UEBERGABE.vorlauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10543 | ÜGS 10: Vorlauftemperatur Primär (status) | `UEBERGABE.vorlauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10544 | ÜGS 11: Vorlauftemperatur Primär (value) | `UEBERGABE.vorlauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10545 | ÜGS 11: Vorlauftemperatur Primär (status) | `UEBERGABE.vorlauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10546 | ÜGS 12: Vorlauftemperatur Primär (value) | `UEBERGABE.vorlauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10547 | ÜGS 12: Vorlauftemperatur Primär (status) | `UEBERGABE.vorlauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10548 | ÜGS 13: Vorlauftemperatur Primär (value) | `UEBERGABE.vorlauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10549 | ÜGS 13: Vorlauftemperatur Primär (status) | `UEBERGABE.vorlauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10550 | ÜGS 14: Vorlauftemperatur Primär (value) | `UEBERGABE.vorlauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10551 | ÜGS 14: Vorlauftemperatur Primär (status) | `UEBERGABE.vorlauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10554 | ÜGS 1: Rücklauftemperatur Primär (value) | `UEBERGABE.ruecklauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10555 | ÜGS 1: Rücklauftemperatur Primär (status) | `UEBERGABE.ruecklauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10556 | ÜGS 2: Rücklauftemperatur Primär (value) | `UEBERGABE.ruecklauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10557 | ÜGS 2: Rücklauftemperatur Primär (status) | `UEBERGABE.ruecklauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10558 | ÜGS 3: Rücklauftemperatur Primär (value) | `UEBERGABE.ruecklauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10559 | ÜGS 3: Rücklauftemperatur Primär (status) | `UEBERGABE.ruecklauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10560 | ÜGS 4: Rücklauftemperatur Primär (value) | `UEBERGABE.ruecklauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10561 | ÜGS 4: Rücklauftemperatur Primär (status) | `UEBERGABE.ruecklauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10562 | ÜGS 5: Rücklauftemperatur Primär (value) | `UEBERGABE.ruecklauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10563 | ÜGS 5: Rücklauftemperatur Primär (status) | `UEBERGABE.ruecklauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10564 | ÜGS 6: Rücklauftemperatur Primär (value) | `UEBERGABE.ruecklauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10565 | ÜGS 6: Rücklauftemperatur Primär (status) | `UEBERGABE.ruecklauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10566 | ÜGS 7: Rücklauftemperatur Primär (value) | `UEBERGABE.ruecklauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10567 | ÜGS 7: Rücklauftemperatur Primär (status) | `UEBERGABE.ruecklauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10568 | ÜGS 8: Rücklauftemperatur Primär (value) | `UEBERGABE.ruecklauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10569 | ÜGS 8: Rücklauftemperatur Primär (status) | `UEBERGABE.ruecklauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10570 | ÜGS 9: Rücklauftemperatur Primär (value) | `UEBERGABE.ruecklauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10571 | ÜGS 9: Rücklauftemperatur Primär (status) | `UEBERGABE.ruecklauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10572 | ÜGS 10: Rücklauftemperatur Primär (value) | `UEBERGABE.ruecklauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10573 | ÜGS 10: Rücklauftemperatur Primär (status) | `UEBERGABE.ruecklauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10574 | ÜGS 11: Rücklauftemperatur Primär (value) | `UEBERGABE.ruecklauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10575 | ÜGS 11: Rücklauftemperatur Primär (status) | `UEBERGABE.ruecklauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10576 | ÜGS 12: Rücklauftemperatur Primär (value) | `UEBERGABE.ruecklauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10577 | ÜGS 12: Rücklauftemperatur Primär (status) | `UEBERGABE.ruecklauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10578 | ÜGS 13: Rücklauftemperatur Primär (value) | `UEBERGABE.ruecklauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10579 | ÜGS 13: Rücklauftemperatur Primär (status) | `UEBERGABE.ruecklauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10580 | ÜGS 14: Rücklauftemperatur Primär (value) | `UEBERGABE.ruecklauftemp_primaer_ist.value` | s16 | 04 | r | r |
| 10581 | ÜGS 14: Rücklauftemperatur Primär (status) | `UEBERGABE.ruecklauftemp_primaer_ist.status` | s16 | 04 | r | r |
| 10583 | ÜGS 1: Ventil | `UEBERGABE.o_ventil` | s16 | 04 | r | r |
| 10584 | ÜGS 2: Ventil | `UEBERGABE.o_ventil` | s16 | 04 | r | r |
| 10585 | ÜGS 3: Ventil | `UEBERGABE.o_ventil` | s16 | 04 | r | r |
| 10586 | ÜGS 4: Ventil | `UEBERGABE.o_ventil` | s16 | 04 | r | r |
| 10587 | ÜGS 5: Ventil | `UEBERGABE.o_ventil` | s16 | 04 | r | r |
| 10588 | ÜGS 6: Ventil | `UEBERGABE.o_ventil` | s16 | 04 | r | r |
| 10589 | ÜGS 7: Ventil | `UEBERGABE.o_ventil` | s16 | 04 | r | r |
| 10590 | ÜGS 8: Ventil | `UEBERGABE.o_ventil` | s16 | 04 | r | r |
| 10591 | ÜGS 9: Ventil | `UEBERGABE.o_ventil` | s16 | 04 | r | r |
| 10592 | ÜGS 10: Ventil | `UEBERGABE.o_ventil` | s16 | 04 | r | r |
| 10593 | ÜGS 11: Ventil | `UEBERGABE.o_ventil` | s16 | 04 | r | r |
| 10594 | ÜGS 12: Ventil | `UEBERGABE.o_ventil` | s16 | 04 | r | r |
| 10595 | ÜGS 13: Ventil | `UEBERGABE.o_ventil` | s16 | 04 | r | r |
| 10596 | ÜGS 14: Ventil | `UEBERGABE.o_ventil` | s16 | 04 | r | r |
| 25306 | ÜGS 1: Temperaturerhöhung | `UEBERGABE.temperatur_anhebung` | s16 | 03 | r | rw |
| 25307 | ÜGS 2: Temperaturerhöhung | `UEBERGABE.temperatur_anhebung` | s16 | 03 | r | rw |
| 25308 | ÜGS 3: Temperaturerhöhung | `UEBERGABE.temperatur_anhebung` | s16 | 03 | r | rw |
| 25309 | ÜGS 4: Temperaturerhöhung | `UEBERGABE.temperatur_anhebung` | s16 | 03 | r | rw |
| 25310 | ÜGS 5: Temperaturerhöhung | `UEBERGABE.temperatur_anhebung` | s16 | 03 | r | rw |
| 25311 | ÜGS 6: Temperaturerhöhung | `UEBERGABE.temperatur_anhebung` | s16 | 03 | r | rw |
| 25312 | ÜGS 7: Temperaturerhöhung | `UEBERGABE.temperatur_anhebung` | s16 | 03 | r | rw |
| 25313 | ÜGS 8: Temperaturerhöhung | `UEBERGABE.temperatur_anhebung` | s16 | 03 | r | rw |
| 25314 | ÜGS 9: Temperaturerhöhung | `UEBERGABE.temperatur_anhebung` | s16 | 03 | r | rw |
| 25315 | ÜGS 10: Temperaturerhöhung | `UEBERGABE.temperatur_anhebung` | s16 | 03 | r | rw |
| 25316 | ÜGS 11: Temperaturerhöhung | `UEBERGABE.temperatur_anhebung` | s16 | 03 | r | rw |
| 25317 | ÜGS 12: Temperaturerhöhung | `UEBERGABE.temperatur_anhebung` | s16 | 03 | r | rw |
| 25318 | ÜGS 13: Temperaturerhöhung | `UEBERGABE.temperatur_anhebung` | s16 | 03 | r | rw |
| 25319 | ÜGS 14: Temperaturerhöhung | `UEBERGABE.temperatur_anhebung` | s16 | 03 | r | rw |
| 25321 | ÜGS 1: Rücklauftemp. Begrenzung | `UEBERGABE.ruecklauftemp_begrenzung` | s16 | 03 | r | rw |
| 25322 | ÜGS 2: Rücklauftemp. Begrenzung | `UEBERGABE.ruecklauftemp_begrenzung` | s16 | 03 | r | rw |
| 25323 | ÜGS 3: Rücklauftemp. Begrenzung | `UEBERGABE.ruecklauftemp_begrenzung` | s16 | 03 | r | rw |
| 25324 | ÜGS 4: Rücklauftemp. Begrenzung | `UEBERGABE.ruecklauftemp_begrenzung` | s16 | 03 | r | rw |
| 25325 | ÜGS 5: Rücklauftemp. Begrenzung | `UEBERGABE.ruecklauftemp_begrenzung` | s16 | 03 | r | rw |
| 25326 | ÜGS 6: Rücklauftemp. Begrenzung | `UEBERGABE.ruecklauftemp_begrenzung` | s16 | 03 | r | rw |
| 25327 | ÜGS 7: Rücklauftemp. Begrenzung | `UEBERGABE.ruecklauftemp_begrenzung` | s16 | 03 | r | rw |
| 25328 | ÜGS 8: Rücklauftemp. Begrenzung | `UEBERGABE.ruecklauftemp_begrenzung` | s16 | 03 | r | rw |
| 25329 | ÜGS 9: Rücklauftemp. Begrenzung | `UEBERGABE.ruecklauftemp_begrenzung` | s16 | 03 | r | rw |
| 25330 | ÜGS 10: Rücklauftemp. Begrenzung | `UEBERGABE.ruecklauftemp_begrenzung` | s16 | 03 | r | rw |
| 25331 | ÜGS 11: Rücklauftemp. Begrenzung | `UEBERGABE.ruecklauftemp_begrenzung` | s16 | 03 | r | rw |
| 25332 | ÜGS 12: Rücklauftemp. Begrenzung | `UEBERGABE.ruecklauftemp_begrenzung` | s16 | 03 | r | rw |
| 25333 | ÜGS 13: Rücklauftemp. Begrenzung | `UEBERGABE.ruecklauftemp_begrenzung` | s16 | 03 | r | rw |
| 25334 | ÜGS 14: Rücklauftemp. Begrenzung | `UEBERGABE.ruecklauftemp_begrenzung` | s16 | 03 | r | rw |
| 25336 | ÜGS 1: Grenztemperatur | `UEBERGABE.grenz_temp` | s16 | 03 | r | rw |
| 25337 | ÜGS 2: Grenztemperatur | `UEBERGABE.grenz_temp` | s16 | 03 | r | rw |
| 25338 | ÜGS 3: Grenztemperatur | `UEBERGABE.grenz_temp` | s16 | 03 | r | rw |
| 25339 | ÜGS 4: Grenztemperatur | `UEBERGABE.grenz_temp` | s16 | 03 | r | rw |
| 25340 | ÜGS 5: Grenztemperatur | `UEBERGABE.grenz_temp` | s16 | 03 | r | rw |
| 25341 | ÜGS 6: Grenztemperatur | `UEBERGABE.grenz_temp` | s16 | 03 | r | rw |
| 25342 | ÜGS 7: Grenztemperatur | `UEBERGABE.grenz_temp` | s16 | 03 | r | rw |
| 25343 | ÜGS 8: Grenztemperatur | `UEBERGABE.grenz_temp` | s16 | 03 | r | rw |
| 25344 | ÜGS 9: Grenztemperatur | `UEBERGABE.grenz_temp` | s16 | 03 | r | rw |
| 25345 | ÜGS 10: Grenztemperatur | `UEBERGABE.grenz_temp` | s16 | 03 | r | rw |
| 25346 | ÜGS 11: Grenztemperatur | `UEBERGABE.grenz_temp` | s16 | 03 | r | rw |
| 25347 | ÜGS 12: Grenztemperatur | `UEBERGABE.grenz_temp` | s16 | 03 | r | rw |
| 25348 | ÜGS 13: Grenztemperatur | `UEBERGABE.grenz_temp` | s16 | 03 | r | rw |
| 25349 | ÜGS 14: Grenztemperatur | `UEBERGABE.grenz_temp` | s16 | 03 | r | rw |

### KWB Easyfire (`kwb_easyfire.json`, 60 Register)

| Adresse | Name (mit Slot) | Parameter | Typ | FC | User | Expert |
|---:|---|---|---|:---:|:---:|:---:|
| 8197 | Kesseltemperatur Ist (value) | `KSM.i_kesseltemp_ist.value` | s16 | 04 | r | r |
| 8198 | Kesseltemperatur Ist (status) | `KSM.i_kesseltemp_ist.status` | s16 | 04 | r | r |
| 8199 | Kesseltemperatur Soll | `KSM.kesseltemp_soll` | s16 | 04 | r | r |
| 8200 | Kesselpumpe | `KSM.DO_Kesselpumpe` | s16 | 04 | r | r |
| 8201 | Kesselpumpe % | `KSM.kesselpumpe_steuerstufe` | u16 | 04 | r | r |
| 8202 | Rücklauftemperatur Ist (value) | `KSM.i_ruecklauftemp_ist.value` | s16 | 04 | r | r |
| 8203 | Rücklauftemperatur Ist (status) | `KSM.i_ruecklauftemp_ist.status` | s16 | 04 | r | r |
| 8207 | Kesselleistung | `KSM.brennerleistung` | s16 | 04 | r | r |
| 8208 | Kesselstatus | `KSM.kesselstatus_anzeige` | s16 | 04 | r | r |
| 8209 | Volllaststunden | `KSM.Betriebsminuten_Summe` | u32 | 04 | r | r |
| 8214 | Sauerstoff Ist | `KSM.O2Ist` | s16 | 04 | r | r |
| 8215 | Flammtemperatur Ist (value) | `KSM.i_flammtemp_ist.value` | s16 | 04 | r | r |
| 8216 | Flammtemperatur Ist (status) | `KSM.i_flammtemp_ist.status` | s16 | 04 | r | r |
| 8218 | Unterdruck Ist | `KSM.AI_Feuerraum_Unterdruck` | s16 | 04 | r | r |
| 8221 | Primärgebläse | `AK.pl_geblaesestufe` | s16 | 04 | r | r |
| 8223 | Saugzugstufe | `KSM.Saugzugstufe` | s16 | 04 | r | r |
| 8224 | Nächste Wartung in | `KSM.ServiceintervallReststunden` | s16 | 04 | r | r |
| 8226 | Antrieb Fördersystem | `FS.o_motor_foerdersystem_1` | s16 | 04 | r | r |
| 8227 | Extern 1 | `KSM.i_extern1` | s16 | 04 | r | r |
| 8228 | Extern 2 | `KSM.i_extern2` | s16 | 04 | r | r |
| 8229 | Extern 3 | `KSM.i_extern3` | s16 | 04 | r | r |
| 8231 | Abgastemperatur (value) | `KSM.i_rauchgastemp_ist.value` | s16 | 04 | r | r |
| 8232 | Abgastemperatur (status) | `KSM.i_rauchgastemp_ist.status` | s16 | 04 | r | r |
| 8233 | Brennstoffverbrauch | `FS.pelletsverbrauch` | u32 | 04 | r | r |
| 8235 | Brennstofffaktor | `EF2.Brennstofffaktor` | s16 | 04 | r | r |
| 8236 | Brennerleistung extern | `AK.externe_brennerleistung` | s16 | 04 | r | r |
| 8237 | Kesseltemp. Soll Extern | `AK.externe_kessel_solltemperatur` | s16 | 04 | r | r |
| 8238 | Saugturbine | `KSM.DO_Pelletssauger` | s16 | 04 | r | r |
| 8250 | Außentemperatur Istwert (value) | `SYSTEM.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8251 | Außentemperatur Istwert (status) | `SYSTEM.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 9044 | Multifunktionsausgang 1 (125) | `KSM.o_multifunktionsausgang_1` | s16 | 04 | r | r |
| 9045 | Multifunktionsausgang 2 (127) | `KSM.o_multifunktionsausgang_2` | s16 | 04 | r | r |
| 9046 | Multifunktionsausgang 3 (124) | `KSM.o_multifunktionsausgang_3` | s16 | 04 | r | r |
| 9047 | Multifunktionsausgang 4 (126) | `KSM.o_multifunktionsausgang_4` | s16 | 04 | r | r |
| 9495 | Modbus Überhitzung | `KSM.modbus_ueberhitzung` | s16 | 04 | r | r |
| 9496 | Modbus Wärmeabnahme Max | `KSM.modbus_waermeabnahme_max` | s16 | 04 | r | r |
| 9497 | Füllstand Aschebehälter | `KSM.aschefuellstand` | u16 | 04 | r | r |
| 9498 | Drehzahl Saugzug | `KSM.i_drehzahl_saugzug` | u16 | 04 | r | r |
| 9877 | Brennerleistung bestimmt durch | `AK.anforderung_bl_ursache` | s16 | 04 | r | r |
| 9878 | Wärmemenge gesamt | `KSM.waermemenge_gesamt_kwh` | u32 | 04 | r | r |
| 9970 | Kesselstatus | `KSM.kesselstatus_anzeige_simple` | s16 | 04 | r | r |
| 9988 | Brennstoffverbrauch Rücksetzzähler | `FS.pelletverbrauch_reset_counter` | u16 | 04 | r | r |
| 9989 | Clee Status | `SYSTEM.comfortenergy_status` | s16 | 04 | r | r |
| 24576 | Kessel Ein/Aus | `AK.anlage_ein` | s16 | 03 | rw | rw |
| 24577 | Solltemperatur 1 | `EF2.KesseltempSoll1` | s16 | 03 | r | rw |
| 24578 | Solltemperatur 2 | `EF2.KesseltempSoll2` | s16 | 03 | r | rw |
| 24581 | Rücklauftemperatur Minimum | `KSM.RuecklauftempMin` | s16 | 03 | r | rw |
| 24583 | Externe Vorgabe | `AK.externe_vorgabe` | s16 | 03 | r | rw |
| 24584 | Kesselprogramm | `AK.kesselprogramm` | s16 | 03 | r | rw |
| 24849 | Modbus Lifetick | `KSM.modbus_lifetick` | u16 | 03 | r | rw |
| 24850 | Modbus Commit Lifetick | `KSM.modbus_commit_lifetick` | u16 | 03 | r | r |
| 24851 | Modbus Kesseltemperatur | `KSM.modbus_kesseltemp_vorgabe` | s16 | 03 | r | rw |
| 24852 | Modbus Kesselleistung | `KSM.modbus_leistung_vorgabe` | s16 | 03 | r | rw |
| 24854 | Modbus Kesselanforderung | `KSM.modbus_kesselanforderung` | s16 | 03 | r | rw |
| 24927 | Restmenge Brennstofflager | `KSM.restmenge_brennstofflager` | u32 | 03 | rw | rw |
| 24932 | Modbus Puffertemperatur oben für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_oben.value` | s16 | 03 | r | rw |
| 24933 | Modbus Puffertemperatur oben für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_oben.status` | s16 | 03 | r | rw |
| 24934 | Modbus Puffertemperatur unten für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_unten.value` | s16 | 03 | r | rw |
| 24935 | Modbus Puffertemperatur unten für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_unten.status` | s16 | 03 | r | rw |
| 25040 | Modbus Überstromnutzung | `SYSTEM.modbus_clee_ueberschusstrom` | s16 | 03 | r | rw |

### KWB EF3 (`kwb_ef3.json`, 58 Register)

| Adresse | Name (mit Slot) | Parameter | Typ | FC | User | Expert |
|---:|---|---|---|:---:|:---:|:---:|
| 8197 | Kesseltemperatur Ist (value) | `KSM.i_kesseltemp_ist.value` | s16 | 04 | r | r |
| 8198 | Kesseltemperatur Ist (status) | `KSM.i_kesseltemp_ist.status` | s16 | 04 | r | r |
| 8199 | Kesseltemperatur Soll | `KSM.kesseltemp_soll` | s16 | 04 | r | r |
| 8200 | Kesselpumpe | `KSM.DO_Kesselpumpe` | s16 | 04 | r | r |
| 8201 | Kesselpumpe % | `KSM.kesselpumpe_steuerstufe` | u16 | 04 | r | r |
| 8202 | Rücklauftemperatur Ist (value) | `KSM.i_ruecklauftemp_ist.value` | s16 | 04 | r | r |
| 8203 | Rücklauftemperatur Ist (status) | `KSM.i_ruecklauftemp_ist.status` | s16 | 04 | r | r |
| 8207 | Kesselleistung | `KSM.brennerleistung` | s16 | 04 | r | r |
| 8208 | Kesselstatus | `KSM.kesselstatus_anzeige` | s16 | 04 | r | r |
| 8209 | Volllaststunden | `KSM.Betriebsminuten_Summe` | u32 | 04 | r | r |
| 8214 | Sauerstoff Ist | `KSM.O2Ist` | s16 | 04 | r | r |
| 8215 | Flammtemperatur Ist (value) | `KSM.i_flammtemp_ist.value` | s16 | 04 | r | r |
| 8216 | Flammtemperatur Ist (status) | `KSM.i_flammtemp_ist.status` | s16 | 04 | r | r |
| 8223 | Saugzugstufe | `KSM.Saugzugstufe` | s16 | 04 | r | r |
| 8224 | Nächste Wartung in | `KSM.ServiceintervallReststunden` | s16 | 04 | r | r |
| 8226 | Antrieb Fördersystem | `FS.o_motor_foerdersystem_1` | s16 | 04 | r | r |
| 8227 | Extern 1 | `KSM.i_extern1` | s16 | 04 | r | r |
| 8228 | Extern 2 | `KSM.i_extern2` | s16 | 04 | r | r |
| 8229 | Extern 3 | `KSM.i_extern3` | s16 | 04 | r | r |
| 8231 | Abgastemperatur (value) | `KSM.i_rauchgastemp_ist.value` | s16 | 04 | r | r |
| 8232 | Abgastemperatur (status) | `KSM.i_rauchgastemp_ist.status` | s16 | 04 | r | r |
| 8233 | Brennstoffverbrauch | `FS.pelletsverbrauch` | u32 | 04 | r | r |
| 8235 | Brennstofffaktor | `EF2.Brennstofffaktor` | s16 | 04 | r | r |
| 8236 | Brennerleistung extern | `AK.externe_brennerleistung` | s16 | 04 | r | r |
| 8237 | Kesseltemp. Soll Extern | `AK.externe_kessel_solltemperatur` | s16 | 04 | r | r |
| 8238 | Saugturbine | `KSM.DO_Pelletssauger` | s16 | 04 | r | r |
| 8250 | Außentemperatur Istwert (value) | `SYSTEM.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8251 | Außentemperatur Istwert (status) | `SYSTEM.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 9044 | Multifunktionsausgang 1 (125) | `KSM.o_multifunktionsausgang_1` | s16 | 04 | r | r |
| 9045 | Multifunktionsausgang 2 (127) | `KSM.o_multifunktionsausgang_2` | s16 | 04 | r | r |
| 9046 | Multifunktionsausgang 3 (124) | `KSM.o_multifunktionsausgang_3` | s16 | 04 | r | r |
| 9047 | Multifunktionsausgang 4 (126) | `KSM.o_multifunktionsausgang_4` | s16 | 04 | r | r |
| 9495 | Modbus Überhitzung | `KSM.modbus_ueberhitzung` | s16 | 04 | r | r |
| 9496 | Modbus Wärmeabnahme Max | `KSM.modbus_waermeabnahme_max` | s16 | 04 | r | r |
| 9497 | Füllstand Aschebehälter | `KSM.aschefuellstand` | u16 | 04 | r | r |
| 9498 | Drehzahl Saugzug | `KSM.i_drehzahl_saugzug` | u16 | 04 | r | r |
| 9877 | Brennerleistung bestimmt durch | `AK.anforderung_bl_ursache` | s16 | 04 | r | r |
| 9878 | Wärmemenge gesamt | `KSM.waermemenge_gesamt_kwh` | u32 | 04 | r | r |
| 9970 | Kesselstatus | `KSM.kesselstatus_anzeige_simple` | s16 | 04 | r | r |
| 9988 | Brennstoffverbrauch Rücksetzzähler | `FS.pelletverbrauch_reset_counter` | u16 | 04 | r | r |
| 9989 | Clee Status | `SYSTEM.comfortenergy_status` | s16 | 04 | r | r |
| 10023 | Differenzdruck Ist | `EF2.ef3_differenzdruck_ist` | s16 | 04 | r | r |
| 24576 | Kessel Ein/Aus | `AK.anlage_ein` | s16 | 03 | rw | rw |
| 24577 | Solltemperatur 1 | `EF2.KesseltempSoll1` | s16 | 03 | r | rw |
| 24578 | Solltemperatur 2 | `EF2.KesseltempSoll2` | s16 | 03 | r | rw |
| 24583 | Externe Vorgabe | `AK.externe_vorgabe` | s16 | 03 | r | rw |
| 24584 | Kesselprogramm | `AK.kesselprogramm` | s16 | 03 | r | rw |
| 24849 | Modbus Lifetick | `KSM.modbus_lifetick` | u16 | 03 | r | rw |
| 24850 | Modbus Commit Lifetick | `KSM.modbus_commit_lifetick` | u16 | 03 | r | r |
| 24851 | Modbus Kesseltemperatur | `KSM.modbus_kesseltemp_vorgabe` | s16 | 03 | r | rw |
| 24852 | Modbus Kesselleistung | `KSM.modbus_leistung_vorgabe` | s16 | 03 | r | rw |
| 24854 | Modbus Kesselanforderung | `KSM.modbus_kesselanforderung` | s16 | 03 | r | rw |
| 24927 | Restmenge Brennstofflager | `KSM.restmenge_brennstofflager` | u32 | 03 | rw | rw |
| 24932 | Modbus Puffertemperatur oben für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_oben.value` | s16 | 03 | r | rw |
| 24933 | Modbus Puffertemperatur oben für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_oben.status` | s16 | 03 | r | rw |
| 24934 | Modbus Puffertemperatur unten für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_unten.value` | s16 | 03 | r | rw |
| 24935 | Modbus Puffertemperatur unten für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_unten.status` | s16 | 03 | r | rw |
| 25040 | Modbus Überstromnutzung | `SYSTEM.modbus_clee_ueberschusstrom` | s16 | 03 | r | rw |

### KWB Multifire (`kwb_multifire.json`, 61 Register)

| Adresse | Name (mit Slot) | Parameter | Typ | FC | User | Expert |
|---:|---|---|---|:---:|:---:|:---:|
| 8197 | Kesseltemperatur Ist (value) | `KSM.i_kesseltemp_ist.value` | s16 | 04 | r | r |
| 8198 | Kesseltemperatur Ist (status) | `KSM.i_kesseltemp_ist.status` | s16 | 04 | r | r |
| 8199 | Kesseltemperatur Soll | `KSM.kesseltemp_soll` | s16 | 04 | r | r |
| 8200 | Kesselpumpe | `KSM.DO_Kesselpumpe` | s16 | 04 | r | r |
| 8201 | Kesselpumpe % | `KSM.kesselpumpe_steuerstufe` | u16 | 04 | r | r |
| 8202 | Rücklauftemperatur Ist (value) | `KSM.i_ruecklauftemp_ist.value` | s16 | 04 | r | r |
| 8203 | Rücklauftemperatur Ist (status) | `KSM.i_ruecklauftemp_ist.status` | s16 | 04 | r | r |
| 8206 | Verbraucher Anforderung | `KSM.verbraucher_anforderung` | s16 | 04 | r | r |
| 8207 | Kesselleistung | `KSM.brennerleistung` | s16 | 04 | r | r |
| 8208 | Kesselstatus | `KSM.kesselstatus_anzeige` | s16 | 04 | r | r |
| 8209 | Volllaststunden | `KSM.Betriebsminuten_Summe` | u32 | 04 | r | r |
| 8213 | Glutbett | `MF2.Glutbettniveau` | s16 | 04 | r | r |
| 8214 | Sauerstoff Ist | `KSM.O2Ist` | s16 | 04 | r | r |
| 8215 | Flammtemperatur Ist (value) | `KSM.i_flammtemp_ist.value` | s16 | 04 | r | r |
| 8216 | Flammtemperatur Ist (status) | `KSM.i_flammtemp_ist.status` | s16 | 04 | r | r |
| 8217 | Ultraschallsensor ist | `MF2.AI_Fuellstand_Zwischenbehaelter` | s16 | 04 | r | r |
| 8218 | Unterdruck Ist | `KSM.AI_Feuerraum_Unterdruck` | s16 | 04 | r | r |
| 8219 | Ausbrandtemperatur (value) | `MF2.i_ausbrandtemp.value` | s16 | 04 | r | r |
| 8220 | Ausbrandtemperatur (status) | `MF2.i_ausbrandtemp.status` | s16 | 04 | r | r |
| 8221 | Primärgebläse | `AK.pl_geblaesestufe` | s16 | 04 | r | r |
| 8222 | Sekundärgebläse | `MF2.sl_geblaesestufe` | s16 | 04 | r | r |
| 8223 | Saugzugstufe | `KSM.Saugzugstufe` | s16 | 04 | r | r |
| 8224 | Nächste Wartung in | `KSM.ServiceintervallReststunden` | s16 | 04 | r | r |
| 8226 | Antrieb Fördersystem | `FS.o_motor_foerdersystem_1` | s16 | 04 | r | r |
| 8227 | Extern 1 | `KSM.i_extern1` | s16 | 04 | r | r |
| 8228 | Extern 2 | `KSM.i_extern2` | s16 | 04 | r | r |
| 8229 | Extern 3 | `KSM.i_extern3` | s16 | 04 | r | r |
| 8230 | Brennstofffaktor | `MF2.Brennstofffaktor` | s16 | 04 | r | r |
| 8236 | Brennerleistung extern | `AK.externe_brennerleistung` | s16 | 04 | r | r |
| 8237 | Kesseltemp. Soll Extern | `AK.externe_kessel_solltemperatur` | s16 | 04 | r | r |
| 8239 | Asche 90% voll | `MF2.i_aschebehaelter_90_prz` | s16 | 04 | r | r |
| 8240 | Luftverschiebung | `MF2.luftverschiebung_gesamt` | s16 | 04 | r | r |
| 8241 | Zwischenbehälter Füllstand | `MF2.zwischenbehaelter_fuellstand_prz` | s16 | 04 | r | r |
| 8250 | Außentemperatur Istwert (value) | `SYSTEM.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8251 | Außentemperatur Istwert (status) | `SYSTEM.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 9044 | Multifunktionsausgang 1 (125) | `KSM.o_multifunktionsausgang_1` | s16 | 04 | r | r |
| 9045 | Multifunktionsausgang 2 (127) | `KSM.o_multifunktionsausgang_2` | s16 | 04 | r | r |
| 9046 | Multifunktionsausgang 3 (124) | `KSM.o_multifunktionsausgang_3` | s16 | 04 | r | r |
| 9047 | Multifunktionsausgang 4 (126) | `KSM.o_multifunktionsausgang_4` | s16 | 04 | r | r |
| 9495 | Modbus Überhitzung | `KSM.modbus_ueberhitzung` | s16 | 04 | r | r |
| 9496 | Modbus Wärmeabnahme Max | `KSM.modbus_waermeabnahme_max` | s16 | 04 | r | r |
| 9498 | Drehzahl Saugzug | `KSM.i_drehzahl_saugzug` | u16 | 04 | r | r |
| 9877 | Brennerleistung bestimmt durch | `AK.anforderung_bl_ursache` | s16 | 04 | r | r |
| 9878 | Wärmemenge gesamt | `KSM.waermemenge_gesamt_kwh` | u32 | 04 | r | r |
| 9970 | Kesselstatus | `KSM.kesselstatus_anzeige_simple` | s16 | 04 | r | r |
| 24576 | Kessel Ein/Aus | `AK.anlage_ein` | s16 | 03 | rw | rw |
| 24579 | Solltemperatur 1 | `MF2.KesseltempSoll1` | s16 | 03 | r | rw |
| 24580 | Solltemperatur 2 | `MF2.KesseltempSoll2` | s16 | 03 | r | rw |
| 24581 | Rücklauftemperatur Minimum | `KSM.RuecklauftempMin` | s16 | 03 | r | rw |
| 24583 | Externe Vorgabe | `AK.externe_vorgabe` | s16 | 03 | r | rw |
| 24584 | Kesselprogramm | `AK.kesselprogramm` | s16 | 03 | r | rw |
| 24849 | Modbus Lifetick | `KSM.modbus_lifetick` | u16 | 03 | r | rw |
| 24850 | Modbus Commit Lifetick | `KSM.modbus_commit_lifetick` | u16 | 03 | r | r |
| 24851 | Modbus Kesseltemperatur | `KSM.modbus_kesseltemp_vorgabe` | s16 | 03 | r | rw |
| 24852 | Modbus Kesselleistung | `KSM.modbus_leistung_vorgabe` | s16 | 03 | r | rw |
| 24854 | Modbus Kesselanforderung | `KSM.modbus_kesselanforderung` | s16 | 03 | r | rw |
| 24932 | Modbus Puffertemperatur oben für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_oben.value` | s16 | 03 | r | rw |
| 24933 | Modbus Puffertemperatur oben für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_oben.status` | s16 | 03 | r | rw |
| 24934 | Modbus Puffertemperatur unten für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_unten.value` | s16 | 03 | r | rw |
| 24935 | Modbus Puffertemperatur unten für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_unten.status` | s16 | 03 | r | rw |
| 25040 | Modbus Überstromnutzung | `SYSTEM.modbus_clee_ueberschusstrom` | s16 | 03 | r | rw |

### KWB Pelletfire+ (`kwb_pelletfire_plus.json`, 63 Register)

| Adresse | Name (mit Slot) | Parameter | Typ | FC | User | Expert |
|---:|---|---|---|:---:|:---:|:---:|
| 8197 | Kesseltemperatur Ist (value) | `KSM.i_kesseltemp_ist.value` | s16 | 04 | r | r |
| 8198 | Kesseltemperatur Ist (status) | `KSM.i_kesseltemp_ist.status` | s16 | 04 | r | r |
| 8199 | Kesseltemperatur Soll | `KSM.kesseltemp_soll` | s16 | 04 | r | r |
| 8200 | Kesselpumpe | `KSM.DO_Kesselpumpe` | s16 | 04 | r | r |
| 8201 | Kesselpumpe % | `KSM.kesselpumpe_steuerstufe` | u16 | 04 | r | r |
| 8202 | Rücklauftemperatur Ist (value) | `KSM.i_ruecklauftemp_ist.value` | s16 | 04 | r | r |
| 8203 | Rücklauftemperatur Ist (status) | `KSM.i_ruecklauftemp_ist.status` | s16 | 04 | r | r |
| 8206 | Verbraucher Anforderung | `KSM.verbraucher_anforderung` | s16 | 04 | r | r |
| 8207 | Kesselleistung | `KSM.brennerleistung` | s16 | 04 | r | r |
| 8208 | Kesselstatus | `KSM.kesselstatus_anzeige` | s16 | 04 | r | r |
| 8209 | Volllaststunden | `KSM.Betriebsminuten_Summe` | u32 | 04 | r | r |
| 8213 | Glutbett | `MF2.Glutbettniveau` | s16 | 04 | r | r |
| 8214 | Sauerstoff Ist | `KSM.O2Ist` | s16 | 04 | r | r |
| 8215 | Flammtemperatur Ist (value) | `KSM.i_flammtemp_ist.value` | s16 | 04 | r | r |
| 8216 | Flammtemperatur Ist (status) | `KSM.i_flammtemp_ist.status` | s16 | 04 | r | r |
| 8218 | Unterdruck Ist | `KSM.AI_Feuerraum_Unterdruck` | s16 | 04 | r | r |
| 8219 | Ausbrandtemperatur (value) | `MF2.i_ausbrandtemp.value` | s16 | 04 | r | r |
| 8220 | Ausbrandtemperatur (status) | `MF2.i_ausbrandtemp.status` | s16 | 04 | r | r |
| 8221 | Primärgebläse | `AK.pl_geblaesestufe` | s16 | 04 | r | r |
| 8222 | Sekundärgebläse | `MF2.sl_geblaesestufe` | s16 | 04 | r | r |
| 8223 | Saugzugstufe | `KSM.Saugzugstufe` | s16 | 04 | r | r |
| 8224 | Nächste Wartung in | `KSM.ServiceintervallReststunden` | s16 | 04 | r | r |
| 8226 | Antrieb Fördersystem | `FS.o_motor_foerdersystem_1` | s16 | 04 | r | r |
| 8227 | Extern 1 | `KSM.i_extern1` | s16 | 04 | r | r |
| 8228 | Extern 2 | `KSM.i_extern2` | s16 | 04 | r | r |
| 8229 | Extern 3 | `KSM.i_extern3` | s16 | 04 | r | r |
| 8230 | Brennstofffaktor | `MF2.Brennstofffaktor` | s16 | 04 | r | r |
| 8233 | Brennstoffverbrauch | `FS.pelletsverbrauch` | u32 | 04 | r | r |
| 8236 | Brennerleistung extern | `AK.externe_brennerleistung` | s16 | 04 | r | r |
| 8237 | Kesseltemp. Soll Extern | `AK.externe_kessel_solltemperatur` | s16 | 04 | r | r |
| 8238 | Saugturbine | `KSM.DO_Pelletssauger` | s16 | 04 | r | r |
| 8239 | Asche 90% voll | `MF2.i_aschebehaelter_90_prz` | s16 | 04 | r | r |
| 8240 | Luftverschiebung | `MF2.luftverschiebung_gesamt` | s16 | 04 | r | r |
| 8250 | Außentemperatur Istwert (value) | `SYSTEM.i_aussen_temperatur.value` | s16 | 04 | r | r |
| 8251 | Außentemperatur Istwert (status) | `SYSTEM.i_aussen_temperatur.status` | s16 | 04 | r | r |
| 9044 | Multifunktionsausgang 1 (125) | `KSM.o_multifunktionsausgang_1` | s16 | 04 | r | r |
| 9045 | Multifunktionsausgang 2 (127) | `KSM.o_multifunktionsausgang_2` | s16 | 04 | r | r |
| 9046 | Multifunktionsausgang 3 (124) | `KSM.o_multifunktionsausgang_3` | s16 | 04 | r | r |
| 9047 | Multifunktionsausgang 4 (126) | `KSM.o_multifunktionsausgang_4` | s16 | 04 | r | r |
| 9495 | Modbus Überhitzung | `KSM.modbus_ueberhitzung` | s16 | 04 | r | r |
| 9496 | Modbus Wärmeabnahme Max | `KSM.modbus_waermeabnahme_max` | s16 | 04 | r | r |
| 9498 | Drehzahl Saugzug | `KSM.i_drehzahl_saugzug` | u16 | 04 | r | r |
| 9877 | Brennerleistung bestimmt durch | `AK.anforderung_bl_ursache` | s16 | 04 | r | r |
| 9878 | Wärmemenge gesamt | `KSM.waermemenge_gesamt_kwh` | u32 | 04 | r | r |
| 9970 | Kesselstatus | `KSM.kesselstatus_anzeige_simple` | s16 | 04 | r | r |
| 9988 | Brennstoffverbrauch Rücksetzzähler | `FS.pelletverbrauch_reset_counter` | u16 | 04 | r | r |
| 24576 | Kessel Ein/Aus | `AK.anlage_ein` | s16 | 03 | rw | rw |
| 24579 | Solltemperatur 1 | `MF2.KesseltempSoll1` | s16 | 03 | r | rw |
| 24580 | Solltemperatur 2 | `MF2.KesseltempSoll2` | s16 | 03 | r | rw |
| 24581 | Rücklauftemperatur Minimum | `KSM.RuecklauftempMin` | s16 | 03 | r | rw |
| 24583 | Externe Vorgabe | `AK.externe_vorgabe` | s16 | 03 | r | rw |
| 24584 | Kesselprogramm | `AK.kesselprogramm` | s16 | 03 | r | rw |
| 24849 | Modbus Lifetick | `KSM.modbus_lifetick` | u16 | 03 | r | rw |
| 24850 | Modbus Commit Lifetick | `KSM.modbus_commit_lifetick` | u16 | 03 | r | r |
| 24851 | Modbus Kesseltemperatur | `KSM.modbus_kesseltemp_vorgabe` | s16 | 03 | r | rw |
| 24852 | Modbus Kesselleistung | `KSM.modbus_leistung_vorgabe` | s16 | 03 | r | rw |
| 24854 | Modbus Kesselanforderung | `KSM.modbus_kesselanforderung` | s16 | 03 | r | rw |
| 24927 | Restmenge Brennstofflager | `KSM.restmenge_brennstofflager` | u32 | 03 | rw | rw |
| 24932 | Modbus Puffertemperatur oben für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_oben.value` | s16 | 03 | r | rw |
| 24933 | Modbus Puffertemperatur oben für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_oben.status` | s16 | 03 | r | rw |
| 24934 | Modbus Puffertemperatur unten für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_unten.value` | s16 | 03 | r | rw |
| 24935 | Modbus Puffertemperatur unten für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_unten.status` | s16 | 03 | r | rw |
| 25040 | Modbus Überstromnutzung | `SYSTEM.modbus_clee_ueberschusstrom` | s16 | 03 | r | rw |

### KWB Combifire (`kwb_combifire.json`, 67 Register)

| Adresse | Name (mit Slot) | Parameter | Typ | FC | User | Expert |
|---:|---|---|---|:---:|:---:|:---:|
| 8197 | Kesseltemperatur Ist (value) | `KSM.i_kesseltemp_ist.value` | s16 | 04 | r | r |
| 8198 | Kesseltemperatur Ist (status) | `KSM.i_kesseltemp_ist.status` | s16 | 04 | r | r |
| 8199 | Kesseltemperatur Soll | `KSM.kesseltemp_soll` | s16 | 04 | r | r |
| 8200 | Kesselpumpe | `KSM.DO_Kesselpumpe` | s16 | 04 | r | r |
| 8201 | Kesselpumpe % | `KSM.kesselpumpe_steuerstufe` | u16 | 04 | r | r |
| 8202 | Rücklauftemperatur Ist (value) | `KSM.i_ruecklauftemp_ist.value` | s16 | 04 | r | r |
| 8203 | Rücklauftemperatur Ist (status) | `KSM.i_ruecklauftemp_ist.status` | s16 | 04 | r | r |
| 8206 | Verbraucher Anforderung | `KSM.verbraucher_anforderung` | s16 | 04 | r | r |
| 8207 | Kesselleistung | `KSM.brennerleistung` | s16 | 04 | r | r |
| 8208 | Kesselstatus | `KSM.kesselstatus_anzeige` | s16 | 04 | r | r |
| 8209 | Volllaststunden | `KSM.Betriebsminuten_Summe` | u32 | 04 | r | r |
| 8211 | Status Pelletmodul | `AK.kesselstatus_anzeige_ak` | s16 | 04 | r | r |
| 8212 | Status Stückholz | `CF2.kesselstatus_anzeige_sh` | s16 | 04 | r | r |
| 8214 | Sauerstoff Ist | `KSM.O2Ist` | s16 | 04 | r | r |
| 8215 | Flammtemperatur Ist (value) | `KSM.i_flammtemp_ist.value` | s16 | 04 | r | r |
| 8216 | Flammtemperatur Ist (status) | `KSM.i_flammtemp_ist.status` | s16 | 04 | r | r |
| 8218 | Unterdruck Ist | `KSM.AI_Feuerraum_Unterdruck` | s16 | 04 | r | r |
| 8221 | Primärgebläse | `AK.pl_geblaesestufe` | s16 | 04 | r | r |
| 8223 | Saugzugstufe | `KSM.Saugzugstufe` | s16 | 04 | r | r |
| 8224 | Nächste Wartung in | `KSM.ServiceintervallReststunden` | s16 | 04 | r | r |
| 8226 | Antrieb Fördersystem | `FS.o_motor_foerdersystem_1` | s16 | 04 | r | r |
| 8227 | Extern 1 | `KSM.i_extern1` | s16 | 04 | r | r |
| 8228 | Extern 2 | `KSM.i_extern2` | s16 | 04 | r | r |
| 8229 | Extern 3 | `KSM.i_extern3` | s16 | 04 | r | r |
| 8233 | Brennstoffverbrauch | `FS.pelletsverbrauch` | u32 | 04 | r | r |
| 8235 | Brennstofffaktor | `EF2.Brennstofffaktor` | s16 | 04 | r | r |
| 8236 | Brennerleistung extern | `AK.externe_brennerleistung` | s16 | 04 | r | r |
| 8237 | Kesseltemp. Soll Extern | `AK.externe_kessel_solltemperatur` | s16 | 04 | r | r |
| 8238 | Saugturbine | `KSM.DO_Pelletssauger` | s16 | 04 | r | r |
| 8242 | Primärluftklappe | `CF2.i_pl_klappe_ist_promille` | s16 | 04 | r | r |
| 8243 | Sekundärluftklappe | `CF2.i_sl_klappe_ist_promille` | s16 | 04 | r | r |
| 8244 | Betriebsmodus | `CF2.betriebsmodus` | s16 | 04 | r | r |
| 8245 | Füllraumtüre | `CF2.i_tuer_geschlossen` | s16 | 04 | r | r |
| 8246 | Maximaler Befüllgrad | `CF2.max_befuellgrad_anzeige` | s16 | 04 | r | r |
| 8247 | Zündung Heizung | `CF2.o_zuendung_heizung_sh` | s16 | 04 | r | r |
| 8248 | Volllaststunden | `CF2.PM_Betriebsminuten_Summe` | u32 | 04 | r | r |
| 9044 | Multifunktionsausgang 1 (125) | `KSM.o_multifunktionsausgang_1` | s16 | 04 | r | r |
| 9045 | Multifunktionsausgang 2 (127) | `KSM.o_multifunktionsausgang_2` | s16 | 04 | r | r |
| 9046 | Multifunktionsausgang 3 (124) | `KSM.o_multifunktionsausgang_3` | s16 | 04 | r | r |
| 9047 | Multifunktionsausgang 4 (126) | `KSM.o_multifunktionsausgang_4` | s16 | 04 | r | r |
| 9495 | Modbus Überhitzung | `KSM.modbus_ueberhitzung` | s16 | 04 | r | r |
| 9496 | Modbus Wärmeabnahme Max | `KSM.modbus_waermeabnahme_max` | s16 | 04 | r | r |
| 9497 | Füllstand Aschebehälter | `KSM.aschefuellstand` | u16 | 04 | r | r |
| 9498 | Drehzahl Saugzug | `KSM.i_drehzahl_saugzug` | u16 | 04 | r | r |
| 9877 | Brennerleistung bestimmt durch | `AK.anforderung_bl_ursache` | s16 | 04 | r | r |
| 9878 | Wärmemenge gesamt | `KSM.waermemenge_gesamt_kwh` | u32 | 04 | r | r |
| 9970 | Pelletkesselstatus | `KSM.kesselstatus_anzeige_simple` | s16 | 04 | r | r |
| 9988 | Brennstoffverbrauch Rücksetzzähler | `FS.pelletverbrauch_reset_counter` | u16 | 04 | r | r |
| 24576 | Kessel Ein/Aus | `AK.anlage_ein` | s16 | 03 | rw | rw |
| 24577 | Solltemperatur 1 | `EF2.KesseltempSoll1` | s16 | 03 | r | rw |
| 24578 | Solltemperatur 2 | `EF2.KesseltempSoll2` | s16 | 03 | r | rw |
| 24581 | Rücklauftemperatur Minimum | `KSM.RuecklauftempMin` | s16 | 03 | r | rw |
| 24583 | Externe Vorgabe | `AK.externe_vorgabe` | s16 | 03 | r | rw |
| 24584 | Kesselprogramm | `AK.kesselprogramm` | s16 | 03 | r | rw |
| 24585 | Kesseltemperatur Soll | `CF2.kesseltemp_soll_1` | s16 | 03 | rw | rw |
| 24586 | Automatische Zündung Funktion | `CF2.automatische_Zuendung_SH` | s16 | 03 | r | rw |
| 24849 | Modbus Lifetick | `KSM.modbus_lifetick` | u16 | 03 | r | rw |
| 24850 | Modbus Commit Lifetick | `KSM.modbus_commit_lifetick` | u16 | 03 | r | r |
| 24851 | Modbus Kesseltemperatur | `KSM.modbus_kesseltemp_vorgabe` | s16 | 03 | r | rw |
| 24852 | Modbus Kesselleistung | `KSM.modbus_leistung_vorgabe` | s16 | 03 | r | rw |
| 24854 | Modbus Kesselanforderung | `KSM.modbus_kesselanforderung` | s16 | 03 | r | rw |
| 24927 | Restmenge Brennstofflager | `KSM.restmenge_brennstofflager` | u32 | 03 | rw | rw |
| 24932 | Modbus Puffertemperatur oben für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_oben.value` | s16 | 03 | r | rw |
| 24933 | Modbus Puffertemperatur oben für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_oben.status` | s16 | 03 | r | rw |
| 24934 | Modbus Puffertemperatur unten für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_unten.value` | s16 | 03 | r | rw |
| 24935 | Modbus Puffertemperatur unten für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_unten.status` | s16 | 03 | r | rw |
| 25040 | Modbus Überstromnutzung | `SYSTEM.modbus_clee_ueberschusstrom` | s16 | 03 | r | rw |

### KWB CF 2 (`kwb_cf2.json`, 67 Register)

| Adresse | Name (mit Slot) | Parameter | Typ | FC | User | Expert |
|---:|---|---|---|:---:|:---:|:---:|
| 8197 | Kesseltemperatur Ist (value) | `KSM.i_kesseltemp_ist.value` | s16 | 04 | r | r |
| 8198 | Kesseltemperatur Ist (status) | `KSM.i_kesseltemp_ist.status` | s16 | 04 | r | r |
| 8199 | Kesseltemperatur Soll | `KSM.kesseltemp_soll` | s16 | 04 | r | r |
| 8200 | Kesselpumpe | `KSM.DO_Kesselpumpe` | s16 | 04 | r | r |
| 8201 | Kesselpumpe % | `KSM.kesselpumpe_steuerstufe` | u16 | 04 | r | r |
| 8202 | Rücklauftemperatur Ist (value) | `KSM.i_ruecklauftemp_ist.value` | s16 | 04 | r | r |
| 8203 | Rücklauftemperatur Ist (status) | `KSM.i_ruecklauftemp_ist.status` | s16 | 04 | r | r |
| 8206 | Verbraucher Anforderung | `KSM.verbraucher_anforderung` | s16 | 04 | r | r |
| 8207 | Kesselleistung | `KSM.brennerleistung` | s16 | 04 | r | r |
| 8208 | Kesselstatus | `KSM.kesselstatus_anzeige` | s16 | 04 | r | r |
| 8209 | Volllaststunden | `KSM.Betriebsminuten_Summe` | u32 | 04 | r | r |
| 8211 | Status Pelletmodul | `AK.kesselstatus_anzeige_ak` | s16 | 04 | r | r |
| 8212 | Status Stückholz | `CF2.kesselstatus_anzeige_sh` | s16 | 04 | r | r |
| 8214 | Sauerstoff Ist | `KSM.O2Ist` | s16 | 04 | r | r |
| 8215 | Flammtemperatur Ist (value) | `KSM.i_flammtemp_ist.value` | s16 | 04 | r | r |
| 8216 | Flammtemperatur Ist (status) | `KSM.i_flammtemp_ist.status` | s16 | 04 | r | r |
| 8218 | Unterdruck Ist | `KSM.AI_Feuerraum_Unterdruck` | s16 | 04 | r | r |
| 8221 | Primärgebläse | `AK.pl_geblaesestufe` | s16 | 04 | r | r |
| 8223 | Saugzugstufe | `KSM.Saugzugstufe` | s16 | 04 | r | r |
| 8224 | Nächste Wartung in | `KSM.ServiceintervallReststunden` | s16 | 04 | r | r |
| 8226 | Antrieb Fördersystem | `FS.o_motor_foerdersystem_1` | s16 | 04 | r | r |
| 8227 | Extern 1 | `KSM.i_extern1` | s16 | 04 | r | r |
| 8228 | Extern 2 | `KSM.i_extern2` | s16 | 04 | r | r |
| 8229 | Extern 3 | `KSM.i_extern3` | s16 | 04 | r | r |
| 8233 | Brennstoffverbrauch | `FS.pelletsverbrauch` | u32 | 04 | r | r |
| 8235 | Brennstofffaktor | `EF2.Brennstofffaktor` | s16 | 04 | r | r |
| 8236 | Brennerleistung extern | `AK.externe_brennerleistung` | s16 | 04 | r | r |
| 8237 | Kesseltemp. Soll Extern | `AK.externe_kessel_solltemperatur` | s16 | 04 | r | r |
| 8238 | Saugturbine | `KSM.DO_Pelletssauger` | s16 | 04 | r | r |
| 8242 | Primärluftklappe | `CF2.i_pl_klappe_ist_promille` | s16 | 04 | r | r |
| 8243 | Sekundärluftklappe | `CF2.i_sl_klappe_ist_promille` | s16 | 04 | r | r |
| 8244 | Betriebsmodus | `CF2.betriebsmodus` | s16 | 04 | r | r |
| 8245 | Füllraumtüre | `CF2.i_tuer_geschlossen` | s16 | 04 | r | r |
| 8246 | Maximaler Befüllgrad | `CF2.max_befuellgrad_anzeige` | s16 | 04 | r | r |
| 8247 | Zündung Heizung | `CF2.o_zuendung_heizung_sh` | s16 | 04 | r | r |
| 8248 | Volllaststunden | `CF2.PM_Betriebsminuten_Summe` | u32 | 04 | r | r |
| 9044 | Multifunktionsausgang 1 (125) | `KSM.o_multifunktionsausgang_1` | s16 | 04 | r | r |
| 9045 | Multifunktionsausgang 2 (127) | `KSM.o_multifunktionsausgang_2` | s16 | 04 | r | r |
| 9046 | Multifunktionsausgang 3 (124) | `KSM.o_multifunktionsausgang_3` | s16 | 04 | r | r |
| 9047 | Multifunktionsausgang 4 (126) | `KSM.o_multifunktionsausgang_4` | s16 | 04 | r | r |
| 9495 | Modbus Überhitzung | `KSM.modbus_ueberhitzung` | s16 | 04 | r | r |
| 9496 | Modbus Wärmeabnahme Max | `KSM.modbus_waermeabnahme_max` | s16 | 04 | r | r |
| 9497 | Füllstand Aschebehälter | `KSM.aschefuellstand` | u16 | 04 | r | r |
| 9498 | Drehzahl Saugzug | `KSM.i_drehzahl_saugzug` | u16 | 04 | r | r |
| 9877 | Brennerleistung bestimmt durch | `AK.anforderung_bl_ursache` | s16 | 04 | r | r |
| 9878 | Wärmemenge gesamt | `KSM.waermemenge_gesamt_kwh` | u32 | 04 | r | r |
| 9970 | Pelletkesselstatus | `KSM.kesselstatus_anzeige_simple` | s16 | 04 | r | r |
| 9988 | Brennstoffverbrauch Rücksetzzähler | `FS.pelletverbrauch_reset_counter` | u16 | 04 | r | r |
| 24576 | Kessel Ein/Aus | `AK.anlage_ein` | s16 | 03 | rw | rw |
| 24577 | Solltemperatur 1 | `EF2.KesseltempSoll1` | s16 | 03 | r | rw |
| 24578 | Solltemperatur 2 | `EF2.KesseltempSoll2` | s16 | 03 | r | rw |
| 24581 | Rücklauftemperatur Minimum | `KSM.RuecklauftempMin` | s16 | 03 | r | rw |
| 24583 | Externe Vorgabe | `AK.externe_vorgabe` | s16 | 03 | r | rw |
| 24584 | Kesselprogramm | `AK.kesselprogramm` | s16 | 03 | r | rw |
| 24585 | Kesseltemperatur Soll | `CF2.kesseltemp_soll_1` | s16 | 03 | rw | rw |
| 24586 | Automatische Zündung Funktion | `CF2.automatische_Zuendung_SH` | s16 | 03 | r | rw |
| 24849 | Modbus Lifetick | `KSM.modbus_lifetick` | u16 | 03 | r | rw |
| 24850 | Modbus Commit Lifetick | `KSM.modbus_commit_lifetick` | u16 | 03 | r | r |
| 24851 | Modbus Kesseltemperatur | `KSM.modbus_kesseltemp_vorgabe` | s16 | 03 | r | rw |
| 24852 | Modbus Kesselleistung | `KSM.modbus_leistung_vorgabe` | s16 | 03 | r | rw |
| 24854 | Modbus Kesselanforderung | `KSM.modbus_kesselanforderung` | s16 | 03 | r | rw |
| 24927 | Restmenge Brennstofflager | `KSM.restmenge_brennstofflager` | u32 | 03 | rw | rw |
| 24932 | Modbus Puffertemperatur oben für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_oben.value` | s16 | 03 | r | rw |
| 24933 | Modbus Puffertemperatur oben für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_oben.status` | s16 | 03 | r | rw |
| 24934 | Modbus Puffertemperatur unten für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_unten.value` | s16 | 03 | r | rw |
| 24935 | Modbus Puffertemperatur unten für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_unten.status` | s16 | 03 | r | rw |
| 25040 | Modbus Überstromnutzung | `SYSTEM.modbus_clee_ueberschusstrom` | s16 | 03 | r | rw |

### KWB CF 1 (`kwb_cf1.json`, 69 Register)

| Adresse | Name (mit Slot) | Parameter | Typ | FC | User | Expert |
|---:|---|---|---|:---:|:---:|:---:|
| 8197 | Kesseltemperatur Ist (value) | `KSM.i_kesseltemp_ist.value` | s16 | 04 | r | r |
| 8198 | Kesseltemperatur Ist (status) | `KSM.i_kesseltemp_ist.status` | s16 | 04 | r | r |
| 8199 | Kesseltemperatur Soll | `KSM.kesseltemp_soll` | s16 | 04 | r | r |
| 8200 | Kesselpumpe | `KSM.DO_Kesselpumpe` | s16 | 04 | r | r |
| 8201 | Kesselpumpe % | `KSM.kesselpumpe_steuerstufe` | u16 | 04 | r | r |
| 8202 | Rücklauftemperatur Ist (value) | `KSM.i_ruecklauftemp_ist.value` | s16 | 04 | r | r |
| 8203 | Rücklauftemperatur Ist (status) | `KSM.i_ruecklauftemp_ist.status` | s16 | 04 | r | r |
| 8206 | Verbraucher Anforderung | `KSM.verbraucher_anforderung` | s16 | 04 | r | r |
| 8207 | Kesselleistung | `KSM.brennerleistung` | s16 | 04 | r | r |
| 8208 | Kesselstatus | `KSM.kesselstatus_anzeige` | s16 | 04 | r | r |
| 8209 | Volllaststunden | `KSM.Betriebsminuten_Summe` | u32 | 04 | r | r |
| 8211 | Status Pelletmodul | `AK.kesselstatus_anzeige_ak` | s16 | 04 | r | r |
| 8212 | Status Stückholz | `CF2.kesselstatus_anzeige_sh` | s16 | 04 | r | r |
| 8214 | Sauerstoff Ist | `KSM.O2Ist` | s16 | 04 | r | r |
| 8215 | Flammtemperatur Ist (value) | `KSM.i_flammtemp_ist.value` | s16 | 04 | r | r |
| 8216 | Flammtemperatur Ist (status) | `KSM.i_flammtemp_ist.status` | s16 | 04 | r | r |
| 8218 | Unterdruck Ist | `KSM.AI_Feuerraum_Unterdruck` | s16 | 04 | r | r |
| 8221 | Primärgebläse | `AK.pl_geblaesestufe` | s16 | 04 | r | r |
| 8223 | Saugzugstufe | `KSM.Saugzugstufe` | s16 | 04 | r | r |
| 8224 | Nächste Wartung in | `KSM.ServiceintervallReststunden` | s16 | 04 | r | r |
| 8226 | Antrieb Fördersystem | `FS.o_motor_foerdersystem_1` | s16 | 04 | r | r |
| 8227 | Extern 1 | `KSM.i_extern1` | s16 | 04 | r | r |
| 8228 | Extern 2 | `KSM.i_extern2` | s16 | 04 | r | r |
| 8229 | Extern 3 | `KSM.i_extern3` | s16 | 04 | r | r |
| 8231 | Abgastemperatur (value) | `KSM.i_rauchgastemp_ist.value` | s16 | 04 | r | r |
| 8232 | Abgastemperatur (status) | `KSM.i_rauchgastemp_ist.status` | s16 | 04 | r | r |
| 8233 | Brennstoffverbrauch | `FS.pelletsverbrauch` | u32 | 04 | r | r |
| 8235 | Brennstofffaktor | `EF2.Brennstofffaktor` | s16 | 04 | r | r |
| 8236 | Brennerleistung extern | `AK.externe_brennerleistung` | s16 | 04 | r | r |
| 8237 | Kesseltemp. Soll Extern | `AK.externe_kessel_solltemperatur` | s16 | 04 | r | r |
| 8238 | Saugturbine | `KSM.DO_Pelletssauger` | s16 | 04 | r | r |
| 8242 | Primärluftklappe | `CF2.i_pl_klappe_ist_promille` | s16 | 04 | r | r |
| 8243 | Sekundärluftklappe | `CF2.i_sl_klappe_ist_promille` | s16 | 04 | r | r |
| 8244 | Betriebsmodus | `CF2.betriebsmodus` | s16 | 04 | r | r |
| 8245 | Füllraumtüre | `CF2.i_tuer_geschlossen` | s16 | 04 | r | r |
| 8246 | Maximaler Befüllgrad | `CF2.max_befuellgrad_anzeige` | s16 | 04 | r | r |
| 8247 | Zündung Heizung | `CF2.o_zuendung_heizung_sh` | s16 | 04 | r | r |
| 8248 | Volllaststunden | `CF2.PM_Betriebsminuten_Summe` | u32 | 04 | r | r |
| 9044 | Multifunktionsausgang 1 (125) | `KSM.o_multifunktionsausgang_1` | s16 | 04 | r | r |
| 9045 | Multifunktionsausgang 2 (127) | `KSM.o_multifunktionsausgang_2` | s16 | 04 | r | r |
| 9046 | Multifunktionsausgang 3 (124) | `KSM.o_multifunktionsausgang_3` | s16 | 04 | r | r |
| 9047 | Multifunktionsausgang 4 (126) | `KSM.o_multifunktionsausgang_4` | s16 | 04 | r | r |
| 9495 | Modbus Überhitzung | `KSM.modbus_ueberhitzung` | s16 | 04 | r | r |
| 9496 | Modbus Wärmeabnahme Max | `KSM.modbus_waermeabnahme_max` | s16 | 04 | r | r |
| 9497 | Füllstand Aschebehälter | `KSM.aschefuellstand` | u16 | 04 | r | r |
| 9498 | Drehzahl Saugzug | `KSM.i_drehzahl_saugzug` | u16 | 04 | r | r |
| 9877 | Brennerleistung bestimmt durch | `AK.anforderung_bl_ursache` | s16 | 04 | r | r |
| 9878 | Wärmemenge gesamt | `KSM.waermemenge_gesamt_kwh` | u32 | 04 | r | r |
| 9970 | Pelletkesselstatus | `KSM.kesselstatus_anzeige_simple` | s16 | 04 | r | r |
| 9988 | Brennstoffverbrauch Rücksetzzähler | `FS.pelletverbrauch_reset_counter` | u16 | 04 | r | r |
| 24576 | Kessel Ein/Aus | `AK.anlage_ein` | s16 | 03 | rw | rw |
| 24577 | Solltemperatur 1 | `EF2.KesseltempSoll1` | s16 | 03 | r | rw |
| 24578 | Solltemperatur 2 | `EF2.KesseltempSoll2` | s16 | 03 | r | rw |
| 24581 | Rücklauftemperatur Minimum | `KSM.RuecklauftempMin` | s16 | 03 | r | rw |
| 24583 | Externe Vorgabe | `AK.externe_vorgabe` | s16 | 03 | r | rw |
| 24584 | Kesselprogramm | `AK.kesselprogramm` | s16 | 03 | r | rw |
| 24585 | Kesseltemperatur Soll | `CF2.kesseltemp_soll_1` | s16 | 03 | rw | rw |
| 24586 | Automatische Zündung Funktion | `CF2.automatische_Zuendung_SH` | s16 | 03 | r | rw |
| 24849 | Modbus Lifetick | `KSM.modbus_lifetick` | u16 | 03 | r | rw |
| 24850 | Modbus Commit Lifetick | `KSM.modbus_commit_lifetick` | u16 | 03 | r | r |
| 24851 | Modbus Kesseltemperatur | `KSM.modbus_kesseltemp_vorgabe` | s16 | 03 | r | rw |
| 24852 | Modbus Kesselleistung | `KSM.modbus_leistung_vorgabe` | s16 | 03 | r | rw |
| 24854 | Modbus Kesselanforderung | `KSM.modbus_kesselanforderung` | s16 | 03 | r | rw |
| 24927 | Restmenge Brennstofflager | `KSM.restmenge_brennstofflager` | u32 | 03 | rw | rw |
| 24932 | Modbus Puffertemperatur oben für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_oben.value` | s16 | 03 | r | rw |
| 24933 | Modbus Puffertemperatur oben für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_oben.status` | s16 | 03 | r | rw |
| 24934 | Modbus Puffertemperatur unten für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_unten.value` | s16 | 03 | r | rw |
| 24935 | Modbus Puffertemperatur unten für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_unten.status` | s16 | 03 | r | rw |
| 25040 | Modbus Überstromnutzung | `SYSTEM.modbus_clee_ueberschusstrom` | s16 | 03 | r | rw |

### KWB CF 1.5 (`kwb_cf1_5.json`, 67 Register)

| Adresse | Name (mit Slot) | Parameter | Typ | FC | User | Expert |
|---:|---|---|---|:---:|:---:|:---:|
| 8197 | Kesseltemperatur Ist (value) | `KSM.i_kesseltemp_ist.value` | s16 | 04 | r | r |
| 8198 | Kesseltemperatur Ist (status) | `KSM.i_kesseltemp_ist.status` | s16 | 04 | r | r |
| 8199 | Kesseltemperatur Soll | `KSM.kesseltemp_soll` | s16 | 04 | r | r |
| 8200 | Kesselpumpe | `KSM.DO_Kesselpumpe` | s16 | 04 | r | r |
| 8201 | Kesselpumpe % | `KSM.kesselpumpe_steuerstufe` | u16 | 04 | r | r |
| 8202 | Rücklauftemperatur Ist (value) | `KSM.i_ruecklauftemp_ist.value` | s16 | 04 | r | r |
| 8203 | Rücklauftemperatur Ist (status) | `KSM.i_ruecklauftemp_ist.status` | s16 | 04 | r | r |
| 8206 | Verbraucher Anforderung | `KSM.verbraucher_anforderung` | s16 | 04 | r | r |
| 8207 | Kesselleistung | `KSM.brennerleistung` | s16 | 04 | r | r |
| 8208 | Kesselstatus | `KSM.kesselstatus_anzeige` | s16 | 04 | r | r |
| 8209 | Volllaststunden | `KSM.Betriebsminuten_Summe` | u32 | 04 | r | r |
| 8211 | Status Pelletmodul | `AK.kesselstatus_anzeige_ak` | s16 | 04 | r | r |
| 8212 | Status Stückholz | `CF2.kesselstatus_anzeige_sh` | s16 | 04 | r | r |
| 8214 | Sauerstoff Ist | `KSM.O2Ist` | s16 | 04 | r | r |
| 8215 | Flammtemperatur Ist (value) | `KSM.i_flammtemp_ist.value` | s16 | 04 | r | r |
| 8216 | Flammtemperatur Ist (status) | `KSM.i_flammtemp_ist.status` | s16 | 04 | r | r |
| 8218 | Unterdruck Ist | `KSM.AI_Feuerraum_Unterdruck` | s16 | 04 | r | r |
| 8221 | Primärgebläse | `AK.pl_geblaesestufe` | s16 | 04 | r | r |
| 8223 | Saugzugstufe | `KSM.Saugzugstufe` | s16 | 04 | r | r |
| 8224 | Nächste Wartung in | `KSM.ServiceintervallReststunden` | s16 | 04 | r | r |
| 8226 | Antrieb Fördersystem | `FS.o_motor_foerdersystem_1` | s16 | 04 | r | r |
| 8227 | Extern 1 | `KSM.i_extern1` | s16 | 04 | r | r |
| 8228 | Extern 2 | `KSM.i_extern2` | s16 | 04 | r | r |
| 8229 | Extern 3 | `KSM.i_extern3` | s16 | 04 | r | r |
| 8233 | Brennstoffverbrauch | `FS.pelletsverbrauch` | u32 | 04 | r | r |
| 8235 | Brennstofffaktor | `EF2.Brennstofffaktor` | s16 | 04 | r | r |
| 8236 | Brennerleistung extern | `AK.externe_brennerleistung` | s16 | 04 | r | r |
| 8237 | Kesseltemp. Soll Extern | `AK.externe_kessel_solltemperatur` | s16 | 04 | r | r |
| 8238 | Saugturbine | `KSM.DO_Pelletssauger` | s16 | 04 | r | r |
| 8242 | Primärluftklappe | `CF2.i_pl_klappe_ist_promille` | s16 | 04 | r | r |
| 8243 | Sekundärluftklappe | `CF2.i_sl_klappe_ist_promille` | s16 | 04 | r | r |
| 8244 | Betriebsmodus | `CF2.betriebsmodus` | s16 | 04 | r | r |
| 8245 | Füllraumtüre | `CF2.i_tuer_geschlossen` | s16 | 04 | r | r |
| 8246 | Maximaler Befüllgrad | `CF2.max_befuellgrad_anzeige` | s16 | 04 | r | r |
| 8247 | Zündung Heizung | `CF2.o_zuendung_heizung_sh` | s16 | 04 | r | r |
| 8248 | Volllaststunden | `CF2.PM_Betriebsminuten_Summe` | u32 | 04 | r | r |
| 9044 | Multifunktionsausgang 1 (125) | `KSM.o_multifunktionsausgang_1` | s16 | 04 | r | r |
| 9045 | Multifunktionsausgang 2 (127) | `KSM.o_multifunktionsausgang_2` | s16 | 04 | r | r |
| 9046 | Multifunktionsausgang 3 (124) | `KSM.o_multifunktionsausgang_3` | s16 | 04 | r | r |
| 9047 | Multifunktionsausgang 4 (126) | `KSM.o_multifunktionsausgang_4` | s16 | 04 | r | r |
| 9495 | Modbus Überhitzung | `KSM.modbus_ueberhitzung` | s16 | 04 | r | r |
| 9496 | Modbus Wärmeabnahme Max | `KSM.modbus_waermeabnahme_max` | s16 | 04 | r | r |
| 9497 | Füllstand Aschebehälter | `KSM.aschefuellstand` | u16 | 04 | r | r |
| 9498 | Drehzahl Saugzug | `KSM.i_drehzahl_saugzug` | u16 | 04 | r | r |
| 9877 | Brennerleistung bestimmt durch | `AK.anforderung_bl_ursache` | s16 | 04 | r | r |
| 9878 | Wärmemenge gesamt | `KSM.waermemenge_gesamt_kwh` | u32 | 04 | r | r |
| 9970 | Pelletkesselstatus | `KSM.kesselstatus_anzeige_simple` | s16 | 04 | r | r |
| 9988 | Brennstoffverbrauch Rücksetzzähler | `FS.pelletverbrauch_reset_counter` | u16 | 04 | r | r |
| 24576 | Kessel Ein/Aus | `AK.anlage_ein` | s16 | 03 | rw | rw |
| 24577 | Solltemperatur 1 | `EF2.KesseltempSoll1` | s16 | 03 | r | rw |
| 24578 | Solltemperatur 2 | `EF2.KesseltempSoll2` | s16 | 03 | r | rw |
| 24581 | Rücklauftemperatur Minimum | `KSM.RuecklauftempMin` | s16 | 03 | r | rw |
| 24583 | Externe Vorgabe | `AK.externe_vorgabe` | s16 | 03 | r | rw |
| 24584 | Kesselprogramm | `AK.kesselprogramm` | s16 | 03 | r | rw |
| 24585 | Kesseltemperatur Soll | `CF2.kesseltemp_soll_1` | s16 | 03 | rw | rw |
| 24586 | Automatische Zündung Funktion | `CF2.automatische_Zuendung_SH` | s16 | 03 | r | rw |
| 24849 | Modbus Lifetick | `KSM.modbus_lifetick` | u16 | 03 | r | rw |
| 24850 | Modbus Commit Lifetick | `KSM.modbus_commit_lifetick` | u16 | 03 | r | r |
| 24851 | Modbus Kesseltemperatur | `KSM.modbus_kesseltemp_vorgabe` | s16 | 03 | r | rw |
| 24852 | Modbus Kesselleistung | `KSM.modbus_leistung_vorgabe` | s16 | 03 | r | rw |
| 24854 | Modbus Kesselanforderung | `KSM.modbus_kesselanforderung` | s16 | 03 | r | rw |
| 24927 | Restmenge Brennstofflager | `KSM.restmenge_brennstofflager` | u32 | 03 | rw | rw |
| 24932 | Modbus Puffertemperatur oben für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_oben.value` | s16 | 03 | r | rw |
| 24933 | Modbus Puffertemperatur oben für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_oben.status` | s16 | 03 | r | rw |
| 24934 | Modbus Puffertemperatur unten für Restwärmenutzung (value) | `KSM.modbus_puffertemperatur_unten.value` | s16 | 03 | r | rw |
| 24935 | Modbus Puffertemperatur unten für Restwärmenutzung (status) | `KSM.modbus_puffertemperatur_unten.status` | s16 | 03 | r | rw |
| 25040 | Modbus Überstromnutzung | `SYSTEM.modbus_clee_ueberschusstrom` | s16 | 03 | r | rw |

### KWB EasyAir Plus (`kwb_easyair_plus.json`, 97 Register)

| Adresse | Name (mit Slot) | Parameter | Typ | FC | User | Expert |
|---:|---|---|---|:---:|:---:|:---:|
| 10230 | EAP 0: WEZ Solltemperatur | `EAPDEV.vorlauftemperatur_soll` | s16 | 04 | r | r |
| 10231 | EAP 1: WEZ Solltemperatur | `EAPDEV.vorlauftemperatur_soll` | s16 | 04 | r | r |
| 10238 | EAP 0: Momentanleistung | `EAPDEV.momentanleistung` | u16 | 04 | r | r |
| 10239 | EAP 1: Momentanleistung | `EAPDEV.momentanleistung` | u16 | 04 | r | r |
| 10246 | EAP 0: Verdichter Drehzahl Ist | `EAPDEV.drehzahl_ist` | u16 | 04 | r | r |
| 10247 | EAP 1: Verdichter Drehzahl Ist | `EAPDEV.drehzahl_ist` | u16 | 04 | r | r |
| 10254 | EAP 0: Verdichter Drehzahl Soll | `EAPDEV.drehzahl_soll` | u16 | 04 | r | r |
| 10255 | EAP 1: Verdichter Drehzahl Soll | `EAPDEV.drehzahl_soll` | u16 | 04 | r | r |
| 10262 | EAP 0: Aufgen. elektr. Leistung | `EAPDEV.aufgenommene_elektr_leistung` | u16 | 04 | r | r |
| 10263 | EAP 1: Aufgen. elektr. Leistung | `EAPDEV.aufgenommene_elektr_leistung` | u16 | 04 | r | r |
| 10270 | EAP 0: Vorlauftemperatur Ist | `EAPDEV.vorlauftemperatur_ist` | s16 | 04 | r | r |
| 10271 | EAP 1: Vorlauftemperatur Ist | `EAPDEV.vorlauftemperatur_ist` | s16 | 04 | r | r |
| 10278 | EAP 0: Rücklauftemperatur Ist | `EAPDEV.ruecklauftemperatur_ist` | s16 | 04 | r | r |
| 10279 | EAP 1: Rücklauftemperatur Ist | `EAPDEV.ruecklauftemperatur_ist` | s16 | 04 | r | r |
| 10286 | EAP 0: Ansauglufttemperatur | `EAPDEV.ansauglufttemperatur` | s16 | 04 | r | r |
| 10287 | EAP 1: Ansauglufttemperatur | `EAPDEV.ansauglufttemperatur` | s16 | 04 | r | r |
| 10294 | EAP 0: Sauggastemperatur | `EAPDEV.sauggastemperatur` | s16 | 04 | r | r |
| 10295 | EAP 1: Sauggastemperatur | `EAPDEV.sauggastemperatur` | s16 | 04 | r | r |
| 10302 | EAP 0: Heissgastemperatur | `EAPDEV.heissgastemperatur` | s16 | 04 | r | r |
| 10303 | EAP 1: Heissgastemperatur | `EAPDEV.heissgastemperatur` | s16 | 04 | r | r |
| 10310 | EAP 0: Drehzahl Ventilator | `EAPDEV.drehzahl_ventilator` | u16 | 04 | r | r |
| 10311 | EAP 1: Drehzahl Ventilator | `EAPDEV.drehzahl_ventilator` | u16 | 04 | r | r |
| 10318 | EAP 0: Volumenstrom | `EAPDEV.volumenstrom` | u16 | 04 | r | r |
| 10319 | EAP 1: Volumenstrom | `EAPDEV.volumenstrom` | u16 | 04 | r | r |
| 10326 | EAP 0: Volumenstrom gemittelt | `EAPDEV.volumenstrom_gemittelt` | u16 | 04 | r | r |
| 10327 | EAP 1: Volumenstrom gemittelt | `EAPDEV.volumenstrom_gemittelt` | u16 | 04 | r | r |
| 10334 | EAP 0: Drehzahl CP | `EAPDEV.drehzahl_cp` | s16 | 04 | r | r |
| 10335 | EAP 1: Drehzahl CP | `EAPDEV.drehzahl_cp` | s16 | 04 | r | r |
| 10342 | EAP 0: Überhitzung | `EAPDEV.ueberhitzung` | s16 | 04 | r | r |
| 10343 | EAP 1: Überhitzung | `EAPDEV.ueberhitzung` | s16 | 04 | r | r |
| 10350 | EAP 0: Unterkühlung | `EAPDEV.unterkuehlung` | s16 | 04 | r | r |
| 10351 | EAP 1: Unterkühlung | `EAPDEV.unterkuehlung` | s16 | 04 | r | r |
| 10358 | EAP 0: Verdampfungstemperatur | `EAPDEV.verdampfungstemperatur` | s16 | 04 | r | r |
| 10359 | EAP 1: Verdampfungstemperatur | `EAPDEV.verdampfungstemperatur` | s16 | 04 | r | r |
| 10366 | EAP 0: Kondensationstemperatur | `EAPDEV.kondensationstemperatur` | s16 | 04 | r | r |
| 10367 | EAP 1: Kondensationstemperatur | `EAPDEV.kondensationstemperatur` | s16 | 04 | r | r |
| 10374 | EAP 0: Niederdruck (relativ) | `EAPDEV.niederdruck` | u16 | 04 | r | r |
| 10375 | EAP 1: Niederdruck (relativ) | `EAPDEV.niederdruck` | u16 | 04 | r | r |
| 10382 | EAP 0: Hochdruck (relativ) | `EAPDEV.hochdruck` | u16 | 04 | r | r |
| 10383 | EAP 1: Hochdruck (relativ) | `EAPDEV.hochdruck` | u16 | 04 | r | r |
| 10390 | EAP 0: Temp. Flüssigkeitsleitung | `EAPDEV.temperatur_fluessigkeitsleitung` | s16 | 04 | r | r |
| 10391 | EAP 1: Temp. Flüssigkeitsleitung | `EAPDEV.temperatur_fluessigkeitsleitung` | s16 | 04 | r | r |
| 10398 | EAP 0: Position 1. EX-Ventil | `EAPDEV.position_erstes_expansionsventil` | u16 | 04 | r | r |
| 10399 | EAP 1: Position 1. EX-Ventil | `EAPDEV.position_erstes_expansionsventil` | u16 | 04 | r | r |
| 10406 | EAP 0: Position 2. EX-Ventil | `EAPDEV.position_zweites_expansionsventi` | u16 | 04 | r | r |
| 10407 | EAP 1: Position 2. EX-Ventil | `EAPDEV.position_zweites_expansionsventi` | u16 | 04 | r | r |
| 10414 | EAP 0: Bivalenz-ELH | `EAPDEV.bivalenz_elh` | s16 | 04 | r | r |
| 10415 | EAP 1: Bivalenz-ELH | `EAPDEV.bivalenz_elh` | s16 | 04 | r | r |
| 10422 | EAP 0: COP | `EAPDEV.cop` | u16 | 04 | r | r |
| 10423 | EAP 1: COP | `EAPDEV.cop` | u16 | 04 | r | r |
| 10430 | EAP 0: Erw. Betriebsstatus | `EAPDEV.erweiterter_betriebsstatus` | s16 | 04 | r | r |
| 10431 | EAP 1: Erw. Betriebsstatus | `EAPDEV.erweiterter_betriebsstatus` | s16 | 04 | r | r |
| 10438 | EAP 0: Status | `EAPDEV.status` | s16 | 04 | r | r |
| 10439 | EAP 1: Status | `EAPDEV.status` | s16 | 04 | r | r |
| 10446 | EAP 0: Anforderung durch | `EAPDEV.anforderung_ursache` | s16 | 04 | r | r |
| 10447 | EAP 1: Anforderung durch | `EAPDEV.anforderung_ursache` | s16 | 04 | r | r |
| 10454 | EAP 0: Zustand Wärmepumpe | `EAPDEV.zustand_waermepumpe` | s16 | 04 | r | r |
| 10455 | EAP 1: Zustand Wärmepumpe | `EAPDEV.zustand_waermepumpe` | s16 | 04 | r | r |
| 24849 | Modbus Lifetick | `KSM.modbus_lifetick` | u16 | 03 | r | rw |
| 24850 | Modbus Commit Lifetick | `KSM.modbus_commit_lifetick` | u16 | 03 | r | r |
| 25168 | EAP 0: Sollwert für Heizen | `EAPDEV.sollwert_heizkreisbetrieb` | s16 | 03 | r | r |
| 25169 | EAP 1: Sollwert für Heizen | `EAPDEV.sollwert_heizkreisbetrieb` | s16 | 03 | r | r |
| 25176 | EAP 0: Sollwert für Warmwasser | `EAPDEV.sollwert_speicherbetrieb` | s16 | 03 | r | r |
| 25177 | EAP 1: Sollwert für Warmwasser | `EAPDEV.sollwert_speicherbetrieb` | s16 | 03 | r | r |
| 25184 | EAP 0: Sollwert für Kühlen | `EAPDEV.sollwert_kuehlbetrieb` | s16 | 03 | r | r |
| 25185 | EAP 1: Sollwert für Kühlen | `EAPDEV.sollwert_kuehlbetrieb` | s16 | 03 | r | r |
| 25192 | EAP 0: Leistungsbegrenzung | `EAPDEV.leistungsbegrenzung` | u16 | 03 | r | r |
| 25193 | EAP 1: Leistungsbegrenzung | `EAPDEV.leistungsbegrenzung` | u16 | 03 | r | r |
| 25200 | EAP 0: Modbus VL-Temp. Soll | `EAPDEV.modbus_vorlauf_soll` | s16 | 03 | r | rw |
| 25201 | EAP 1: Modbus VL-Temp. Soll | `EAPDEV.modbus_vorlauf_soll` | s16 | 03 | r | rw |
| 25208 | EAP 0: Mobus Max. Verdichter Soll | `EAPDEV.modbus_max_verdichterdrehz_soll` | u16 | 03 | r | rw |
| 25209 | EAP 1: Mobus Max. Verdichter Soll | `EAPDEV.modbus_max_verdichterdrehz_soll` | u16 | 03 | r | rw |
| 25216 | EAP 0: Max. Leistung Heizen | `EAPDEV.max_leistung_heizen` | s16 | 03 | r | r |
| 25217 | EAP 1: Max. Leistung Heizen | `EAPDEV.max_leistung_heizen` | s16 | 03 | r | r |
| 25224 | EAP 0: Min. Leistung Heizen | `EAPDEV.min_leistung_heizen` | s16 | 03 | r | r |
| 25225 | EAP 1: Min. Leistung Heizen | `EAPDEV.min_leistung_heizen` | s16 | 03 | r | r |
| 25232 | EAP 0: Max. Leistung Warmwasser | `EAPDEV.max_leistung_warmwasser` | s16 | 03 | r | r |
| 25233 | EAP 1: Max. Leistung Warmwasser | `EAPDEV.max_leistung_warmwasser` | s16 | 03 | r | r |
| 25240 | EAP 0: Min. Leistung Warmwasser | `EAPDEV.min_leistung_warmwasser` | s16 | 03 | r | r |
| 25241 | EAP 1: Min. Leistung Warmwasser | `EAPDEV.min_leistung_warmwasser` | s16 | 03 | r | r |
| 25248 | EAP 0: Max. Leistung Kühlen | `EAPDEV.max_leistung_kuehlen` | s16 | 03 | r | r |
| 25249 | EAP 1: Max. Leistung Kühlen | `EAPDEV.max_leistung_kuehlen` | s16 | 03 | r | r |
| 25256 | EAP 0: Min. Leistung Kühlen | `EAPDEV.min_leistung_kuehlen` | s16 | 03 | r | r |
| 25257 | EAP 1: Min. Leistung Kühlen | `EAPDEV.min_leistung_kuehlen` | s16 | 03 | r | r |
| 25264 | EAP 0: Zeitfenster Beginn | `EAPDEV.fluester1_beginn` | u16 | 03 | r | r |
| 25265 | EAP 1: Zeitfenster Beginn | `EAPDEV.fluester1_beginn` | u16 | 03 | r | r |
| 25272 | EAP 0: Zeitfenster Ende | `EAPDEV.fluester1_ende` | u16 | 03 | r | r |
| 25273 | EAP 1: Zeitfenster Ende | `EAPDEV.fluester1_ende` | u16 | 03 | r | r |
| 25280 | EAP 0: Zeitfenster Beginn | `EAPDEV.fluester2_beginn` | u16 | 03 | r | r |
| 25281 | EAP 1: Zeitfenster Beginn | `EAPDEV.fluester2_beginn` | u16 | 03 | r | r |
| 25288 | EAP 0: Zeitfenster Ende | `EAPDEV.fluester2_ende` | u16 | 03 | r | r |
| 25289 | EAP 1: Zeitfenster Ende | `EAPDEV.fluester2_ende` | u16 | 03 | r | r |
| 25296 | EAP 0: Max. Drehzahl | `EAPDEV.fluester_max_drehzahl` | s16 | 03 | r | r |
| 25297 | EAP 1: Max. Drehzahl | `EAPDEV.fluester_max_drehzahl` | s16 | 03 | r | r |
| 25350 | SG Boilerladung | `EAP.sg_boilerladung_modbus` | s16 | 03 | r | rw |
| 25351 | Brauchw. Solltemp. | `EAP.brauchwasser_solltemp` | s16 | 03 | rw | rw |
| 25377 | Max.Leistung WW | `EAP.sg_max_leistung_ww_modbus` | s16 | 03 | r | rw |
