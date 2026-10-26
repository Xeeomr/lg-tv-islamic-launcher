# Clean Your TV — guida all’uso

No-root e Root sono opzioni equivalenti per diverse configurazioni della TV. Scegli No-root per LG Developer Mode oppure Root se disponi già di accesso root tramite SSH. Compatibilità e verifiche eseguite sono specifiche di ogni edizione.

## Requisiti

Questa guida descrive **[v1.2.0 stabile](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/tag/v1.2.0)**. I collegamenti `releases/latest/download` distribuiscono la versione stabile pubblicata. Vedi [installazione](../INSTALL.md) e [note di rilascio](../RELEASE-1.2.0.md).

Versioni del rilascio: cytv **0.3.1**, Home **1.4.1**, Home Helper **0.6.19**, Root **0.3.0**, Home Updater e Root Updater **0.2.1**, Android **0.2.1-preview** (codice **10**), supervisore System Updater **1.0.0**, protocollo **1**.

Accendi il televisore e collegalo alla stessa rete locale affidabile del computer. Dopo l’installazione il computer può restare spento. La compatibilità dipende da modello, firmware e telecomando; Root ha ancora verifiche hardware da completare.

- **No-root:** attiva LG Developer Mode e Key Server. Inserisci la frase di accesso mostrata sul televisore e accetta sullo schermo la richiesta separata di abbinamento. Developer Mode deve restare attivo: alla scadenza le app installate in questo modo possono essere rimosse. Controlla il timer ufficiale anche con rinnovo Beta attivo. Il monitoraggio di Helper richiede la rete locale.

Il Helper No-root aggiornato richiede Node.js 0.12.2 o successivo sulla TV. Il programma di installazione verifica questo requisito prima di installare. I pacchetti già pubblicati non acquisiscono automaticamente questa compatibilità; accesso al telecomando, standby e avvio a freddo richiedono prove su ogni modello.

- **Root:** serve un accesso SSH root già disponibile. L’installer non ottiene i privilegi root. Non attivare Developer Mode su una configurazione già dotata di root. Mantieni disponibili accesso root e servizi di ripristino.

## Python opzionale per Root

Root richiede Python 3.9+ sulla TV. L’installer verifica realmente moduli e operazioni necessari, inclusi `json`, `fcntl`, blocchi, file e sottoprocessi: il solo numero di versione non basta. Se l’interprete esistente è adatto, non scarica un altro Python. Altrimenti, durante la configurazione può scaricare sul computer o su Android CPython **3.13.17 per ARMv7 soft-float**, fissato per URL, dimensione e SHA-256, e trasferirlo con la connessione SSH già verificata. I pacchetti ordinari desktop/Android non contengono questo archivio; per questa fase la TV non deve accedere a Internet.

Il download opzionale è circa **26,3 MB**, il trasferimento SSH normalizzato **51,5 MB**, i file installati **119,3 MB**; la preparazione richiede **320 MiB** liberi sulla TV. La compatibilità del loader e delle librerie viene verificata prima dell’attivazione. I file risiedono in slot privati sotto `/var/lib/clean-your-tv-python/`: Python di sistema, libc e PATH globale non vengono modificati. Restano necessari root, servizi webOS compatibili e Node.js **8+** per Root/System Updater; il Helper No-root richiede Node.js **0.12.2+**.

Per preparare una cache verificata su un computer con Internet, senza cercare né contattare una TV:

```sh
./cytv --prepare-python-runtime --data-dir /percorso/cache-privata
```

Riusa la stessa `--data-dir` durante l’installazione. Per trasferire la cache, crea una cartella privata dedicata: non condividere dati contenenti chiavi SSH o profili. `status`, `doctor`, `restore` e `uninstall` non scaricano automaticamente Python. Conserva gli slot ancora usati da Root, dagli updater o dal ripristino, anche dopo la rimozione delle app. Dettagli: [runtime opzionale](../OPTIONAL-PYTHON.md).

## Installazione e lingua

