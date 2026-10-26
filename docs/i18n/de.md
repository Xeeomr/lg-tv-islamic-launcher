# Clean Your TV — Benutzeranleitung

No-root und Root sind gleichwertige Optionen für unterschiedliche TV-Konfigurationen. Wählen Sie No-root für LG Developer Mode oder Root für vorhandenen Root-Zugriff per SSH. Kompatibilität und Testumfang hängen von der jeweiligen Edition ab.

## Voraussetzungen

Diese Anleitung beschreibt **[v1.2.0 stable](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/tag/v1.2.0)**. Die Links `releases/latest/download` liefern die veröffentlichte stabile Version. Siehe [Installation](../INSTALL.md) und [Versionshinweise](../RELEASE-1.2.0.md).

Die Version enthält cytv **0.3.1**, Home **1.4.1**, Home Helper **0.6.19**, Root Edition **0.3.0**, Home Updater und Root Updater **0.2.1**, Android **0.2.1-preview** (Versionscode **10**) und System-Updater-Supervisor **1.0.0** (Protokoll **1**). Dies sind die Komponenten von v1.2.0.

Root 0.2.0, Root Updater 0.2.0 und Supervisor 1.0.0 wurden auf OLED55C3RLA / Firmware 43.21.71 / webOS 11.2.0 geprüft (`d344d92`, Produktinhalt identisch mit `4b66951`). Fernbedienung, dreifaches Home mit Wiederaufnahme, Standby/Aufwachen mit 70 Sekunden geöffnetem Emby, Versionsmenüs und verständliche Meldung bei nicht verfügbarem Feed bestanden. Echter Kaltstart, Helper 0.6.19 am TV, UK6540PTD und vollständiges signiertes Systemupdate/Rollback sind ungetestet. Die stabile Veröffentlichung akzeptiert diese begrenzten Nachweise; andere Modelle sind nicht validiert.

Fernseher einschalten und mit demselben vertrauenswürdigen Heimnetz wie den Computer verbinden. Danach muss der Computer nicht eingeschaltet bleiben. Die Kompatibilität hängt von Modell, Firmware und Fernbedienung ab; für Root stehen noch Gerätetests aus.

- **No-root:** LG Developer Mode und Key Server einschalten. Die am Fernseher angezeigte Passphrase eingeben und die separate Kopplungsanfrage am Fernseher bestätigen. Developer Mode muss aktiv bleiben: Bei Ablauf können nachinstallierte Apps entfernt werden. Den offiziellen Timer auch mit aktivierter Beta-Verlängerung kontrollieren. Die Überwachung durch Helper benötigt das lokale Netzwerk.

Der aktualisierte No-root Helper benötigt Node.js 0.12.2 oder neuer auf dem TV. Der Installer prüft die TV-Laufzeit vor der Installation. Ältere veröffentlichte Pakete erhalten diese Kompatibilität nicht automatisch; Eingabegeräte, Standby und Kaltstart müssen je Modell getestet werden.

- **Root:** Bereits vorhandener Root-Zugang über SSH ist nötig. Der Installer richtet keinen Root-Zugang ein. Developer Mode nicht auf einem bereits gerooteten Fernseher aktivieren. Root-Zugang und Wiederherstellungsdienste verfügbar halten.

## Optionales Python für Root in v1.1.0

Root benötigt auf dem TV ein funktionsfähiges Python **3.9+**. Der Installer prüft benötigte Module (darunter `json` und `fcntl`), Sperren, Dateisystemzugriffe und Unterprozesse; die Versionsnummer allein genügt nicht. Ein geeignetes vorhandenes Python vermeidet den Zusatzdownload. Andernfalls lädt die Einrichtung auf dem Computer oder Android-Gerät geprüftes **CPython 3.13.17 für ARMv7 Soft-Float** herunter und überträgt es über vertrauenswürdiges SSH. Der TV benötigt dafür kein Internet. Das optionale Archiv ist nicht im normalen Installer enthalten: etwa **26.3 MB** Download, **51.5 MB** normalisierte SSH-Übertragung und **119.3 MB** installierte Dateien; für die anfängliche Bereitstellung sind **320 MiB** freier Speicher nötig. Die private Laufzeit ersetzt weder System-Python noch libc oder den globalen PATH.

