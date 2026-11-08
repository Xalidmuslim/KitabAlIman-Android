#!/usr/bin/env bash
set -euo pipefail

mkdir -p qa
PACKAGE="com.xalid.kitabaliman.preview30"
ACTIVITY="com.xalid.meditsinaproroka.nativeapp.MainActivity"

adb install -r qa/bin/app-release.apk
adb shell wm size 432x768
adb shell wm density 160
adb shell settings put system font_scale 1.0
adb shell pm path "$PACKAGE" | tee qa/package_path.txt
adb logcat -c
adb shell am force-stop "$PACKAGE" || true
adb shell am start -W -n "$PACKAGE/$ACTIVITY" | tee qa/activity_launch.txt
sleep 12

if ! adb shell pidof "$PACKAGE" >/dev/null; then
  echo "Explicit activity did not stay alive. Trying installed LAUNCHER intent."
  adb shell monkey -p "$PACKAGE" -c android.intent.category.LAUNCHER 1 | tee qa/launcher_retry.txt
  sleep 10
fi

adb shell dumpsys activity activities > qa/activity_state.txt
adb logcat -d -v threadtime > qa/app_logcat.txt
adb shell pidof "$PACKAGE" | tee qa/app_pid.txt || true
adb shell screencap -p /sdcard/iman_v30_home.png
adb pull /sdcard/iman_v30_home.png qa/iman_v30_home.png

test -s qa/iman_v30_home.png
if ! test -s qa/app_pid.txt; then
  echo "Error: v30 did not start / crashed. See app_logcat.txt and activity_state.txt." >&2
  exit 3
fi
if ! grep -q "$PACKAGE" qa/activity_state.txt; then
  echo "Error: v30 package is not resumed on screen." >&2
  exit 4
fi
echo "Screenshot from live app process: $(cat qa/app_pid.txt)"
