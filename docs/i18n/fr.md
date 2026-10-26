# Clean Your TV — guide d’utilisation

No-root et Root sont des options équivalentes pour différentes configurations du téléviseur. Choisissez No-root pour LG Developer Mode ou Root si vous disposez déjà d’un accès root par SSH. La compatibilité et les essais réalisés sont propres à chaque édition.

## Prérequis

Ce guide décrit **[v1.2.0 stable](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/tag/v1.2.0)**. Les liens `releases/latest/download` fournissent la version stable publiée. Voir [installation](../INSTALL.md) et [notes de version](../RELEASE-1.2.0.md).

La version contient cytv **0.3.1**, Home **1.4.1**, Home Helper **0.6.19**, Root Edition **0.3.0**, Home Updater et Root Updater **0.2.1**, Android **0.2.1-preview** (code de version **10**) et le superviseur System Updater **1.0.0** (protocole **1**). Ce sont les composants de v1.2.0.

Root 0.2.0, Root Updater 0.2.0 et le superviseur 1.0.0 ont été vérifiés sur OLED55C3RLA / micrologiciel 43.21.71 / webOS 11.2.0 (`d344d92`, contenu produit identique à `4b66951`). Commandes, triple Home et reprise, veille/réveil avec Emby ouvert pendant 70 secondes, menus des versions et message clair en cas de flux indisponible ont réussi. Le vrai démarrage à froid, Helper 0.6.19 sur TV, UK6540PTD et une mise à jour/restauration complète signée restent non testés. La publication stable accepte ces preuves limitées ; les autres modèles ne sont pas validés.

Allumez le téléviseur et reliez-le au même réseau local de confiance que l’ordinateur. L’ordinateur peut ensuite rester éteint. La compatibilité dépend du modèle, du micrologiciel et de la télécommande ; des essais matériels restent à terminer pour Root.

- **No-root :** activez LG Developer Mode et Key Server. Saisissez la phrase secrète affichée sur le téléviseur et acceptez sur celui-ci la demande d’association distincte. Developer Mode doit rester actif : son expiration peut supprimer les applications installées ainsi. Surveillez son compteur officiel même avec le renouvellement Beta activé. La surveillance du Helper nécessite le réseau local.

Le Helper No-root mis à jour nécessite Node.js 0.12.2 ou ultérieur sur le téléviseur. L’installateur vérifie ce prérequis avant l’installation. Les anciens paquets publiés ne bénéficient pas automatiquement de cette compatibilité ; l’accès à la télécommande, la veille et le démarrage à froid restent à tester sur chaque modèle.

- **Root :** un accès SSH root existant est nécessaire. L’installateur ne roote pas le téléviseur. N’activez pas Developer Mode sur une installation déjà rootée. Conservez l’accès root et les services de récupération.

## Python facultatif pour Root dans v1.1.0

Root exige un Python **3.9+** fonctionnel sur le téléviseur. L’installateur vérifie les modules nécessaires (dont `json` et `fcntl`), les verrous, les opérations sur les fichiers et les sous-processus ; le numéro de version seul ne suffit pas. Un interpréteur existant adapté évite le téléchargement supplémentaire. Sinon, la configuration télécharge sur l’ordinateur ou l’appareil Android un **CPython 3.13.17 pour ARMv7 soft-float** vérifié, puis le transfère par SSH de confiance ; le téléviseur n’a pas besoin d’Internet. L’archive facultative n’est pas incluse dans les installateurs ordinaires : environ **26.3 MB** à télécharger, **51.5 MB** pour le transfert SSH normalisé et **119.3 MB** installés ; **320 MiB** libres sont nécessaires à la préparation initiale. Cet environnement privé ne remplace ni Python système, ni libc, ni le PATH global.

Un chargeur et des bibliothèques compatibles restent nécessaires. L’accès root SSH, Node.js **8+**, `luna-send` et les répertoires webOS des applications et services restent requis ; No-root Helper exige Node.js **0.12.2+**. Le LG UK6540PTD / micrologiciel 05.50.70 / ARM32 du ticket #37 (Python 2.7.12 sans Python 3) **n’a pas été validé sur matériel** avec cet environnement. Les essais QEMU ne valident ni le téléviseur, ni le démarrage à froid, ni la télécommande, ni le retour en arrière. Les résultats matériels antérieurs restent limités aux modèles, micrologiciels et fichiers testés.

Pour préparer un cache vérifié sur un ordinateur connecté à Internet **sans contacter de téléviseur** :

```sh
./cytv --language fr --prepare-python-runtime
```

