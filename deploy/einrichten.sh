#!/bin/sh
# Variante ohne Container: Digest ueber ein vorhandenes nginx ausliefern.
# Einmalig mit sudo ausfuehren. Anpassbar per Umgebung:
#   WEB_DIR    Zielordner im Webroot          (Standard /var/www/html/checkmates)
#   WEB_OWNER  Nutzer, der den Job ausfuehrt  (Standard: Aufrufer von sudo)
#   SITES      nginx-Site-Dateien, Leerzeichen-getrennt (Standard: default)
# Die Location nutzt /etc/nginx/.htpasswd fuer den Login.
set -e
WEB_DIR=${WEB_DIR:-/var/www/html/checkmates}
WEB_OWNER=${WEB_OWNER:-${SUDO_USER:-$(id -un)}}
SITES=${SITES:-/etc/nginx/sites-available/default}

install -d -o "$WEB_OWNER" -g "$WEB_OWNER" "$WEB_DIR"
cp "$(dirname "$0")/nginx-checkmates.conf" /etc/nginx/snippets/checkmates.conf
for site in $SITES; do
  grep -q "^[^#]*include snippets/checkmates.conf" "$site" && continue
  cp "$site" "$site.bak-$(date +%Y%m%d-%H%M%S)"
  python3 - "$site" <<'PY'
import re, sys
p = sys.argv[1]; s = open(p).read()
# vor der ersten nicht auskommentierten "location / {", sonst vor dem letzten
# nicht auskommentierten "}" der Datei
m = re.search(r"^([ \t]*)location / \{", s, re.M)
if m:
    i = m.start()
    s = s[:i] + m[1] + "include snippets/checkmates.conf;\n\n" + s[i:]
else:
    zeilen = s.splitlines(keepends=True)
    j = max(k for k, z in enumerate(zeilen) if z.strip() == "}")
    zeilen.insert(j, "\tinclude snippets/checkmates.conf;\n")
    s = "".join(zeilen)
open(p, "w").write(s)
PY
done
nginx -t
systemctl reload nginx
echo "fertig: $WEB_DIR - danach CMK_WEB_DIR=$WEB_DIR in .env setzen"