- **Windows x64:** scarica `cytv-windows-x64-desktop.zip`, scegli **Estrai tutto** in Esplora file e apri `cytv-desktop/cytv-desktop.exe`. Mantieni la cartella `_internal` accanto al file. La firma dell’editore Windows non è configurata. La console separata è `cytv-windows-x64.exe`; rinominala in `cytv.exe` e usa `.\cytv.exe` in PowerShell per i comandi seguenti.
- **macOS 13+:** estrai `cytv-macos-arm64.zip` per Apple Silicon oppure `cytv-macos-x64.zip` per Intel, sposta `cytv.app` in Applicazioni e aprila. Consenti l’accesso alla rete locale. Se un download affidabile viene bloccato, usa Privacy e sicurezza → Apri comunque; non disattivare Gatekeeper. La verifica sui sistemi meno recenti non è conclusa.
- **Linux x64:** su Ubuntu 22.04+, Debian 12+ o Mint 21+, installa `cytv-linux-x64.deb` con il gestore grafico dei pacchetti e apri Clean Your TV dal menu. Le librerie possono richiedere Internet. Linux ARM non è incluso. L’eseguibile autonomo `cytv-linux-x64` è la CLI; usa il `.deb` per l’app grafica.

[Installer Android](../../android/README.md): sono disponibili tutte e dieci le lingue. Il pulsante in alto a destra mostra la lingua attuale; toccalo per sceglierne un’altra. La scelta viene salvata sul telefono.

Su Android, l’azione di manutenzione scelta resta visibile durante la connessione e mostra il proprio avanzamento. L’interfaccia usa il carattere di sistema del telefono con etichette e testi di aiuto più grandi.

L’assistente usa inizialmente la lingua del sistema e salva una scelta esplicita. Sul televisore, apri **Impostazioni → Lingua** e scegli una lingua oppure l’opzione automatica del sistema. Le preferenze del televisore e dell’installer sono separate. I codici sono nell’[indice delle lingue](../LANGUAGES.md).

Per la CLI scaricata separatamente su macOS/Linux, dalla cartella estratta:

```sh
chmod +x cytv
./cytv --language it install
```

Scegli il televisore o inserisci l’IP, seleziona l’edizione e controlla il riepilogo. Accetta una nuova identità SSH solo per il tuo televisore su una rete affidabile; una chiave salvata cambiata blocca l’accesso. Root prepara il ripristino e attiva subito Home, senza prova temporanea né passaggio per confermare il mantenimento. Verifica frecce, OK, Home, Indietro/Annulla, volume, standby e avvio a freddo.

Se la rimozione di Root si interrompe, scegli di nuovo Rimuovi nell’app. Verifica il registro della TV e i pacchetti prima di continuare, senza ripetere una rimozione completata. Se è ancora in corso, attendi un minuto. Se il risultato non è verificabile, riavvia la TV e verifica di nuovo; conserva il rapporto per il supporto.

## Uso e ripristino

Le frecce selezionano, OK apre; tieni premuto OK per riordinare. Un breve Indietro conserva navigazione e conferma di uscita dell’app. Home apre il launcher quando il controllo è attivo. Nelle nuove compilazioni, tieni premuto Indietro per 1,2 secondi per aprire LG Home una volta. L’interruttore del controllo Home e le impostazioni restano invariati.

**Nuove compilazioni: premi Home tre volte entro due secondi**, rilasciandolo tra le pressioni. Ripristina LG Home e interrompe il controllo senza cancellare le preferenze. Con No-root Helper fino alla 0.6.13 inclusa, tieni invece premuto Home per circa due secondi. La pressione prolungata di Home non è il gesto di emergenza di Root.

No-root: apri **Home Helper** dalle app LG per riprendere; aprire solo Home non annulla l’arresto. Root: attiva **Cambia Home** nelle impostazioni Home per riprendere. **Apri LG Home** apre LG Home una volta senza cambiare la destinazione di Home. Per ripristinare LG Home come destinazione permanente, disattiva **Cambia Home** o esegui `cytv restore`. Non eseguire entrambi i controllori insieme. Se il problema ricompare, lascia attivo LG Home.

