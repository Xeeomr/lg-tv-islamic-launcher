**English** · [العربية](README.md)

# Arabic Islamic Home for LG TVs

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
- Days left until Ramadan (an estimate until the official announcement); it turns into "Ramadan Mubarak" during the month.
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
- A screensaver after the idle time you choose: slowly moving photo, clock, Hijri date, a verse and the next prayer; the text drifts slightly to protect the panel.
- 20 high-quality Islamic wallpapers under open licences, grouped for Fajr, day, Maghrib and night, changing with the prayer times, with photographer credits, an adjustable dark overlay and a live-preview picker.

**Speed and stability**
- Home opens the new interface, and leaving any app brings you back to it.
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
- **Apps**: long-press OK on any app; add apps from the "+" tile at the end of the list.
- **LG's original home**: press Home three times quickly.

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

## Uninstall and going back to LG's home
- **Temporarily**: press Home three times, or Settings → Backup and restore → Back to LG's original home.
- **Permanently**: delete the "Home" and "Home Helper" apps from the TV's app list, or turn off Developer Mode. Nothing in the TV system itself is changed.

## Ads in LG's own home
This project does not change system settings. To turn off ads and recommendations in LG's original home:
- Settings → General → System → Additional settings → Home settings: turn off Home Promotion and Content Recommendation.
- Settings → General → About this TV → User agreements: withdraw consent for viewing information and interest-based ads.

## Known limitations
- LG's home can flash for under a second when leaving some apps. Removing it completely is not possible without root.
- On a cold boot (after unplugging) LG's home can show for a few seconds before Helper starts.
- The adhan and screensaver do not run while the TV is in standby.
- Weather alone needs the internet; offline it shows the last update time.

## Sources and licences
- Code: MIT, based on Clean Your TV (Gathin, OmkarK97, Razdva122). See [LICENSE](LICENSE).
- Quran text: [Tanzil Project](https://tanzil.net) (CC BY 3.0, copied verbatim). See [launcher/quran/LICENSE-TANZIL.txt](launcher/quran/LICENSE-TANZIL.txt).
- Hadith: [hadith-api](https://github.com/fawazahmed0/hadith-api) (Unlicense).
- Cities: [GeoNames](https://www.geonames.org) (CC BY 4.0) with Arabic names from Wikidata (CC0).
- Fonts: Amiri Quran and Noto Sans Arabic (SIL OFL 1.1).
- Wallpapers: Wikimedia Commons; each photographer and licence is in [launcher/wallpapers/CREDITS.txt](launcher/wallpapers/CREDITS.txt) and on screen.
- Weather: [Open-Meteo](https://open-meteo.com).
