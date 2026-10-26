# Clean Your TV — instrukcja użytkownika

No-root i Root to równorzędne opcje dla różnych konfiguracji telewizora. Wybierz No-root dla LG Developer Mode lub Root, jeśli masz już dostęp root przez SSH. Zgodność i zakres wykonanych testów są określane osobno dla każdej wersji.

## Wymagania

Ta instrukcja opisuje **[v1.2.0 stable](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/tag/v1.2.0)**. Odnośniki `releases/latest/download` pobierają opublikowane wydanie stabilne. Zobacz [instalację](../INSTALL.md) i [opis wydania](../RELEASE-1.2.0.md).

Wersje wydania: cytv **0.3.1**, Home **1.4.1**, Home Helper **0.6.19**, Root **0.3.0**, Home Updater i Root Updater **0.2.1**, Android **0.2.1-preview** (kod **10**), nadzorca System Updater **1.0.0**, protokół **1**.

Włącz telewizor i połącz go z tą samą zaufaną siecią lokalną co komputer. Później komputer może być wyłączony. Zgodność zależy od modelu, oprogramowania i pilota; Root ma nieukończone testy sprzętowe.

- **No-root:** włącz LG Developer Mode i Key Server. Wpisz hasło wyświetlane na telewizorze i zaakceptuj na nim osobne żądanie parowania. Developer Mode musi pozostać aktywny: wygaśnięcie sesji może usunąć tak zainstalowane aplikacje. Sprawdzaj oficjalny licznik także przy włączonym odnawianiu Beta. Monitorowanie Helper wymaga sieci lokalnej.

Zaktualizowany Helper No-root wymaga Node.js 0.12.2 lub nowszego na telewizorze. Instalator sprawdza ten wymóg przed instalacją. Wcześniej opublikowane pakiety nie uzyskują tej zgodności automatycznie; dostęp do urządzeń wejściowych, wybudzanie i zimny start wymagają testów na każdym modelu.

- **Root:** potrzebny jest istniejący dostęp root przez SSH. Instalator nie uzyskuje uprawnień root. Nie włączaj Developer Mode na telewizorze z istniejącym rootem. Zachowaj dostęp root i usługi odzyskiwania.

## Opcjonalny Python dla Root

Root wymaga na TV Pythona 3.9+. Instalator sprawdza rzeczywiste moduły i operacje, w tym `json`, `fcntl`, blokady, pliki i podprocesy; sam numer wersji nie wystarcza. Jeśli obecny interpreter spełnia wymagania, dodatkowy Python nie jest pobierany. W przeciwnym razie podczas konfiguracji komputer lub Android może pobrać przypięty CPython **3.13.17 dla ARMv7 soft-float**, sprawdzić URL, rozmiar i SHA-256, a następnie przesłać go istniejącym zaufanym połączeniem SSH. Zwykłe pakiety instalatora nie zawierają tego archiwum. TV nie potrzebuje Internetu na tym etapie.

Dodatkowe pobranie to około **26,3 MB**, znormalizowana transmisja SSH **51,5 MB**, zainstalowane pliki **119,3 MB**; przygotowanie wymaga **320 MiB** wolnego miejsca na TV. Zgodność programu ładującego i bibliotek jest sprawdzana przed aktywacją. Prywatne wersje znajdują się w `/var/lib/clean-your-tv-python/`, bez zmiany systemowego Pythona, libc lub globalnego PATH. Nadal potrzebne są root, odpowiednie usługi webOS i Node.js **8+** dla Root/System Updater; No-root Helper wymaga Node.js **0.12.2+**.

Na komputerze z Internetem przygotuj zweryfikowaną pamięć podręczną bez wyszukiwania TV ani łączenia się z nim:

```sh
./cytv --prepare-python-runtime --data-dir /sciezka/prywatna-pamiec
```

Podczas instalacji użyj tego samego `--data-dir`. Do przenoszenia przygotuj osobny prywatny katalog, bez zwykłych kluczy SSH i profili. Polecenia `status`, `doctor`, `restore` i `uninstall` nie pobierają Pythona automatycznie. Zachowaj wersje używane przez Root, updatery i odzyskiwanie, także po usunięciu aplikacji. Więcej: [opcjonalny runtime](../OPTIONAL-PYTHON.md).

## Instalacja i język