Utilisez le même répertoire de données privé pour l’installation. Pour déplacer le cache, préparez un nouveau répertoire dédié avec `--data-dir /path/to/private-data` et utilisez cette option pour les deux commandes. Ne copiez pas vos clés SSH et profils habituels dans un cache partagé. L’état, le diagnostic, la restauration et la suppression ne téléchargent pas Python automatiquement. Conservez les versions de l’environnement référencées par les outils de mise à jour ou la récupération. Voir les [détails sur Python](../OPTIONAL-PYTHON.md).

## Installation et langue

- **Windows x64 :** téléchargez `cytv-windows-x64-desktop.zip`, choisissez **Extraire tout** dans l’Explorateur, puis ouvrez `cytv-desktop/cytv-desktop.exe`. Gardez le dossier `_internal` à côté. La signature d’éditeur Windows n’est pas configurée. La console séparée est `cytv-windows-x64.exe` ; renommez-la en `cytv.exe` et utilisez `.\cytv.exe` dans PowerShell pour les commandes suivantes.
- **macOS 13+ :** décompressez `cytv-macos-arm64.zip` pour Apple Silicon ou `cytv-macos-x64.zip` pour Intel. Placez `cytv.app` dans Applications et ouvrez-la ; autorisez l’accès au réseau local. En cas de blocage d’un téléchargement fiable, utilisez Confidentialité et sécurité → Ouvrir quand même, sans désactiver Gatekeeper. La validation sur les anciens systèmes reste ouverte.
- **Linux x64 :** sous Ubuntu 22.04+, Debian 12+ ou Mint 21+, installez `cytv-linux-x64.deb` avec le gestionnaire graphique de paquets, puis ouvrez Clean Your TV depuis le menu. Internet peut être nécessaire pour les bibliothèques. Linux ARM n’est pas fourni. L’exécutable autonome `cytv-linux-x64` est la CLI ; utilisez le `.deb` pour l’application graphique.

[Installateur Android](../../android/README.md) : les dix langues sont disponibles. Le bouton en haut à droite affiche la langue actuelle ; touchez-le pour en choisir une autre. Le choix est enregistré sur le téléphone.

Sur Android, l’action de maintenance choisie reste visible pendant la connexion et affiche sa propre progression. L’interface utilise la police système du téléphone avec des libellés et des aides plus grands.

L’assistant utilise initialement la langue du système et mémorise votre choix explicite. Sur le téléviseur, ouvrez **Paramètres → Langue** et choisissez une langue ou l’option automatique du système. Les préférences du téléviseur et de l’installateur sont indépendantes. Les codes figurent dans l’[index des langues](../LANGUAGES.md).

Pour la CLI téléchargée séparément sous macOS/Linux, depuis son dossier décompressé :

```sh
chmod +x cytv
./cytv --language fr install
```

Choisissez le téléviseur ou son adresse IP, l’édition, puis vérifiez le récapitulatif. N’acceptez une nouvelle identité SSH que pour votre téléviseur sur un réseau fiable ; une clé enregistrée modifiée bloque la connexion. Root prépare la récupération et active Home immédiatement, sans essai temporaire ni étape de conservation. Testez flèches, OK, Home, Retour/Annuler, volume, veille et démarrage à froid.

Si la suppression de Root est interrompue, choisissez à nouveau Supprimer dans l’application. Elle vérifie le journal du TV et les paquets avant de continuer, sans répéter une suppression terminée. Si l’opération est en cours, attendez une minute. Si le résultat reste invérifiable, redémarrez le TV et vérifiez à nouveau ; conservez le rapport pour le support.

## Utilisation et récupération

Les flèches sélectionnent, OK ouvre ; maintenez OK pour réorganiser. Un appui bref sur Retour conserve la navigation et la confirmation de sortie de l’application. Home ouvre le lanceur si le contrôle est actif. Dans les nouvelles compilations, maintenez Retour pendant 1,2 seconde pour ouvrir LG Home une fois. L’interrupteur du contrôle de Home et vos paramètres restent inchangés.

**Nouvelles compilations : appuyez trois fois sur Home en deux secondes**, en relâchant entre les appuis. Cela rétablit LG Home et arrête le contrôle sans effacer vos préférences. Avec No-root Helper jusqu’à 0.6.13 inclus, maintenez plutôt Home environ deux secondes. Maintenir Home n’est pas le geste d’urgence de Root.

No-root : ouvrez **Home Helper** dans les applications LG pour reprendre ; Home seul ne supprime pas l’arrêt. Root : activez **Changer Home** dans les paramètres de Home pour reprendre. **Ouvrir LG Home** ouvre LG Home une fois sans modifier la destination de Home. Pour rétablir LG Home comme destination permanente, désactivez **Changer Home** ou exécutez `cytv restore`. N’exécutez jamais les deux contrôleurs ensemble. Si la panne revient, laissez LG Home actif.

```sh
./cytv --language fr status
./cytv --language fr doctor --report
./cytv --language fr restore
./cytv --language fr uninstall
```

