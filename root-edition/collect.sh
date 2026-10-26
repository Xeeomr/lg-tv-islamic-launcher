#!/bin/sh
# Read-only: stdout only. Never source device files or execute their contents.
printf 'uid=%s\n' "$(id -u)"
printf 'kernel_arch=%s\n' "$(uname -m)"
printf 'kernel_release=%s\n' "$(uname -r)"
printf 'userspace_bits=%s\n' "$(getconf LONG_BIT 2>/dev/null)"
for source in /etc/starfish-release /etc/webos-release; do
    if [ -r "$source" ]; then
        sed -n 's/^WEBOS_RELEASE_VERSION=/webos_release=/p; s/^WEBOS_BUILD_ID=/webos_build=/p; s/^STARFISH_RELEASE_VERSION=/starfish_release=/p; s/^STARFISH_BUILD_ID=/starfish_build=/p' "$source"
    fi
done
if [ -r /proc/self/status ]; then
    sed -n 's/^CapEff:[[:space:]]*/effective_capabilities=/p; s/^NoNewPrivs:[[:space:]]*/no_new_privileges=/p' /proc/self/status
fi
printf 'mount_namespace=%s\n' "$(readlink /proc/self/ns/mnt 2>/dev/null)"
for tool in luna-send systemctl; do
    if command -v "$tool" >/dev/null 2>&1; then printf '%s_present=yes\n' "$tool"; else printf '%s_present=no\n' "$tool"; fi
done