- **Windows x64:** pobierz `cytv-windows-x64-desktop.zip`, wybierz **Wyodrębnij wszystkie** w Eksploratorze i otwórz `cytv-desktop/cytv-desktop.exe`. Zachowaj obok folder `_internal`. Podpis wydawcy Windows nie jest skonfigurowany. Osobna konsola to `cytv-windows-x64.exe`; zmień nazwę na `cytv.exe` i użyj `.\cytv.exe` w PowerShell dla poniższych poleceń.
- **macOS 13+:** rozpakuj `cytv-macos-arm64.zip` dla Apple Silicon lub `cytv-macos-x64.zip` dla Intela. Przenieś `cytv.app` do Aplikacji i otwórz; zezwól na dostęp do sieci lokalnej. Jeśli zaufany plik zostanie zablokowany, użyj Prywatność i ochrona → Otwórz mimo to; nie wyłączaj Gatekeepera. Zgodność ze starszymi systemami nie jest w pełni potwierdzona.
- **Linux x64:** na Ubuntu 22.04+, Debianie 12+ lub Mint 21+ zainstaluj `cytv-linux-x64.deb` przez graficzny menedżer pakietów i otwórz Clean Your TV z menu. Pobranie bibliotek może wymagać Internetu. Nie ma pakietu Linux ARM. Samodzielny plik `cytv-linux-x64` to CLI; aplikacja graficzna jest w pakiecie `.deb`.

[Instalator Android](../../android/README.md) obsługuje wszystkie dziesięć języków interfejsu. W prawym górnym rogu widać bieżący język; dotknij go, aby wybrać inny. Wybór zostaje zapisany w telefonie.

W Androidzie wybrane działanie serwisowe pozostaje widoczne podczas łączenia i pokazuje własny postęp. Interfejs używa czcionki systemowej telefonu oraz większych etykiet i tekstów pomocy.

Kreator początkowo używa języka systemu i zapamiętuje wybrany język. Na telewizorze otwórz **Ustawienia → Język** i wybierz język lub automatyczny wybór według systemu. Preferencje instalatora i telewizora są niezależne. Kody zawiera [spis języków](../LANGUAGES.md).

Dla osobno pobranej CLI na macOS/Linux, w rozpakowanym katalogu:

```sh
chmod +x cytv
./cytv --language pl install
```

Wybierz telewizor lub podaj IP, wybierz edycję i sprawdź podsumowanie. Nową tożsamość SSH zatwierdzaj tylko dla własnego telewizora w zaufanej sieci; zmieniony zapisany klucz blokuje dostęp. Root przygotowuje odzyskiwanie i od razu aktywuje Home, bez okresu próbnego ani potwierdzenia zachowania ustawień. Sprawdź strzałki, OK, Home, Wstecz/Anuluj, głośność, czuwanie i uruchomienie po całkowitym odłączeniu zasilania.

Jeśli usuwanie Root zostanie przerwane, ponownie wybierz Usuń w aplikacji. Sprawdzi dziennik TV i stan pakietów przed kontynuowaniem; nie ponowi zakończonego usuwania. Jeśli operacja trwa, odczekaj minutę. Jeśli wyniku nie można potwierdzić, uruchom TV ponownie i sprawdź stan; zachowaj raport dla pomocy technicznej.

## Obsługa i odzyskiwanie

Strzałki wybierają, OK otwiera; przytrzymaj OK, aby zmienić kolejność. Krótkie Wstecz zachowuje nawigację aplikacji i jej potwierdzenie wyjścia. Home otwiera ekran Clean Your TV, gdy sterowanie jest aktywne. W nowych kompilacjach przytrzymaj Wstecz przez 1,2 sekundy, aby jednorazowo otworzyć LG Home. Przełącznik sterowania Home i ustawienia pozostają bez zmian.

**Nowe kompilacje: naciśnij Home trzy razy w ciągu dwóch sekund**, puszczając przycisk po każdym naciśnięciu. Przywraca to LG Home i zatrzymuje sterowanie bez usuwania preferencji. W No-root Helper do wersji 0.6.13 włącznie zamiast tego przytrzymaj Home około dwóch sekund. Przytrzymanie Home nie jest gestem awaryjnym Root.

No-root: otwórz **Home Helper** z listy aplikacji LG, aby wznowić; samo Home nie znosi blokady. Root: włącz **Zmień Home** w ustawieniach Home, aby wznowić. **Otwórz LG Home** otwiera LG Home jednorazowo bez zmiany celu przycisku Home. Aby przywrócić LG Home jako stały cel, wyłącz **Zmień Home** lub uruchom `cytv restore`. Nie uruchamiaj obu kontrolerów jednocześnie. Przy powtarzającym się błędzie pozostań przy LG Home.

```sh
./cytv --language pl status
./cytv --language pl doctor --report
./cytv --language pl restore
./cytv --language pl uninstall
```

