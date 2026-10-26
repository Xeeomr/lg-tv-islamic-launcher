# Риски LG webOS из чужих issues и исправлений

Дата: 25 октября 2026. Код: `3f56cc1df911ac525541abba0a666daae425137c` и текущее рабочее дерево. Исследование не меняет приложение и не выполняет команды на ТВ.

После исследования пользователь поручил исправления. В рабочем дереве исправлены пункты 1–5: tar-даты, импорт URL и совместимая сигнатура HTTPS для Node 8, права No-root staging, собственные CA и проверки TV runtimes. Общий установщик Root дополнительно копирует только IPK в `/var/lib/clean-your-tv-installer` с проверкой доверенных родителей, сохраняя recovery-код и rollback cache приватными; при неизвестном результате установки копия IPK сохраняется. Ниже сохранены исходные наблюдения аудита; статус аппаратной совместимости от локальных исправлений не меняется. Новые проверки входят в `scripts/test.sh`. CA snapshot и обновление уже установленной инфраструктуры описаны в [TLS trust](../../TLS-TRUST.md).

### Что остаётся проверить на ТВ

Пункты 6–7 остаются аппаратными сценариями, а не обещанием исправления:

- Установка финальных IPK на старой webOS 5 и на webOS 26 с журналом pkgverifier/appinstalld.
- Новая установка Root, установка отдельного Root Updater и rollback с приватным исходным IPK и доступностью `/var/lib/clean-your-tv-installer` для appinstalld; при потере ответа не повторять установку до выяснения состояния backend.
- Продление Developer Mode от настоящего service UID, сравнение server Check и состояния на ТВ, Quick Start+ on/off и сохранение приложений после исходного срока сессии.
- Standby/wake, поздняя сеть, переподключение пульта, аварийный выход с зависшим renderer и реальный failsafe на финальном bundle.
- Отдельно согласованная cold-power проверка; прежнее решение отложить прямое отключение AC сохраняется.

Установщик не обходит отзыв ключей SSAP, права LS2 или pinning Root infrastructure. Бета-статус автопродления и аппаратные ограничения сохраняются.

Два дефекта воспроизведены локально: нулевые даты внутри IPK и отказ загрузчиков обновлений без глобального `URL`. Ещё один сильный кандидат — недоступный другим UID каталог установки. Остальные пункты разделяют установленный факт в коде и аппаратные сценарии, для которых пока недостаточно доказательств.

## Что изучено

| Проект | Изученные проблемы и изменения | Связь с нашим проектом |
| --- | --- | --- |
| webosbrew/webos-homebrew-channel | TLS #167/#179 и PR #189; failsafe PR #164; lifecycle #244; права #255; startup #256; changelog | Загрузка обновлений, LS2, привилегии, загрузка и восстановление |
| webosbrew/dev-manager-desktop | v1.99.20; renewal #244/#256/#279; macOS PR #421 и issue #429 | Установка, SSH, обновление Developer Mode и desktop packaging |
| Simon34545/lginputhook | IPK #38 и v1.5.1; standby #39; tvservice #41; cold boot #13 | Нативный ввод, формат пакета, питание |
| home-assistant-libs/aiowebostv | pairing #718; потеря WRITE_SETTINGS #728 | SSAP, разрешения и изменение прошивок |
| OmkarK97/webos-vibehack | README troubleshooting и issue #1 | Непосредственный предшественник No-root |
| lasharor/cleanyourtv-WebOS | release notes 1.4.4–1.4.13 | Другой webOS launcher: runtime requirements, rollback, Home |
| jellyfin/jellyfin-webos | issues #115/#252 и список проблем | Рассмотрены чёрные экраны; их причины не перенесены на наш launcher без доказательств |

Это целевая выборка issues, PR и release notes, а не полный просмотр истории каждого репозитория. Сообщение пользователя в issue рассматривается как наблюдение, а предложенная им причина — как гипотеза, пока её не подтверждают исправление или отдельная проверка.

## 1. P1 — Наши IPK повторяют исправленный баг с датой 1970 года

