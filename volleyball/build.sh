#!/bin/sh
# 由 scorer.html（線上 Artifact 用的版本）產生可獨立開啟、可安裝成 App 的 index.html
cd "$(dirname "$0")"
{
  cat <<'HEAD'
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#1B2638">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="排球">
<link rel="manifest" href="manifest.webmanifest?v=2">
<link rel="icon" href="icons/icon-192.png?v=2" type="image/png">
<link rel="apple-touch-icon" href="icons/icon-180.png?v=2">
<style>:root { padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); } body { margin: 0; }</style>
</head>
<body>
HEAD
  cat scorer.html
  cat <<'TAIL'
<script>
if ('serviceWorker' in navigator && location.protocol !== 'file:') {
  window.addEventListener('load', () => { navigator.serviceWorker.register('sw.js').catch(() => {}); });
}
</script>
</body>
</html>
TAIL
} > index.html