Kompatible Loader und Bibliotheken bleiben erforderlich. Root-SSH, Node.js **8+**, `luna-send` und die webOS-Verzeichnisse für Apps und Dienste werden weiterhin benötigt; No-root Helper benötigt Node.js **0.12.2+**. LG UK6540PTD / Firmware 05.50.70 / ARM32 aus Issue #37 (Python 2.7.12 ohne Python 3) hat mit dieser Laufzeit **keine Hardware-Abnahme** bestanden. QEMU-Tests belegen weder TV-Kompatibilität noch Kaltstart, Fernbedienung oder Rollback. Frühere Gerätetests gelten nur für die jeweils dokumentierten Modelle, Firmware und Artefakte.

Verifizierten Cache auf einem Computer mit Internet **ohne TV-Verbindung** vorbereiten:

```sh
./cytv --language de --prepare-python-runtime
```

Bei der Einrichtung dasselbe private Datenverzeichnis verwenden. Für einen übertragbaren Cache mit `--data-dir /path/to/private-data` ein neues separates Verzeichnis vorbereiten und die Option bei beiden Befehlen angeben. Normale SSH-Schlüssel und Profile nicht in einen geteilten Cache kopieren. Status, Diagnose, Wiederherstellung und Entfernung laden Python nicht automatisch herunter. Laufzeitversionen behalten, auf die installierte Updater oder Wiederherstellungsdaten verweisen. Siehe [Python-Details](../OPTIONAL-PYTHON.md).

## Installation und Sprache

- **Windows x64:** `cytv-windows-x64-desktop.zip` herunterladen, im Explorer **Alle extrahieren** wählen und `cytv-desktop/cytv-desktop.exe` öffnen. Den Ordner `_internal` daneben behalten. Eine Windows-Herausgebersignatur ist nicht eingerichtet. Die separate Konsole heißt `cytv-windows-x64.exe`; für die folgenden PowerShell-Befehle in `cytv.exe` umbenennen und `.\cytv.exe` verwenden.
- **macOS 13+:** `cytv-macos-arm64.zip` für Apple Silicon oder `cytv-macos-x64.zip` für Intel entpacken. `cytv.app` nach Programme verschieben und öffnen; Zugriff auf das lokale Netzwerk erlauben. Bei einer Sperre für einen vertrauenswürdigen Projekt-Download Datenschutz & Sicherheit → Dennoch öffnen verwenden. Gatekeeper nicht abschalten. Ältere Systeme sind nicht abschließend geprüft.
- **Linux x64:** Unter Ubuntu 22.04+, Debian 12+ oder Mint 21+ `cytv-linux-x64.deb` mit der grafischen Paketverwaltung installieren, dann Clean Your TV im Anwendungsmenü öffnen. Für Bibliotheken kann Internet nötig sein. Linux ARM wird nicht angeboten. Die eigenständige Datei `cytv-linux-x64` ist die CLI; für die grafische App das `.deb` verwenden.

[Android-Installer](../../android/README.md): Alle zehn Oberflächensprachen sind verfügbar. Oben rechts steht die aktuelle Sprache; antippen, um eine andere zu wählen. Die Auswahl wird auf dem Smartphone gespeichert.

Unter Android bleibt die gewählte Wartungsaktion beim Verbinden sichtbar und zeigt ihren eigenen Fortschritt. Die Oberfläche nutzt die Systemschrift des Smartphones mit größeren Beschriftungen und Hilfetexten.

Der Desktop-Assistent verwendet zunächst die Systemsprache und speichert eine ausdrückliche Auswahl. Am Fernseher unter **Einstellungen → Sprache** die gewünschte Sprache oder die automatische Systemauswahl wählen. Die Spracheinstellungen von Installer und Fernseher sind unabhängig. Alle Sprachcodes stehen im [Sprachverzeichnis](../LANGUAGES.md).

Für die separat heruntergeladene CLI unter macOS/Linux im entpackten Verzeichnis:

```sh
chmod +x cytv
./cytv --language de install
```

Fernseher oder IP-Adresse und Edition auswählen, dann die Zusammenfassung prüfen. Einer neuen SSH-Identität nur für den eigenen Fernseher im vertrauenswürdigen Netz zustimmen; ein geänderter gespeicherter Schlüssel blockiert den Zugang. Root aktiviert Home nach Einrichtung der Wiederherstellung sofort, ohne Testphase oder Behalten-Schritt. Pfeile, OK, Home, Zurück/Abbrechen, Lautstärke, Bereitschaft und Kaltstart am eigenen Fernseher testen.

