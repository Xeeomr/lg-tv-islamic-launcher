# Initial issue status audit

Reviewed on 2026-10-25 using all 14 existing issues, their comments and timeline
references, related PR descriptions/discussions/reviews, and public releases.
This is a historical snapshot; current GitHub labels are authoritative.
At review time PR #35 had merged, but v1.1.0 was not publicly released;
v1.0.3 remained the latest published release.

All reports describe failures and receive `bug`. The table records the additional
status or disposition. Issue links use this repository's GitHub issue numbers.

| Issue | Status / disposition | Evidence and next step |
| --- | --- | --- |
| [#55](https://github.com/Razdva122/clean-your-tv-lg-webos/issues/55) | `status:planned` | Detailed Root finalize, migration and interrupted-cleanup report; no linked fix or outstanding reporter request. Queue investigation of service exit diagnostics and setup recovery. |
| [#54](https://github.com/Razdva122/clean-your-tv-lg-webos/issues/54) | `status:awaiting-release` | PR #52 addresses both reported Node 8.12 WebSocket startup blockers and is included in #35. Public release and original C1 acceptance remain pending. |
| [#51](https://github.com/Razdva122/clean-your-tv-lg-webos/issues/51) | `status:planned` | Reproducible Helper installation rejection with a failed-operation diagnostic; no linked fix or outstanding reporter request. Queue diagnosis of the underlying TV service rejection; do not infer a duplicate. |
| [#47](https://github.com/Razdva122/clean-your-tv-lg-webos/issues/47) | `status:awaiting-release` | PR #52 addresses Node 0.12 startup/polyfills and WebSocket compatibility, included in #35. Public release and original 49UJ750V acceptance remain pending. |
| [#41](https://github.com/Razdva122/clean-your-tv-lg-webos/issues/41) | `status:needs-info` | Latest maintainer reply requests Developer Mode state and the read-only appInstallService status response. No reporter answer yet; no confirmed fix. |
| [#37](https://github.com/Razdva122/clean-your-tv-lg-webos/issues/37) | `status:awaiting-release` | Reporter identified missing TV Python 3 and corrected the model to UK6540PTD. PR #38 adds diagnostics; #43 supplies optional Python and is included in #35. Publication and actual UK6540PTD acceptance remain pending. |
| [#24](https://github.com/Razdva122/clean-your-tv-lg-webos/issues/24) | `status:needs-info` | Original unfinished removal remains unresolved; the follow-up #41 is waiting for a TV response. PR #42 fixes a separate Android comment only, so it cannot move the whole issue to awaiting-release. |
| [#23](https://github.com/Razdva122/clean-your-tv-lg-webos/issues/23) | `duplicate` (closed) | Existing maintainer reply explicitly identifies #24 as canonical. Preserve closure; no delivery status because the original removal failure remains unresolved. |
| [#22](https://github.com/Razdva122/clean-your-tv-lg-webos/issues/22) | `status:needs-info` | v1.0.3 provides safer Key Server diagnostics, not a confirmed cause/fix. Latest reply requests a fresh report and TV versions. |
| [#21](https://github.com/Razdva122/clean-your-tv-lg-webos/issues/21) | `status:needs-info` | Latest reply requests installed versions and a fresh result/report after v1.0.3. PR #33 improves stale-PID handling and visibility; original Helper/tile symptoms are unconfirmed. |
| [#20](https://github.com/Razdva122/clean-your-tv-lg-webos/issues/20) | `status:released` (closed) | v1.0.1 publishes the rendering correction; the reporter confirms Home 1.3.7 displays icons and launches apps on the original 49UJ750V. |
| [#15](https://github.com/Razdva122/clean-your-tv-lg-webos/issues/15) | `status:needs-info` | Reporter confirmed the SSH fix, then hit a separate ARM32 check. v0.10.8 corrected userspace detection; latest reply requests a retest, with no subsequent result. |
| [#12](https://github.com/Razdva122/clean-your-tv-lg-webos/issues/12) | `status:needs-info` | Later process snapshots show the controller alive. PRs #13/#31 improve packaging and diagnostics, not a confirmed C5 fix. Latest reply requests the guided report and observed foreground app after v1.0.3. |
| [#10](https://github.com/Razdva122/clean-your-tv-lg-webos/issues/10) | `status:needs-info` | Startup/standby corrections shipped; #11 and the latest maintainer reply explicitly leave the issue open for QNED80T confirmation across standby/resume. |

No issue is left in active analysis or implementation after this metadata task.
Future agent work must update these labels as described in `AGENTS.md`.
