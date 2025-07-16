# KWB Heating Integration - Entwicklungsrichtlinien

<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

## Projekt-Übersicht

Dies ist eine Home Assistant Custom Component für KWB Heizungsanlagen mit Modbus TCP/RTU Unterstützung.

## Architektur-Prinzipien

- **Datengetrieben**: Vollständige Konfiguration über JSON-Struktur (`kwb_config.json`)
- **Modular**: Klare Trennung zwischen Modbus-Kommunikation, Datenverarbeitung und HA Integration
- **Config Flow**: Vollständige UI-basierte Konfiguration über Home Assistant
- **Access Level System**: UserLevel vs. ExpertLevel mit entsprechender Entitäts-Erstellung
- **Robust**: Graceful Degradation bei Teilausfällen

## Code-Standards

- **Python Standards**: PEP 8, vollständige Type Hints
- **Home Assistant Guidelines**: Einhaltung aller HA Development Standards
- **Async/Await**: Konsequente Verwendung asynchroner Programmierung
- **Error Handling**: Umfassende Exception-Behandlung

## Wichtige Konzepte

### Access Level System
```python
# Zwei Zugriffsstufen in Config Flow konfigurierbar:
ACCESS_LEVELS = {
    "UserLevel": "Standardfunktionen für Endbenutzer",
    "ExpertLevel": "Vollzugriff für Experten/Service"
}

# Register-basierte Entitäts-Erstellung:
# access="R" → Sensor-Entitäten (Read-Only)
# access="RW" + passender access_level → Number/Select-Entitäten (Read-Write)
```

### Register-Datenmodell
```json
{
  "starting_address": 0,
  "name": "Beschreibender Name",
  "data_type": "04",           // Modbus Function Code
  "access": "R",               // R=ReadOnly, RW=ReadWrite
  "access_level": "UserLevel", // UserLevel oder ExpertLevel
  "type": "s16",
  "unit": "°C",
  "value_table": "table_name"
}
```

### Modbus-Kommunikation
- **Adaptive Function Codes**: Automatische Erkennung Input/Holding Register
- **Intelligent Batching**: Optimierung der Register-Abfragen
- **Connection Management**: Automatische Wiederverbindung

## Verzeichnisstruktur

```
/custom_components/kwb_heating/  # Haupt-Integration
├── __init__.py                  # Setup und Konfiguration
├── config_flow.py               # UI-basierte Konfiguration
├── const.py                     # Konstanten und Mappings
├── coordinator.py               # DataUpdateCoordinator
├── modbus_client.py             # Modbus-Kommunikation
├── register_manager.py          # Register-Definitionen
├── entity_factory.py            # Dynamische Entitäts-Erstellung
├── sensor.py                    # Sensor-Entitäten
├── number.py                    # Number-Entitäten (RW)
├── select.py                    # Select-Entitäten (RW)
├── switch.py                    # Switch-Entitäten (RW)
├── kwb_config.json              # Register-Definitionen
└── translations/                # UI-Übersetzungen

/tests/                          # Alle Tests hier
├── unit/                        # Unit Tests
├── integration/                 # Integration Tests
├── fixtures/                    # Mock-Objekte
└── data/                        # Test-Daten

/assets/                         # Icons, Logos, Dokumentation
/docs/                          # Benutzer-Dokumentation
```

## Entwicklungs-Phasen

### Phase 1: Kern-Funktionalität
- Basis-Modbus-Kommunikation
- Config Flow mit Access Level Auswahl
- JSON-Konfigurations-Parser
- Einfache Sensor-Entitäten (Read-Only)

### Phase 2: Erweiterte Funktionen
- Alle HA Entitäts-Typen (Number, Select, Switch)
- Read/Write Funktionalität basierend auf Access Level
- Equipment-basierte Konfiguration
- Umfassendes Logging und Debugging

### Phase 3: Premium-Features
- Alarm-System Integration
- Multi-Device Support
- Expert-Level Funktionen
- Performance-Optimierungen

## Test-Anforderungen

- **Unit Tests**: Alle Kernkomponenten
- **Config Flow Tests**: Vollständige UI-Flow-Tests
- **Access Level Tests**: Korrekte Entitäts-Erstellung
- **Modbus Tests**: Mock-Device Kommunikation

## Wichtige Design-Patterns

- **DataUpdateCoordinator**: Für Daten-Updates
- **Config Flow**: Für UI-Konfiguration
- **Factory Pattern**: Für dynamische Entitäts-Erstellung
- **Dependency Injection**: Für lose Kopplung

## KWB-spezifische Besonderheiten

- **Input Register bevorzugt**: KWB-Geräte verwenden hauptsächlich Function Code 04
- **Equipment-Konfiguration**: Heizkreise, Pufferspeicher, Solar, etc.
- **Alarm-Integration**: 1000+ Alarmcodes verfügbar
- **Wertetabellen**: Enum-Umwandlung für Status-Werte

## Qualitäts-Ziele

- **99%+ Uptime** bei stabiler Netzverbindung
- **Sub-Sekunden Response** für UI-Interaktionen
- **Minimaler Ressourcenverbrauch**
- **Intuitive Konfiguration** ohne technische Expertise