```sh
./cytv --language it status
./cytv --language it doctor --report
./cytv --language it restore
./cytv --language it uninstall
```

Dopo un’interruzione, esegui prima `status` e conserva i registri. `restore` ripristina LG Home senza rimuovere app; `uninstall` lo ripristina prima della rimozione. I dati di ripristino Root restano intenzionalmente: non cancellarli per forzare una reinstallazione. Controlla i rapporti prima di condividerli; non pubblicare chiavi o cartelle dei profili.

## Aggiornamenti e rimozione

Dopo la connessione, cytv mostra versione installata → inclusa e distingue prima installazione, reinstallazione e downgrade. Controlla il riepilogo prima della conferma; `--yes` non rende sicuro un passaggio incompatibile. Conserva pacchetti funzionanti e copie private delle impostazioni. Per gli aggiornamenti dal computer ferma No-root Helper prima di sostituire i pacchetti; non disinstallare prima. Non sovrascrivere un ambiente Root attivo con una sola IPK: usa il percorso previsto da cytv. Rimuovere l’app desktop non rimuove le app TV.

La candidata aggiunge **Aggiorna tutto** in Impostazioni → Aggiornamenti software. Il System Updater indipendente verifica un insieme firmato per l’edizione: Home, Helper e Home Updater per No-root su TV con root; Root Home, Root Updater e runtime di controllo/ripristino per Root. L’installazione dalla TV richiede **root, Homebrew Channel**, Python compatibile, Node.js 8+ e servizi webOS funzionanti. Su TV senza root usa il computer.

Per una prima installazione usa l’installer completo della candidata, che prepara Home e l’Updater di ripristino dell’edizione. Questa versione di transizione non è offerta dal feed stabile.