Après interruption, lancez d’abord `status` et conservez les journaux. `restore` rétablit LG Home sans supprimer les applications ; `uninstall` le rétablit avant leur suppression. Les données de récupération Root sont conservées volontairement : ne les effacez pas pour forcer une réinstallation. Vérifiez les rapports avant partage ; ne publiez ni clés ni dossiers de profils.

## Mises à jour et suppression

Gardez les paquets fonctionnels et des sauvegardes privées des paramètres. Pour remplacer les paquets No-root depuis l’ordinateur, arrêtez d’abord Helper et mettez à jour sans désinstaller : la désinstallation peut effacer les réglages. Supprimer l’application de bureau ne supprime pas les applications TV. Ne remplacez pas un environnement Root actif par une IPK isolée ; utilisez le parcours explicite de récupération ou de réinstallation de cytv.

Dans v1.1.0, **Tout mettre à jour** dans Paramètres de Home → Mises à jour logicielles utilise un ensemble signé : Home, Helper et Home Updater pour No-root sur un téléviseur rooté ; Root Home, Root Updater et l’environnement de contrôle de Home et de récupération pour Root. Cela exige root, Homebrew Channel, les services d’installation webOS fonctionnels, Python 3.9+ et Node.js 8+. Un téléviseur non rooté continue à utiliser l’installateur sur ordinateur.

