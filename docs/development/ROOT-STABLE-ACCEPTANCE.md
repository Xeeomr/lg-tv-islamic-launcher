# Fixed-build stable acceptance

Target: OLED55C3RLA / 43.21.71, 2026-10-23.
Bundle manifest SHA-256: `cb2495c1e218f1916d89b5fdb11e78f28123068b66ef30481d3b4766010225a2`.
Installed identity matches the reproducible local integration build.

- Full local suite passed, including 367 Root tests.
- Active after normal software reboot for over 30 minutes; system Home and guardian verified.
- Private backup and ordinary launcher/helper static hashes captured outside Git.
- Settings exit: user confirmed LG Home and controls; all three routes restored and intent disabled.
- Triple Home from active mode: user confirmed first attempt without zoom; recovery reason `escape`, all routes restored and intent disabled.
- Frozen-renderer test is **not accepted**: user needed a second attempt. Independent resumer recorded timeout at 45 seconds with route still pending; final recovery succeeded later. No event trace proves why the first gesture was missed. Investigate with passive recording before changing gesture policy.

This was the initial open-gate list. Subsequent results below close specific checks; do not treat the initial list as the final status.

## Subsequent checks on the same artifact

- Passive all-channel capture recognized both Home triples (about 0.83 and 0.90 s). No gesture policy was changed.
- Repeated frozen-renderer test passed on the first attempt. Resumer recorded `restored` at uptime 2480.26 while renderer remained `T (stopped)`, before the resumption timeout; all Home destinations and disabled intent verified. The earlier untraced second-attempt report remains recorded above rather than explained away.
- User confirmed quick 2–3 second standby/resume, arrows/OK, held arrow, volume, pointer/wheel and short Home.
- Genuine Homebrew failsafe skipped the owned normal-boot hook. Recovery restored all three Home routes; boot gate returned false at uptime 63.66 and disabled intent. A second authorized reboot returned normal access without silently re-enabling Root.
- Normal uninstall completed and removed the candidate and owned hook. State was archived, then the identical bundle clean-installed with profile migration; installation left Home unchanged. Static hashes of production launcher/helper matched exactly before/after. Permanent candidate reactivation passed fresh health checks.

- User confirmed all five apps after reinstall, in-app Back, exit Cancel and confirmed exit in Kinopoisk; second application VK Video also returned correctly.
- Stalling only the verified emergency observer triggered independent restoration in 2.414 seconds. All routes returned to LG, intent disabled, recovery integrity intact.
- Root mode was explicitly re-enabled after the fault test with fresh health and the candidate opened. The user deferred cold-power testing; no power disconnection was performed.

## Remaining acceptance

Cold-power startup is pending by user choice. The one second-attempt gesture report remains unexplained; subsequent captured triples and the instrumented frozen-renderer repeat passed without a policy change. Preserve this observation and investigate if repeated. Do not advertise universal compatibility or a completed cold-power matrix.

No runtime changes were needed in this session. Only evidence and acceptance planning were updated.