Bei unterbrochener Root-Entfernung erneut Entfernen in der App wählen. Sie prüft das TV-Journal und den Paketzustand vor dem Fortsetzen; abgeschlossene Entfernung wird nicht erneut gesendet. Läuft der Vorgang noch, eine Minute warten. Bei unklarem Ergebnis den TV neu starten und erneut prüfen; Diagnosebericht für den Support behalten.

## Bedienung und Wiederherstellung

Pfeile wählen eine Kachel, OK öffnet sie; OK gedrückt halten zum Verschieben. Kurzes Zurück behält Navigation und Beendigungsdialog der App bei. Kurzes Home öffnet bei aktiver Home-Steuerung den Launcher. In neuen Builds öffnet 1,2 Sekunden langes Drücken von Zurück LG Home einmalig. Der Home-Schalter und Ihre Einstellungen bleiben unverändert.

**Neue Builds: Home innerhalb von zwei Sekunden dreimal kurz drücken**, dazwischen loslassen. Dies stellt LG Home wieder her und stoppt die Steuerung, ohne Einstellungen zurückzusetzen. Beim älteren No-root Helper bis einschließlich 0.6.13 stattdessen Home etwa zwei Sekunden halten. Langes Home ist nicht die Root-Notfallgeste.

No-root: **Home Helper** in der LG-App-Liste öffnen, um fortzufahren; Home allein hebt den Stopp nicht auf. Root: **Home ändern** in den Home-Einstellungen einschalten, um fortzufahren. **LG Home öffnen** öffnet LG Home einmalig, ohne das Home-Ziel zu ändern. Für LG Home als dauerhaftes Ziel **Home ändern** ausschalten oder `cytv restore` ausführen. Beide Steuerungen nie gleichzeitig betreiben. Bei wiederholtem Fehler LG Home aktiv lassen.

```sh
./cytv --language de status
./cytv --language de doctor --report
./cytv --language de restore
./cytv --language de uninstall
```

Nach einer Unterbrechung zuerst `status` ausführen und Protokolle behalten. `restore` stellt LG Home ohne App-Entfernung wieder her; `uninstall` stellt es vor der Entfernung wieder her. Root-Wiederherstellungsdaten bleiben absichtlich erhalten; nicht zum Erzwingen einer Neuinstallation löschen. Diagnoseberichte vor Weitergabe prüfen; Schlüssel und Profilordner nicht veröffentlichen.

## Aktualisierung und Entfernung

Funktionierende Pakete und private Einstellungssicherungen behalten. Bei No-root-Paketersatz vom Computer zuerst Helper stoppen und ohne vorherige Deinstallation aktualisieren, da diese Einstellungen löschen kann. Das Entfernen der Desktop-App entfernt keine TV-Apps. Keine einzelne IPK über eine aktive Root-Laufzeit installieren; den ausdrücklichen Wiederherstellungs- oder Neuinstallationsablauf von cytv verwenden.

In v1.1.0 verwendet **Alles aktualisieren** unter Home-Einstellungen → Softwareupdates einen signierten Veröffentlichungssatz: Home, Helper und Home Updater für No-root auf einem gerooteten TV; Root Home, Root Updater sowie die Home-Steuerungs- und Wiederherstellungslaufzeit für Root. Benötigt werden Root, Homebrew Channel, funktionierende webOS-Installationsdienste, Python 3.9+ und Node.js 8+. Fernseher ohne Root werden weiterhin vom Computer aktualisiert.