Po przerwaniu operacji najpierw uruchom `status` i zachowaj dzienniki. `restore` przywraca LG Home bez usuwania aplikacji; `uninstall` przywraca je przed usunięciem. Dane odzyskiwania Root pozostają celowo: nie kasuj ich, by wymusić ponowną instalację. Sprawdź raporty przed udostępnieniem; nie publikuj kluczy ani katalogów profili.

## Aktualizacja i usuwanie

Po połączeniu cytv pokazuje wersję zainstalowaną → dołączoną i rozróżnia pierwszą instalację, ponowną instalację i cofnięcie wersji. Sprawdź podsumowanie przed potwierdzeniem; `--yes` nie omija kontroli zgodności. Zachowaj działające pakiety i prywatne kopie ustawień. Przed wymianą pakietów z komputera zatrzymaj No-root Helper; nie odinstalowuj wcześniej aplikacji. Nie zastępuj działającego Root pojedynczym IPK: użyj odpowiedniej procedury cytv. Usunięcie aplikacji komputerowej nie usuwa aplikacji z TV.

Kandydat dodaje **Aktualizuj wszystko** w Ustawienia → Aktualizacje oprogramowania. Niezależny System Updater weryfikuje podpisany zestaw dla danej edycji: Home, Helper i Home Updater dla No-root na TV z rootem; Root Home, Root Updater oraz runtime sterowania i odzyskiwania dla Root. Aktualizacja na TV wymaga **roota, Homebrew Channel**, odpowiedniego Pythona, Node.js 8+ i działających usług webOS. Na TV bez roota aktualizuj z komputera.

Przy pierwszej instalacji użyj kompletnego instalatora kandydata, który przygotuje Home i Updater odzyskiwania danej edycji. Ta wersja przejściowa nie jest oferowana w stabilnym kanale aktualizacji.