Pour une nouvelle installation, utilisez l’installateur complet de la version stable afin d’installer la version de transition de Home et l’outil de récupération correspondant à l’édition. **Une installation Root existante avec un Root Updater conservé peut bloquer volontairement une réinstallation générique.** Examinez d’abord `status`, Récupération et la transaction existante en suivant le parcours de récupération adapté à l’ancienne installation ; voir le [contrôle du téléviseur déjà installé](../UPDATES.md#one-time-computer-preparation). Ne supprimez pas les journaux et ne contournez pas cette vérification. Une ancienne mise à jour OTA de Home seul n’installe pas la nouvelle infrastructure.

Activez les **mises à jour de tous les composants TV** dans l’installateur de bureau uniquement lorsque les composants installés et l’état de récupération sont prêts. Pour une connexion SSH root enregistrée et l’édition Root :

```sh
./cytv --language fr enable-system-updates --edition root --host TV_ADDRESS
```

Cette action distincte installe le superviseur fixe et sauvegarde l’ensemble installé comme référence de retour en arrière. Elle exige `systemUpdateProtocol = 1` dans les métadonnées de Home installé, sans réinstaller Home ni modifier sa destination. L’édition No-root ordinaire sur un TV rooté exige SSH root et les composants correspondants installés depuis l’ordinateur ; voir la [préparation initiale](../UPDATES.md#one-time-computer-preparation). Une ancienne mise à jour OTA de Home seul **n’installe pas** la nouvelle infrastructure du superviseur, de Python ou des outils de mise à jour. Une fois le superviseur installé, les anciens installateurs incompatibles sont bloqués ; ne remplacez pas les paquets en le contournant.

Les mises à jour système vérifient et mettent en cache l’ensemble candidat et l’ensemble précédent, conservent réglages et profils et continuent si Home ou un outil de mise à jour se ferme. La récupération restaure tout l’ensemble précédent et son profil. Les nouveaux essais physiques, dont la libération des entrées de Helper 0.6.19, le démarrage à froid, la mise à jour complète et le retour en arrière, restent à effectuer ; les anciens essais C3 ne couvrent que leurs paquets Home documentés. Voir les [détails de mise à jour et récupération](../UPDATES.md).

Documentation technique en anglais : [bureau](../DESKTOP_INSTALL.md), [CLI](../CLI.md), [No-root](../INSTALL.md), [installation manuelle](../MANUAL_INSTALL.md), [récupération](../RECOVERY.md), [éditions](../EDITIONS.md).

Après connexion, cytv lit les versions du téléviseur et affiche la version actuelle → incluse pour Home et Home Helper (No-root), ou Root et Root Updater. Vérifiez et confirmez avant installation. Les premières installations, réinstallations et retours à une version antérieure sont signalés ; `--yes` ignore la confirmation mais affiche les versions.

Les mises à jour logicielles affichent uniquement les détails de la version installée ou plus récente. Ouvrez Récupération pour voir la version enregistrée à restaurer ou la raison de son indisponibilité ; Retour revient aux mises à jour.

No-root vérifie l’ABI du shell du téléviseur et accepte un noyau 64 bits avec un environnement ARM32 confirmé. En cas d’échec, joignez le JSON de diagnostic généré ; ne partagez ni clés ni phrases secrètes.

Les mises à jour de Home demandent une confirmation avant l’installation ; le démarrage est ensuite vérifié automatiquement. L’actualisation de l’état conserve le bouton sélectionné avec la télécommande.

Les deux éditions vérifient automatiquement le démarrage ; aucune confirmation manuelle du bon fonctionnement n’est nécessaire. L’ancien retour en arrière de Home seul restaure le paquet Home précédent et son profil ; System Updater restaure l’ensemble complet précédent. La récupération reste disponible après confirmation, sans limite de temps, jusqu’à la prochaine mise à jour. Les réglages modifiés ensuite peuvent être perdus ; le retour en arrière demande confirmation. Les mises à jour et restaurations No-root sur le TV exigent toujours root et Homebrew Channel. Après interruption, lancez `status` et consultez Récupération. Un résultat d’installation incertain bloque réinstallation et retour en arrière : conservez rapports, journaux et versions de l’environnement, sans effacer l’état pour forcer un nouvel essai. Reprenez une opération cytv interrompue uniquement par son parcours de récupération vérifié.

L’écran de mise à jour sépare les versions, l’état et les nouveautés lisibles. Haut/Bas fait défiler les notes ; Gauche/Droite choisit les actions fixes en bas. Après les vérifications automatiques du démarrage, Root rétablit le contrôle de Home s’il était activé ; No-root conserve l’état du Helper séparé. Un réglage désactivé ou une désactivation explicite ou d’urgence reste désactivé.

L’ouverture des réglages de Home lance une recherche de mises à jour en arrière-plan. Un point orange sur Mises à jour logicielles indique une version plus récente, même si elle nécessite une installation depuis l’ordinateur. Les réglages restent utilisables pendant la recherche.

No-root : ouvrez Réglages de Home → Mode développeur pour le renouvellement automatique, la vérification de session et le diagnostic. L’écran principal conserve un bref état et les erreurs de renouvellement visibles. Retour ramène aux réglages de Home. Les deux éditions regroupent Langue, Mises à jour logicielles et Réglages TV sur la même ligne ; la flèche ouvre chaque option.

À l’ouverture, Home Helper indique son rôle et son état. Le démarrage d’un Helper arrêté nécessite une confirmation. Home Updater et Root Updater expliquent la restauration ; les mises à jour habituelles sont dans les paramètres de Home. La restauration est proposée uniquement si une version enregistrée existe et demande confirmation avant de remplacer Home et ses paramètres.

Si Root affiche `Denied methods call status` juste après la préparation du superviseur, fermez puis rouvrez Home Root une fois et vérifiez les mises à jour. Si l’erreur persiste, conservez le diagnostic et les données de récupération.

[1.1.0 hardware acceptance](../RELEASE-1.1.0-ACCEPTANCE.md)

1.2.0 (#51) : après un refus de paquet par le téléviseur, le rapport JSON conserve uniquement la catégorie d’opération, des codes numériques bornés, un état de paquet autorisé et un résultat booléen. Il exclut le texte brut de l’erreur, les chemins et les identifiants d’applications. Vérifiez-le avant de le partager ; aucune nouvelle tentative automatique. La correction de l’échec d’installation sur UN70006LA n’est pas confirmée.

1.2.0 (#59) : si l’état de Helper ne peut pas être vérifié, **Démarrer Helper** reste disponible avec confirmation. Ouvrir la tuile ne redémarre pas Helper et ne lève pas un arrêt d’urgence. Les réglages Home nécessitent un contrôle qui répond.

1.2.0 (#55) : Root valide la migration avant l’installation. Une installation interrompue avant le provisionnement peut être supprimée sans instantané LS2 jamais créé ; un reçu vérifié est conservé pour l’archivage et la réinstallation habituels de cytv. Un instantané manquant plus tard ou des preuves contradictoires bloquent toujours le nettoyage. Le nouveau pilote est requis ; l’échec du démarrage du service de récupération sur OLED Flex reste non résolu.

## Blocage du micrologiciel LG dans 1.2.0

Root uniquement : Réglages Home → Mises à jour du micrologiciel LG modifie le réglage existant de Homebrew Channel. Cela inclut les mises à jour de sécurité du micrologiciel ; celles de Clean Your TV restent séparées. Un vrai redémarrage du TV est nécessaire dans les deux sens ; la veille ne suffit pas. Le bouton montre le réglage enregistré, pas un blocage effectif vérifié. Certains TV vérifient avant le blocage ; les alertes peuvent rester et un blocage sur le routeur peut être nécessaire. Homebrew conserve le réglage après suppression ou retour arrière de CYTV. En cas d’indisponibilité ou de résultat non confirmé, vérifiez Homebrew et actualisez l’état. Le périmètre des tests TV figure dans le compte rendu de validation.

[LG firmware blocking](../LG-FIRMWARE-UPDATES.md) · [1.2.0](../RELEASE-1.2.0-ACCEPTANCE.md)