Bei einer neuen Einrichtung mit dem vollständigen Installer der stabilen Version die passende Home-Übergangsversion und den Wiederherstellungs-Updater der Edition installieren. **Eine bestehende Root-Installation mit erhaltenem Root Updater kann eine allgemeine Neuinstallation absichtlich blockieren.** Zuerst `status`, Wiederherstellung und die vorhandene Transaktion mit dem passenden bisherigen Wiederherstellungsablauf prüfen; siehe [Prüfung eines bereits eingerichteten TVs](../UPDATES.md#one-time-computer-preparation). Keine Journale löschen und diese Prüfung nicht umgehen. Ein älteres OTA-Update nur für Home installiert die neue Infrastruktur nicht.

Erst wenn die installierten Komponenten und der Wiederherstellungszustand bereit sind, im Desktop-Installer **Updates für alle TV-Komponenten** aktivieren. Für eine gespeicherte Root-SSH-Verbindung und die Root-Edition:

```sh
./cytv --language de enable-system-updates --edition root --host TV_ADDRESS
```

Diese separate Aktion richtet den festen Supervisor ein und sichert den installierten Komponentensatz als Rollback-Basis. Sie setzt `systemUpdateProtocol = 1` in den installierten Home-Metadaten voraus, installiert Home nicht neu und ändert die Home-Zuordnung nicht. Die normale No-root-Edition auf einem gerooteten TV benötigt Root-SSH und passende, vom Computer installierte Komponenten; siehe [Ersteinrichtung](../UPDATES.md#one-time-computer-preparation). Ein älteres OTA-Update nur für Home richtet neue Supervisor-, Python- oder Updater-Infrastruktur **nicht** ein. Nach Einrichtung des Supervisors werden kollidierende ältere Installer gesperrt; Pakete nicht an ihm vorbei ersetzen.

Systemupdates prüfen und speichern den neuen und vorherigen Satz, erhalten Einstellungen und Profile und laufen nach dem Schließen von Home oder Updater weiter. Die Wiederherstellung setzt den gesamten vorherigen Komponentensatz samt Profil zurück. Helper 0.6.19 am TV, echter Kaltstart und vollständiges signiertes Upgrade/Rollback bleiben ungetestet. Siehe [Updates und Wiederherstellung](../UPDATES.md).

Technische Anleitungen auf Englisch: [Desktop](../DESKTOP_INSTALL.md), [CLI](../CLI.md), [No-root](../INSTALL.md), [manuelle Installation](../MANUAL_INSTALL.md), [Wiederherstellung](../RECOVERY.md), [Editionen](../EDITIONS.md).

Nach dem Verbinden liest cytv die installierten TV-Versionen und zeigt aktuelle → mitgelieferte Version für Home und Home Helper (No-root) oder Root und Root Updater. Prüfen und bestätigen Sie die Versionen vor der Installation. Erstinstallation, Neuinstallation und ältere Versionen werden gekennzeichnet; `--yes` überspringt die Bestätigung, zeigt aber weiterhin die Versionen.

Software-Updates zeigt Versionsdetails nur für die installierte oder eine neuere Version. Unter Wiederherstellung siehst du die gespeicherte Version für die Rückkehr oder den Grund, warum sie nicht verfügbar ist; Zurück führt zu den Updates.

No-root prüft die ABI der TV-Shell und akzeptiert einen 64-Bit-Kernel mit bestätigtem ARM32-Benutzerraum. Schlägt die Prüfung fehl, hängen Sie den erzeugten Diagnosebericht an; teilen Sie keine Schlüssel oder Passphrasen.

Home-Updates erfordern eine Bestätigung vor der Installation; danach wird der Start automatisch geprüft. Die Statusabfrage im Hintergrund behält die mit der Fernbedienung gewählte Taste bei.

Beide Editionen prüfen den Start automatisch; eine manuelle Funktionsbestätigung ist nicht nötig. Das ältere Home-Rollback stellt nur das vorherige Home-Paket und sein Profil wieder her; System Updater stellt den vollständigen vorherigen Veröffentlichungssatz wieder her. Die Wiederherstellung bleibt nach Bestätigung ohne Zeitlimit bis zum nächsten Update verfügbar. Spätere Einstellungsänderungen können verloren gehen; Rollback verlangt eine Bestätigung. No-root-Updates und Rollback am TV benötigen weiterhin Root und Homebrew Channel. Nach einer Unterbrechung `status` ausführen und die Wiederherstellung prüfen. Ein ungewisses Installationsergebnis sperrt Neuinstallation und Rollback: Protokolle, Journale und Laufzeitversionen behalten, niemals Zustand löschen, um einen neuen Versuch zu erzwingen. Unterbrochene cytv-Vorgänge nur über den geprüften Wiederherstellungsablauf fortsetzen.

Der Update-Bildschirm trennt Versionen, Status und lesbare Neuerungen. Oben/Unten blättert durch die Änderungen, Links/Rechts wählt die festen Aktionen darunter. Nach automatischen Startprüfungen stellt Root die zuvor aktivierte Home-Steuerung wieder her; No-root erhält den Zustand des separaten Helpers. Deaktivierte Einstellungen sowie ausdrückliches oder Notfall-Ausschalten bleiben erhalten.

Beim Öffnen der Home-Einstellungen wird im Hintergrund nach Updates gesucht. Ein orangefarbener Punkt bei Softwareupdates zeigt eine neuere Version an, auch wenn sie die Einrichtung am Computer erfordert. Die Einstellungen bleiben während der Prüfung bedienbar.

No-root: Öffne Home-Einstellungen → Entwicklermodus für automatische Verlängerung, Sitzungsprüfung und Diagnose. Auf der Hauptseite bleiben der Kurzstatus und Verlängerungsfehler sichtbar. Zurück führt zu den Home-Einstellungen. Beide Editionen zeigen Sprache, Softwareupdates und TV-Einstellungen in derselben Zeile; der Pfeil öffnet den jeweiligen Eintrag.

Home Helper zeigt beim Öffnen seinen Zweck und Status. Der Start eines gestoppten Helpers muss bestätigt werden. Home Updater und Root Updater erklären die Wiederherstellung; reguläre Updates befinden sich in den Home-Einstellungen. Die Wiederherstellung wird nur bei einer gespeicherten Version angeboten und erfordert eine Bestätigung vor dem Ersetzen von Home und seinen Einstellungen.

Zeigt Root direkt nach der Supervisor-Einrichtung `Denied methods call status`, Home Root einmal schließen und erneut öffnen, dann Updates prüfen. Bei anhaltendem Fehler Diagnose und Wiederherstellungsdaten aufbewahren.

[1.1.0 hardware acceptance](../RELEASE-1.1.0-ACCEPTANCE.md)

1.2.0 (#51): Nach einer Paket-Ablehnung durch den TV enthält der Diagnosebericht nur die Vorgangskategorie, begrenzte numerische Fehler-/Statuscodes, einen freigegebenen Paketstatus und ein boolesches Ergebnis. Roher TV-Fehlertext, Pfade und App-IDs bleiben ausgeschlossen. Vor dem Teilen prüfen; keine automatische Wiederholung. Der Installationsfehler auf UN70006LA ist noch nicht als behoben bestätigt.

1.2.0 (#59): Wenn der Helper-Status nicht geprüft werden kann, bleibt **Helper starten** mit Bestätigung verfügbar. Das Öffnen der Kachel startet Helper nicht neu und hebt keinen Notstopp auf. Die Home-Tasteneinstellungen benötigen eine antwortende Steuerung.

1.2.0 (#55): Root prüft die Migrationsdaten vor der Installation. Eine vor der Provisionierung unterbrochene Installation kann ohne einen noch nicht erstellten LS2-Snapshot entfernt werden; ein geprüfter Beleg bleibt für die normale cytv-Archivierung und Neuinstallation erhalten. Später fehlende Snapshots oder widersprüchliche Daten stoppen die Bereinigung weiterhin. Dies erfordert den neuen Treiber; der Startfehler des Recovery-Dienstes auf OLED Flex bleibt ungelöst.

## LG-Firmware-Sperre in 1.2.0

Nur Root: Home-Einstellungen → LG-Firmware-Updates ändert die vorhandene Homebrew-Channel-Einstellung. Dies betrifft auch Firmware-Sicherheitsupdates; Clean Your TV wird separat aktualisiert. Beide Richtungen erfordern einen echten TV-Neustart; Standby reicht nicht aus. Der Schalter zeigt die gespeicherte Einstellung, keine geprüfte aktive Sperre. Manche TVs prüfen vor Beginn der Sperre; Hinweise können bleiben und eine Router-Sperre kann nötig sein. Homebrew behält die Einstellung nach Entfernung oder Rollback von CYTV. Bei fehlender Verfügbarkeit oder Bestätigung Homebrew prüfen und Status aktualisieren. Den Umfang der TV-Prüfung beschreibt der Abnahmebericht.

[LG firmware blocking](../LG-FIRMWARE-UPDATES.md) · [1.2.0](../RELEASE-1.2.0-ACCEPTANCE.md)
