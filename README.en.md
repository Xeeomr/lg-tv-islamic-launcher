**English** · [العربية](README.md)

# Xee Launcher · Arabic Islamic Home for LG TVs

A clean Arabic home screen for LG webOS TVs, **without root**. It replaces LG's ad-filled home with a calm, Apple TV–style interface with an Arabic and Islamic identity: prayer times, an interactive adhan, the Holy Quran, hadith, a screensaver and wallpapers that follow the time of day.

Built on [Clean Your TV](https://github.com/Razdva122/clean-your-tv-lg-webos) (MIT) and installed through LG's **official Developer Mode** only — no exploit, no jailbreak.

> Tested on **LG 43UQ70006LB** (webOS 22, firmware 04.60.91). Other webOS 22+ models are expected to work but are not verified.

<p align="center"><img src="docs/screenshots/mockups/before-after.jpg" alt="Before and after" width="100%"></p>
<p align="center"><b>Before</b>: LG's original home with ads and promoted content &nbsp;·&nbsp; <b>After</b>: the new interface</p>

<table>
<tr>
<td width="50%"><img src="docs/screenshots/mockups/adhan.jpg" alt="Adhan screen"><p align="center">The adhan screen, shown over any app</p></td>
<td width="50%"><img src="docs/screenshots/mockups/screensaver.jpg" alt="Screensaver"><p align="center">Screensaver</p></td>
</tr>
<tr>
<td width="50%"><img src="docs/screenshots/mockups/settings.jpg" alt="Settings"><p align="center">Settings: 18 sections in Arabic</p></td>
<td width="50%"><img src="docs/screenshots/mockups/city-search.jpg" alt="City picker"><p align="center">Offline city picker</p></td>
</tr>
</table>

## Features

**Home screen**
- 12-hour clock (AM/PM in Arabic), Gregorian and Hijri dates (Umm al-Qura), city name and weather.
- Six prayer times (Fajr, Sunrise, Dhuhr, Asr, Maghrib, Isha) with the next prayer highlighted and a live countdown.
- A Quran verse or hadith card that changes every time you return Home, never repeats back to back and never cuts a text.
- A countdown to the next occasion: Ramadan, then Eid al-Fitr, then Eid al-Adha (an estimate until the official announcement). During Ramadan it shows the day and the days left to Eid; on Eid and the Day of Arafah it shows a greeting.
- Favourite apps: long-press OK on an app for Move, Move to start, Replace, Remove from Home (the app stays installed) and App info.
- The whole interface and settings are in Arabic, right to left.

**Prayer times**
- Computed **offline** for any place with a local astronomical calculation, matching Aladhan within a minute in Saudi Arabia and Egypt.
- Built-in database of 8,099 cities (every city in Arab countries has its Arabic name), search, and automatic location on first start.
- Calculation method chosen automatically per country (Umm al-Qura for Saudi Arabia, the Egyptian authority for Egypt, …) or by hand, Asr school, and per-prayer minute adjustments.

**Interactive adhan**
- At prayer time a full-screen adhan appears over whatever is running, pauses the video, then returns to the previous app and resumes playback.
- Back, EXIT or any key stops the adhan and takes you back; volume keys keep working.
- Options: full adhan, notification only, or off; per-prayer switches; a separate Fajr voice; raising the TV volume during the adhan and restoring it afterwards.
- A pre-prayer alert (5–30 minutes) shown over any app without pausing it.
- "Test the adhan in 30 seconds" to try the whole flow from inside any app.

**Quran and hadith**
- The complete Quran (114 surahs, 6,236 ayahs) in Uthmani script from [Tanzil](https://tanzil.net), offline, set in Amiri Quran.
- An-Nawawi's Forty (42 hadith) and forty Hadith Qudsi with their sources.
- Content: Quran only, hadith only, or alternating.

**Screensaver and wallpapers**
- LG's clock screensaver never shows: over Home the Islamic screensaver takes its place, and over any other app (a paused YouTube video, say) the app simply stays on screen.
- A screensaver after the idle time you choose: slowly moving photo, clock, Hijri date, a verse and the next prayer; the text drifts slightly to protect the panel.
- 20 high-quality Islamic wallpapers under open licences, grouped for Fajr, day, Maghrib and night, changing with the prayer times, with photographer credits, an adjustable dark overlay and a live-preview picker.

**The Holy Quran: radio, audio mushaf and live broadcasts** (the Quran button at the top)
- **Radio**: live Radio Quran Cairo and Saudi Quran Radio, mp3quran.net reciter radios (Al-Husary, Abdul Basit, Al-Minshawi, Mustafa Ismail, Al-Tablawi, Alafasy, Al-Muaiqly, Al-Sudais, Al-Shuraim), tafsir, ruqyah, and morning and evening adhkar.
- **Audio mushaf**: pick any of the 114 surahs and one of 14 reciters; it is recited ayah by ayah with the ayah shown in Uthmani script, the next ayah and a progress bar. Recitation carries on surah after surah, and your khatma is saved and resumed with its progress.
- **Live**: Masjid al-Haram and Masjid an-Nabawi live, full screen; ◀ ▶ switches between them.
- Built for listening all night: automatic reconnect, playback carries on if the system restarts Home, a sleep timer (15 minutes to 4 hours) that can turn the TV off, and "screen off, sound on".
- Recitation and broadcasts pause for the adhan and resume afterwards; what is playing shows on Home and the screensaver.

**Adhkar and reminders**
- Morning adhkar start by themselves after Fajr and evening adhkar after Asr (adjustable), when Home is on screen and nothing else is playing; inside another app you get a notification instead.
- Friday: a reminder for Surat al-Kahf with a "Listen" button, the last hour of Friday, and Thursday night's salawat.
- The evening before: fasting reminders for Arafah, Tasu'a and Ashura and the White Days, and optionally Mondays and Thursdays.

**Night mode**
- From half an hour after Isha until Fajr the wallpaper is darker and the light calmer.

**Phone control (Xee Remote)**
- Open `http://TV-IP:8090` on a phone on the same network, or scan the QR code in Settings → Phone control. The TV shows a 4-digit code to pair the phone once.
- A full remote: arrows, OK, Back, Home, Exit, volume and mute, play and pause, typing on the TV (to search YouTube, say), and turning the screen or the TV off.
- Quran from the phone: radio, surahs, continue the khatma, choose the reciter, live broadcasts and the sleep timer.
- Open any installed app, and every setting: city search, adhan and voices, adhkar and reminders, wallpapers, screensaver and updates.
- Add it to the phone's home screen to use it like an app.

**Automatic updates**
- The TV looks for a new release on GitHub and installs it by itself, no computer needed, while Home is not in use and nothing is playing.
- Every update is signed, and nothing is installed unless the signature and each file's hash match.
- Turn it off or check by hand in Settings → Updates, or from the phone.

**Speed and stability**
- Home and EXIT open the new interface, and leaving any app or input (HDMI and others) brings you back to it in under a second without LG's home showing.
- After turning the TV off and on (standby) the new interface appears directly.
- Pressing Home **three times within two seconds** opens LG's original home as an emergency exit.

## Requirements

- An LG TV with webOS 22 or newer, and an LG account.
- A Mac or Linux computer on the **same network** (Windows via WSL is untested) with Node.js 20.19+, npm, Python 3.9+ and Git.

## Installation

### 1. Turn on Developer Mode on the TV
1. Install **Developer Mode** from the LG Content Store.
2. Open it, sign in with your LG account, turn on **Dev Mode Status** and accept the restart.
3. Open it again and turn on **Key Server**.
4. Note the **IP Address** and **Passphrase** it shows.

### 2. Install from the computer

```sh
git clone https://github.com/Xeeomr/lg-tv-islamic-launcher.git
cd lg-tv-islamic-launcher
./install.sh 192.168.1.50
```

Use your TV's IP. During installation, type the **Passphrase** when asked and accept the **pairing request** that appears on the TV. The script downloads its own tools (webOS CLI, Zig) without admin rights, builds and installs everything and starts it. Afterwards the computer can be turned off; everything runs on the TV.

### 3. (Optional) Thmanyah typeface
The interface uses the open Noto Sans Arabic font. To use the [Thmanyah](https://thmanyah.com/font) typeface, download it yourself from its site (free, but its licence does not allow redistribution, so it is not in this repository), then:

```sh
scripts/add-thmanyah.sh ~/Downloads/Thmanyah-Font-Family.zip
./install.sh 192.168.1.50
```

### 4. (Optional) More adhan recordings
Three openly licensed recordings are included. To add the Makkah or Madinah adhan or others, put the file in `launcher/audio/` if you have the right to use it and reinstall. See [launcher/audio/README.md](launcher/audio/README.md).

## Usage
- **Settings**: the crescent button at the top left. 18 sections: sections on the right, options on the left. ↑↓ to move, ← or OK to enter and change values, Back to leave. Changes save automatically.
- **Radio**: the Radio button at the top. Stations on the right; stop, sleep timer and screen off on the left.
- **Quran**: the Quran button at the top, with three sections: Radio, Audio mushaf and Live. In the mushaf: OK pauses, ◀ next ayah, ▶ previous, Back leaves while recitation continues.
- **Phone**: Settings → Phone control, then scan the QR code.
- **Apps**: long-press OK on any app; add apps from the "+" tile at the end of the list.
- **LG's original home**: press Home three times quickly.

### Private files after updates
The Thmanyah typeface and adhan recordings that may not be redistributed are never part of public releases. To keep them on your TV through automatic updates, run once:

```sh
python3 scripts/push-private.py 192.168.1.50
```

and type the code shown on the TV. The files are kept inside Home Helper and updates leave them alone.

## Important: the Developer Mode session
LG's Developer Mode is a timed session. If it expires, installed apps (including this one) can be removed. Open **Developer Mode** now and then and press **Extend Session Time**. If the interface was removed, just run `./install.sh` again.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `Failed to get ssh private key` during install | The TV is in standby or Key Server is off. Wake the TV and turn on Key Server in Developer Mode |
| `All configured authentication methods failed` | Wrong Passphrase; check it in the Developer Mode app |
| LG's home shows instead of the new one | Open the "Home Helper" app from the app list and choose "Start Helper" |
| The adhan is not audible | The TV volume is low: Settings → Sound → Raise TV volume for the adhan |
| The adhan does not return to the previous app | Settings → About → the "Diagnostics" line shows why |

## Stop LG's home from opening at power on
LG opens its own home every time the TV turns on. Turn that off once: Settings → General → System → Additional settings → Home settings → **Home Auto Launch** → Off. The TV then comes back straight to this interface.

## Uninstall and going back to LG's home
- **Temporarily**: press Home three times, or Settings → Backup and restore → Back to LG's original home.
- **Permanently**: delete the "Xee Launcher" and "Home Helper" apps from the TV's app list, or turn off Developer Mode. Nothing in the TV system itself is changed.

## Ads in LG's own home
This project does not change system settings. To turn off ads and recommendations in LG's original home:
- Settings → General → System → Additional settings → Home settings: turn off Home Promotion and Content Recommendation.
- Settings → General → About this TV → User agreements: withdraw consent for viewing information and interest-based ads.

## Known limitations
- Leaving an app can show a black screen for under a second before Home appears, a little longer if the system closed Home to free memory.
- On a cold boot (after unplugging) LG's home can show for a few seconds before Helper starts.
- The adhan and screensaver do not run while the TV is in standby.
- Weather alone needs the internet; offline it shows the last update time.

## Publishing an update (developers)
`scripts/publish-update.sh` builds clean public packages (no pairing key or private file, and it checks), signs the update manifest with your private key, and publishes a GitHub release that TVs install by themselves. The private key stays in `~/.config/xee-launcher/`, outside the repository; the public key is in `native/app/updater.js`. If you fork the project, generate your own key and put your public key there.

## Sources and licences
- Code: MIT, based on Clean Your TV (Gathin, OmkarK97, Razdva122). See [LICENSE](LICENSE).
- Quran text: [Tanzil Project](https://tanzil.net) (CC BY 3.0, copied verbatim). See [launcher/quran/LICENSE-TANZIL.txt](launcher/quran/LICENSE-TANZIL.txt).
- Hadith: [hadith-api](https://github.com/fawazahmed0/hadith-api) (Unlicense).
- Cities: [GeoNames](https://www.geonames.org) (CC BY 4.0) with Arabic names from Wikidata (CC0).
- Fonts: Amiri Quran and Noto Sans Arabic (SIL OFL 1.1).
- Wallpapers: Wikimedia Commons; each photographer and licence is in [launcher/wallpapers/CREDITS.txt](launcher/wallpapers/CREDITS.txt) and on screen.
- Weather: [Open-Meteo](https://open-meteo.com).
- Radio and recitations: streamed live from their sources (radiojar.com, mp3quran.net and everyayah.com), and the live broadcasts from the Saudi Quran and Sunnah channels; no audio is stored in this repository.
- QR codes: [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator) (MIT).