**Чужой случай.** На webOS 5.3.0 пакет lginputhook не устанавливался с ошибкой `-5`. В журнале pkgverifier причиной отказа извлечения control был слишком старый timestamp. Автор проекта связал исправление в 1.5.1 с переходом на новый CLI, который перестал записывать нулевую дату control. [Issue #38](https://github.com/Simon34545/lginputhook/issues/38), [release 1.5.1](https://github.com/Simon34545/lginputhook/releases/tag/v1.5.1).

**У нас.** `cytv/package.py:47–65` и `root-edition/build.py:22–37` создают `TarInfo` без задания `mtime`; по умолчанию это 0. Это касается control и данных. В `root-edition/tests/test_build_root.py:50` тест даже требует `m.mtime == 0`. Персонализация пакетов также пересобирает data через `cytv.package.tgz`.

**Проверено локально:** оба настоящих сборщика для контрольного файла выдали `('control', 0)`. Это проверка содержимого tar, а не только gzip-заголовка. Удалять `gzip(..., mtime=0)` само по себе недостаточно.

**Последствие:** риск отказа установки и отката на затронутых старых прошивках. Отказ именно нашего IPK на физическом webOS 5 в этом исследовании не проверялся.

**Минимальное исправление:** одинаковая фиксированная современная дата для tar entries в обоих сборщиках. Воспроизводимость сохранится. Обновить проверку, которая сейчас закрепляет epoch 0; проверять control и data у финального персонализированного артефакта. Затем установка на webOS 5 с журналом pkgverifier.

## 2. P1 — Каталог установки закрыт для отдельного UID appinstalld

**Чужое исправление.** Dev Manager v1.99.20 перенёс IPK из `/tmp` в `/media/developer/temp` и изменил права для установки на webOS 11. Release notes прямо связывают это с ограничениями appinstalld. [Release v1.99.20](https://github.com/webosbrew/dev-manager-desktop/releases/tag/v1.99.20).

**У нас.** В `cytv/operations.py:164–170` путь уже правильный, но команда `umask 077; ... mkdir <stage>` создаёт новый вложенный каталог с правами 0700. Файл внутри загружается с 0644. При работе installer backend под другим непривилегированным UID файл всё равно нельзя прочитать: нет права прохода по каталогу.

**Статус:** права 0700 следуют непосредственно из команды. Применение отдельного UID/namespace к нашему пути на конкретной новой прошивке требует ТВ. Это сильный кандидат на install failure на C5/webOS 26, но не доказанная причина уже известного Helper startup issue.

**Минимальное исправление:** обеспечить чтение IPK и проход по всем каталогам для реального backend, сохранив запрет посторонней записи. Не переносить 0777 на весь staging без необходимости. Проверить фактический inode/mode и установку через LS2 на webOS 26; в локальном тесте моделировать разные UID. Текущий mock в `tests/cytv/test_operations.py` права доступа backend не проверяет.

## 3. P1 — Оба загрузчика обновлений отвергают все URL в Node.js 8

**Чужой опыт.** В другом launcher явно учитывают Node.js 8 на webOS 5; в 1.4.13 добавили остановку на слишком старой платформе. [Release notes cleanyourtv-WebOS](https://github.com/lasharor/cleanyourtv-WebOS/releases).

**У нас.** `updater-service/transport.js:5` и `root-edition/updater/fetch.js:9` вызывают `new URL(...)` без импорта. В Node.js глобальный `URL` появился только в v10; в v8 доступен `require('url').URL`. [Документация Node.js](https://nodejs.org/api/url.html#class-url), [документация v8](https://nodejs.org/download/release/v8.17.0/docs/api/url.html).

В обоих модулях ReferenceError поглощается `catch`, после чего разрешённый GitHub URL считается запрещённым. До TLS-запроса выполнение не доходит.

**Локальная проверка:** загрузил каждый настоящий модуль в VM с обычным `URL` и с `URL: undefined`. Для одного и того же допустимого адреса оба вернули соответственно `true` и `false`. Это моделирование отсутствующей глобальной функции на Node v23.11.0, а не запуск полного сервиса в Node 8.

**Минимальное исправление:** импортировать `URL` из `url` в обоих модулях. Добавить исполнение модулей под минимальным поддерживаемым TV Node. Проверка браузерных assets под Chrome 38 и `node --check` на современном Node эту ошибку не ловят.

## 4. P1 для старых прошивок — HTTPS зависит от устаревшего CA store телевизора

**Чужое исправление.** Homebrew Channel исправил ошибки сертификатов отдельным Mozilla CA bundle. В разборе #167 указано, что встроенный store Node на webOS 5/6 устарел; PR #189 объясняет, почему простого переключения системного store недостаточно для всех поколений. [Issue #167](https://github.com/webosbrew/webos-homebrew-channel/issues/167), [PR #189](https://github.com/webosbrew/webos-homebrew-channel/pull/189).

**У нас.** `renewal-service/transport.js:20–23`, `updater-service/transport.js:11` и `root-edition/updater/fetch.js` используют стандартный `https` без своего `ca`. Собственный доверенный bundle в этих путях не подключён. Поэтому даже после исправления пункта 3 остаётся зависимость от прошивки и цепочек сертификатов LG/GitHub/CDN.

**Последствие:** невозможность проверить обновление или продлить Developer Mode при рабочем LAN. Подпись release manifest защищает содержимое, но не исправляет TLS-доступность.

**Статус:** зависимость подтверждается кодом; TLS failure на конкретном текущем ТВ не воспроизводился. Нельзя утверждать, что все старые модели уже не работают.

**Минимальное исправление:** поддерживаемый CA bundle для исходящего HTTPS с сохранением проверки имени и сертификата. Проверить конечный CDN после redirect, developer.lge.com, неверное время ТВ и недоверенный сертификат. Не использовать `rejectUnauthorized:false` для внешних загрузок. Наше исключение для локального SSAP — другой путь.

## 5. P2 — Наличие Python 3 не означает совместимость Root runtime

**Чужое исправление.** Другой launcher в 1.4.9 убрал зависимость от Python: установка останавливалась на ТВ без python3. В 1.4.13 отдельно добавили ранний отказ на старой платформе. [Release notes](https://github.com/lasharor/cleanyourtv-WebOS/releases).

**У нас.** Проверка отсутствия Python уже есть: `cytv/operations.py:53–61`. Но она проверяет executable и импорт `json,fcntl`, а не минимальную версию. В `root-edition/runtime/provision.py:23` и `root-edition/updater/device.py:43` используется `Path.is_relative_to`, появившийся в Python 3.9. Python 3.8 может пройти эту предварительную проверку и упасть позднее. [Документация pathlib](https://docs.python.org/3.9/library/pathlib.html#pathlib.PurePath.is_relative_to).

**Минимальное исправление:** проверять поддерживаемую версию TV Python и необходимые API до мутаций; отдельно проверять TV Node. Требования к Node/Python на компьютере сборки не задают версию интерпретаторов телевизора. Переписывать весь Root runtime на Node ради этого аудита не требуется.

## 6. P2 — Рост серверного таймера Developer Mode не закрывает аппаратную приёмку

**Чужие наблюдения.** В Dev Manager #256 пользователь показал успешный Reset и большой таймер Check при расходящемся отображении на ТВ; участники спорили, является ли это лишь отображением. Подтверждён рабочий интерактивный путь — запуск Developer Mode с `extend:true`. В #244/#279 есть похожие жалобы. [#256 с обсуждением](https://github.com/webosbrew/dev-manager-desktop/issues/256), [#244](https://github.com/webosbrew/dev-manager-desktop/issues/244), [#279](https://github.com/webosbrew/dev-manager-desktop/issues/279).

**У нас.** `renewal-service/renewal.js:30–45` делает Check → Reset → Check и требует прирост больше 60 секунд. Это уже защищает от простого ложного `result:success`. Но все наблюдения — с сервера LG; локальный enforcement и сохранение приложений не проверяются. README правильно оставляет функцию Beta и требует следить за официальным таймером.

**Непокрыто:** реальное продление непривилегированным service UID, сравнение серверного и TV состояния, Quick Start+ on/off, настоящий cold boot, сохранение sideloaded приложений после исходного срока сессии. Дополнительно проверить доступность и тип token path: в HBC #256 описана конфигурация с директорией, тогда как наш `readToken` ожидает файл; это не универсальное свойство всех webOS.

**Вывод:** считать это пробелом доказательств, а не установленным багом продления. Не запускать Developer Mode автоматически каждый час: он выходит на передний план. При неопределённости показывать точный статус и доступный пользователю ручной путь.

## 7. Аппаратный приоритет — cold boot, failsafe и аварийный выход

**Чужой опыт.** В lginputhook standby сломался после изменения инъекции: свежая загрузка работала, wake давал чёрный экран; отдельно описан сбой tvservice. Это сообщения о конкретной реализации, не доказательство общего дефекта webOS. [#39](https://github.com/Simon34545/lginputhook/issues/39), [#41](https://github.com/Simon34545/lginputhook/issues/41). Homebrew Channel отдельно добавлял sync при очистке failsafe; само описание PR осторожно оценивает ожидаемый эффект. [PR #164](https://github.com/webosbrew/webos-homebrew-channel/pull/164).

**У нас механизмы другие.** No-root relay работает через evdev, а не инъекцию в tvservice. Он проверяет устройства, имеет heartbeat и снимает grab при выходе. Root boot gate проверяет marker текущей загрузки вместе с отсутствием failsafe; восстановление вынесено отдельно. Поэтому переносить на нас причину `hexdump` collision из inputhook неверно.

**Оставшийся пробел:** `root-edition/RELEASE-ACCEPTANCE.md` прямо оставляет cold-power проверку отложенной и один пропуск emergency gesture открытым. `docs/COMPATIBILITY.md` не подтверждает C5 startup и новые исправления на C4. Это существеннее добавления ещё одного mock-теста того же автомата.

**Нужна матрица на финальном bundle:** standby и быстрый wake; Quick Start+ on/off; cold boot; сеть появляется поздно; переподключение пульта; аварийный выход при зависшем renderer; восстановление при недоступном launcher/сервисе. Прямое отключение AC проводить в отдельной согласованной аппаратной сессии: ранее оно было отложено пользователем. Этот аудит не меняет это решение.

## Что уже защищено или нельзя объявить нашим багом

| Чужая проблема | Наша защита и остаток |
| --- | --- |
| Pairing ломается из-за blacklist signed manifest, порт 3000 перестаёт работать — [aiowebostv #718](https://github.com/home-assistant-libs/aiowebostv/issues/718) | `lgtv.py` и `native/app/screen-watch.js` уже используют unsigned manifest и WSS 3001. На отзыв ключа watcher останавливается; полезна отдельная проверка восстановления pairing после OTA |
| После удаления signed manifest теряется WRITE_SETTINGS — [aiowebostv #728](https://github.com/home-assistant-libs/aiowebostv/issues/728) | Не добавлять signed manifest обратно ради «полноты». Проверять реально необходимые нам методы и их разрешения; запись picture settings не является функцией launcher |
| macOS не даёт LAN доступ — [Dev Manager PR #421](https://github.com/webosbrew/dev-manager-desktop/pull/421) | В `scripts/desktop_packaging.py:80–86` есть NSLocalNetworkUsageDescription и ad-hoc codesign. Нужна проверка готового .app после скачивания. Гипотеза про RSA из issue #429 не заменяет разбор реального PR |
| Legacy SSH, отсутствие SFTP — [Dev Manager releases](https://github.com/webosbrew/dev-manager-desktop/releases) | `cytv/transport.py` использует Paramiko, обрабатывает legacy RSA для No-root и передаёт файлы через shell с hash/mode verification; SFTP не требуется |
| Процесс Node завершается в ожидании LS2 — [HBC #244](https://github.com/webosbrew/webos-homebrew-channel/issues/244) | Тот issue относится к собственному FakeActivityManager в unreleased main HBC. Мы его не используем; RPC updater имеет timeout, Root recovery держит child process. Это сценарий интеграции с HBC, не доказанный дефект нашего event loop |
| SSH root работает, а клиентский LS2 install/exec запрещён — [HBC #255](https://github.com/webosbrew/webos-homebrew-channel/issues/255) | Root сервис проверяет UID, установщик настраивает собственные roles. Но успешный SSH/checkRoot не заменяет вызов нужного метода от настоящего caller. Проверить после self-update HBC/OTA; не обещать готовность по одному root status |
| Копирование startup поверх подписанного start-devmode удаляет dev apps — [HBC #256](https://github.com/webosbrew/webos-homebrew-channel/issues/256) | `root-edition/startup_hook.py` владеет отдельным init.d hook и не переписывает start-devmode. Не брать этот legacy workaround из чужих инструкций |
| Установка вне /media/developer — [HBC changelog](https://github.com/webosbrew/webos-homebrew-channel/blob/main/CHANGELOG.md) | Наши установленные пути фиксированы. Альтернативная раскладка — ограничение переносимости; перед расширением поддержки нужен отказ до мутаций или разрешение реального пути, а не механическая замена всех строк |

## Порядок устранения

1. Исправить tar timestamps и отсутствие импорта URL. Это локально подтверждённые дефекты с небольшими исправлениями.
2. Проверить staging от UID backend и исправить traversal permissions; после этого повторить установку на webOS 26. Не смешивать результат установки с причиной Helper startup.
3. Задать минимальные TV runtime requirements и обработать CA store. Подтвердить финальные пакеты на старой прошивке и новой C5.
4. Провести отдельную аппаратную приёмку recovery/power и Developer Mode renewal. Рост количества unit-тестов её не заменяет.

## Проверки этого аудита

Среда: локальный Node v23.11.0, Python 3.14.2. ТВ не подключался. Воспроизведение epoch 0 использовало настоящие `cytv.package.tgz` и `root-edition/build.py::tgz`; URL — настоящие JS modules в `vm.runInNewContext` с отсутствующей глобальной функцией.

Запущены следующие существующие проверки:

```sh
node tests/renewal-core.cjs
node tests/renewal-transport.cjs
node tests/updates/service.cjs
node root-edition/tests/test_update_policy.cjs
python3 -m unittest discover -s tests/cytv -p test_operations.py
python3 -m unittest discover -s root-edition/tests -p test_build_root.py
python3 -m unittest discover -s root-edition/tests -p test_boot_gate.py
```

Все перечисленные проверки прошли: renewal core — 12 тестов, renewal transport — 8 сценариев, остальные два JS entry point — без ошибок; Python — 48 + 7 + 5 = 60 тестов. Полный suite и реальное Node 8/TV окружение не запускались. Прохождение этих тестов не закрывает выявленные пробелы: например, сборочный тест прямо считает нулевые даты правильными.

Повторить локальные воспроизведения из корня репозитория:

```sh
python3 - <<'PY'
import io, tarfile, importlib.util, sys
from pathlib import Path
from cytv import package
sys.path.insert(0, str(Path('root-edition').resolve()))
spec = importlib.util.spec_from_file_location('audit_build', 'root-edition/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
for name, build in [('cytv', package.tgz), ('root', builder.tgz)]:
    with tarfile.open(fileobj=io.BytesIO(build({'control': b'Package: audit\n'})), mode='r:gz') as t:
        print(name, [(m.name, m.mtime) for m in t])
PY
node - <<'JS'
const fs = require('fs'), vm = require('vm');
const url = 'https://github.com/Razdva122/clean-your-tv-lg-webos/releases/latest/download/update.json';
for (const file of ['updater-service/transport.js', 'root-edition/updater/fetch.js']) {
  for (const URLValue of [URL, undefined]) {
    const context = {require, module:{exports:{}}, URL:URLValue, Buffer, console, setTimeout, clearTimeout};
    vm.runInNewContext(fs.readFileSync(file, 'utf8'), context, {filename:file});
    console.log(file, typeof URLValue, context.module.exports.allowed(url));
  }
}
JS
```

## Проверка исправлений в отдельной ветке

Ветка `codex/webos-upstream-fixes` создана от `3f56cc1df911ac525541abba0a666daae425137c` в отдельном worktree. Параллельные изменения system-updater в неё не включены.

Полный `bash scripts/test.sh` завершился с кодом 0: 788 Python-тестов (466 Root, 71 setup, 230 installer, 19 Android, 2 preview), а также JS/C, проверки совместимости web assets и синтаксиса. `scripts/build-cytv.py --payload-only` завершился с кодом 0. Отдельная проверка содержимого четырёх фактически собранных IPK подтвердила современные фиксированные tar-даты; CA и лицензии включены в сервисные пакеты.

Аппаратный прогон не выполнялся. Доступность нового защищённого Root staging path для appinstalld на каждом целевом firmware остаётся отдельной проверкой, как и продление Developer Mode и power/recovery матрица. Пакеты не публиковались и на ТВ не устанавливались.