Jeśli Root jest już zainstalowany i zachowany jest Root Updater, zwykła ponowna instalacja może zostać celowo zablokowana. Najpierw uruchom `status` i diagnostykę, następnie sprawdź transakcję oraz stan odzyskiwania w dotychczasowym Updaterze. Aktywne lub niepewne operacje rozwiąż przez odpowiadający im wcześniejszy mechanizm odzyskiwania; przejście na nową infrastrukturę wymaga oceny rzeczywistego stanu TV. Nie usuwaj dziennika ani nie obchodź blokady przez `--yes`, pojedynczy IPK lub stare OTA. OTA samej aplikacji nie instaluje nowej infrastruktury. Zobacz [kontrolę istniejącego TV](../UPDATES.md#one-time-computer-preparation).

Dopiero po potwierdzeniu zgodnej konfiguracji z Home `systemUpdateProtocol = 1` i właściwym Updaterem odzyskiwania włącz nadzorcę z komputera. W instalatorze wybierz włączenie aktualizacji wszystkich komponentów TV; dla Root, z zapisanym połączeniem root SSH:

```sh
./cytv --language pl enable-system-updates --edition root --host TV_ADDRESS
```

Dla No-root na TV z rootem najpierw zainstaluj Home/Helper/Home Updater z komputera, następnie skorzystaj z procedury z aliasem root SSH w [instrukcji aktualizacji](../UPDATES.md#one-time-computer-preparation). Nadzorca zapisuje zweryfikowaną bazę odzyskiwania faktycznie zainstalowanych komponentów. Starsze OTA aktualizujące tylko aplikację nie instalują nowego Pythona, nadzorcy ani infrastruktury updaterów. Po przygotowaniu używaj wspólnego mechanizmu; kolidujące starsze instalatory są blokowane.

Instalacja wymaga potwierdzenia, a sprawdzenie uruchomienia jest automatyczne. Profil i ustawienia są zachowywane; jawne lub awaryjne wyłączenie sterowania Home nie jest cofane. Góra/Dół przewija opis zmian, Lewo/Prawo wybiera stałe przyciski, a odświeżanie nie przenosi zaznaczenia. Pomarańczowa kropka oznacza nową wersję, także gdy wymaga komputera. Otwórz Odzyskiwanie w Updaterze, aby zobaczyć stan i dostępną poprzednią wersję. Cofnięcie aktualizacji systemu przywraca cały poprzedni zestaw i zapisany profil; późniejsze zmiany ustawień zostaną utracone. Automatyczna kontrola uruchomienia nie usuwa możliwości cofnięcia, która pozostaje do następnej transakcji.

Po przerwaniu uruchom `status` i zachowaj dziennik oraz dane odzyskiwania. Niejednoznaczny wynik blokuje ponowną instalację i cofanie; odczyt wersji nie dowodzi zakończenia instalatora. Nie usuwaj dziennika, blokad ani wersji Pythona, aby wymusić próbę. `doctor --report` wskazuje poszczególne niespełnione wymagania Root i zapisuje numeryczne kody SSH bez poświadczeń i surowego wyjścia. Sprawdź raport przed udostępnieniem.

## Testy sprzętowe i ograniczenia

Root 0.2.0, Root Updater 0.2.0 i nadzorca 1.0.0 sprawdzono na OLED55C3RLA / firmware 43.21.71 / webOS 11.2.0 (`d344d92`, identyczna zawartość produktu jak `4b66951`). Przeszły sterowanie, potrójny Home i wznowienie, czuwanie/wybudzenie z Emby otwartym przez 70 sekund, menu wersji i czytelny komunikat o niedostępnej liście aktualizacji. Prawdziwy zimny start, Helper 0.6.19 na TV, UK6540PTD i pełna podpisana aktualizacja/wycofanie systemu nie zostały przetestowane. Wydanie stabilne przyjęto z tym ograniczonym zakresem dowodów; inne modele nie są zweryfikowane.

No-root sprawdza ABI powłoki i dopuszcza 64-bitowe jądro tylko ze zweryfikowanym środowiskiem ARM32. Nazwa modelu ani `armv7l` nie gwarantują zgodności. Zakres wcześniejszych testów pozostaje ograniczony do sprawdzonego sprzętu i pakietów.

No-root: Ustawienia Home → Tryb dewelopera zawiera odnawianie Beta, kontrolę sesji i diagnostykę. Zawsze sprawdzaj oficjalny licznik. Home Helper pokazuje stan i prosi o potwierdzenie wznowienia po zatrzymaniu.

Dokumentacja techniczna: [aplikacja komputerowa](../DESKTOP_INSTALL.md), [CLI](../CLI.md), [instalacja ręczna](../MANUAL_INSTALL.md), [odzyskiwanie](../RECOVERY.md), [edycje](../EDITIONS.md), [aktualizacje](../UPDATES.md).

Jeśli Root pokazuje `Denied methods call status` zaraz po konfiguracji nadzorcy, zamknij i ponownie otwórz Home Root jeden raz, a następnie sprawdź aktualizacje. Jeśli błąd pozostaje, zachowaj diagnostykę i dane odzyskiwania.

1.2.0 (#51): po odrzuceniu pakietu przez TV raport JSON zachowuje tylko kategorię operacji, ograniczone liczbowe kody błędu/statusu, dozwolony stan pakietu i wynik logiczny. Pomija surowy tekst błędu TV, ścieżki i identyfikatory aplikacji. Sprawdź raport przed udostępnieniem; nie ma automatycznej ponownej próby, a naprawa instalacji na UN70006LA nie jest jeszcze potwierdzona.

1.2.0 (#59): jeśli nie można sprawdzić stanu Helper, **Uruchom Helper** pozostaje dostępne z potwierdzeniem. Otwarcie kafelka nie uruchamia ponownie Helper ani nie znosi zatrzymania awaryjnego. Ustawienia Home wymagają odpowiedzi sterowania.

1.2.0 (#55): Root sprawdza dane migracji przed instalacją. Instalację przerwaną przed konfiguracją usług można usunąć bez nigdy nieutworzonej migawki LS2; zachowuje zweryfikowany zapis dla zwykłej archiwizacji i ponownej instalacji cytv. Brak migawki na późniejszym etapie lub sprzeczne dowody nadal blokują czyszczenie. Wymagany jest nowy sterownik; problem startu usługi odzyskiwania na OLED Flex pozostaje nierozwiązany.

## Blokada oprogramowania LG w 1.2.0

Tylko Root: Ustawienia Home → Aktualizacje oprogramowania LG zmienia istniejące ustawienie Homebrew Channel. Dotyczy też aktualizacji zabezpieczeń TV; aktualizacje Clean Your TV są oddzielne. Obie zmiany wymagają prawdziwego ponownego uruchomienia TV; czuwanie nie wystarczy. Przełącznik pokazuje zapisane ustawienie, nie potwierdza działania blokady. Niektóre TV sprawdzają wcześniej; powiadomienia mogą pozostać i może być potrzebna blokada na routerze. Homebrew zachowuje ustawienie po usunięciu lub cofnięciu wersji CYTV. Przy niedostępności lub braku potwierdzenia sprawdź Homebrew i odśwież stan. Zakres testów TV opisuje zapis akceptacji.

[LG firmware blocking](../LG-FIRMWARE-UPDATES.md) · [1.2.0](../RELEASE-1.2.0-ACCEPTANCE.md)