Se Root è già installato e Root Updater è ancora presente, una reinstallazione generica può essere rifiutata intenzionalmente. Prima esegui `status` e la diagnostica, poi verifica la transazione e lo stato di ripristino nell’Updater esistente. Risolvi le operazioni attive o incerte tramite il relativo percorso di ripristino precedente; la transizione dell’infrastruttura va valutata sullo stato reale della TV. Non cancellare il diario né aggirare il blocco con `--yes`, una IPK isolata o un vecchio OTA. L’OTA della sola app non installa la nuova infrastruttura. Segui il [controllo della TV esistente](../UPDATES.md#one-time-computer-preparation).

Solo dopo aver verificato una configurazione compatibile con Home `systemUpdateProtocol = 1` e l’Updater di ripristino appropriato, abilita il supervisore dal computer. Nell’installer scegli l’opzione per abilitare gli aggiornamenti di tutti i componenti TV; per Root, con connessione SSH root salvata:

```sh
./cytv --language it enable-system-updates --edition root --host TV_ADDRESS
```

Per No-root su TV con root, prepara prima Home/Helper/Home Updater dal computer e usa il procedimento con alias SSH root in [Aggiornamenti](../UPDATES.md#one-time-computer-preparation). Il supervisore salva una base di ripristino verificata dei componenti realmente installati. Un vecchio aggiornamento OTA della sola app non installa il nuovo runtime Python, il supervisore o l’infrastruttura degli updater. Dopo la preparazione usa il percorso comune: gli installer precedenti in conflitto vengono rifiutati.

L’installazione richiede conferma, poi verifica automaticamente l’avvio. Le impostazioni e il profilo vengono conservati; un arresto esplicito o di emergenza del controllo Home non viene annullato. La schermata mantiene il fuoco del telecomando: Su/Giù scorre le note, Sinistra/Destra sceglie le azioni. Un punto arancione indica una nuova versione, anche quando richiede il computer. Apri Ripristino dall’Updater per conoscere lo stato e la versione precedente disponibile. Il ripristino del sistema torna all’intero insieme precedente e al profilo salvato; le modifiche successive alle impostazioni possono andare perse. La verifica automatica dell’avvio non elimina il ripristino, che resta disponibile fino alla transazione successiva.

Dopo un’interruzione esegui `status`, conserva il diario e i dati di ripristino. Un risultato ambiguo blocca nuove installazioni e ripristini; leggere una versione non dimostra che l’installer abbia terminato. Non cancellare diari, blocchi o slot Python per forzare un tentativo. Conserva il rapporto `doctor --report`: distingue i requisiti Root falliti e registra codici numerici SSH senza credenziali o output grezzo. Controllalo comunque prima di condividerlo.

## Verifiche hardware e limiti

Root 0.2.0, Root Updater 0.2.0 e supervisore 1.0.0 sono stati verificati su OLED55C3RLA / firmware 43.21.71 / webOS 11.2.0 (`d344d92`, contenuto identico a `4b66951`). Superati comandi, triplo Home e ripresa, standby/risveglio con Emby aperto per 70 secondi, menu versioni e messaggio chiaro con feed non disponibile. Avvio a freddo reale, Helper 0.6.19 su TV, UK6540PTD e aggiornamento/ripristino completo firmato non sono stati testati. Il rilascio stabile accetta queste prove limitate; gli altri modelli non sono validati.

No-root controlla l’ABI della shell e accetta un kernel a 64 bit solo con ambiente ARM32 verificato. Un nome di modello o `armv7l` non garantiscono compatibilità. Mantieni i limiti hardware della versione effettivamente provata.

No-root: Impostazioni Home → Modalità sviluppatore raccoglie rinnovo Beta, verifica sessione e diagnostica. Controlla sempre il timer ufficiale. Home Helper mostra il proprio stato e richiede conferma per riprendere dopo un arresto.

Documentazione tecnica: [desktop](../DESKTOP_INSTALL.md), [CLI](../CLI.md), [installazione manuale](../MANUAL_INSTALL.md), [ripristino](../RECOVERY.md), [edizioni](../EDITIONS.md), [aggiornamenti](../UPDATES.md).

Se Root mostra `Denied methods call status` subito dopo la preparazione del supervisore, chiudi e riapri Home Root una volta, poi controlla gli aggiornamenti. Se persiste, conserva diagnostica e stato di ripristino.

1.2.0 (#51): dopo il rifiuto di un pacchetto da parte della TV, il rapporto JSON conserva solo la categoria dell’operazione, codici numerici limitati, uno stato del pacchetto consentito e un risultato booleano. Esclude il testo originale dell’errore, percorsi e ID delle app. Controllalo prima di condividerlo; nessun tentativo automatico. La risoluzione del problema di installazione su UN70006LA non è ancora confermata.

1.2.0 (#59): se lo stato di Helper non può essere verificato, **Avvia Helper** resta disponibile con conferma. Aprire il riquadro non riavvia Helper e non annulla un arresto di emergenza. Le impostazioni Home richiedono che il controllo risponda.

1.2.0 (#55): Root verifica la migrazione prima di installare. Un’installazione interrotta prima del provisioning può essere rimossa senza uno snapshot LS2 mai creato; conserva una ricevuta verificata per la normale archiviazione e reinstallazione di cytv. Snapshot mancanti nelle fasi successive o prove in conflitto bloccano ancora la pulizia. Serve il nuovo driver; il problema di avvio del servizio di recupero su OLED Flex resta irrisolto.

## Blocco firmware LG in 1.2.0

Solo Root: Impostazioni Home → Aggiornamenti firmware LG modifica l’impostazione esistente di Homebrew Channel. Include gli aggiornamenti di sicurezza del firmware; quelli di Clean Your TV restano separati. Serve un vero riavvio della TV in entrambe le direzioni; lo standby non basta. L’interruttore mostra l’impostazione salvata, non un blocco effettivo verificato. Alcune TV controllano prima del blocco; gli avvisi possono restare e può servire un blocco sul router. Homebrew conserva l’impostazione dopo rimozione o rollback di CYTV. Se non disponibile o non confermato, controlla Homebrew e aggiorna lo stato. Il verbale di accettazione descrive la portata dei test TV.

[LG firmware blocking](../LG-FIRMWARE-UPDATES.md) · [1.2.0](../RELEASE-1.2.0-ACCEPTANCE.md)
