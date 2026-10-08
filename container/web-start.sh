#!/bin/sh
# Erzeugt die Login-Liste aus WEB_USERS ("name:passwort,name2:passwort2") und startet Caddy.
set -e
if [ -z "$WEB_USERS" ]; then
  echo "WEB_USERS ist leer - ohne Login wird nichts ausgeliefert." >&2
  exit 1
fi
: > /tmp/users.caddy
echo "$WEB_USERS" | tr ',' '\n' | while IFS=: read -r name passwort; do
  [ -n "$name" ] && [ -n "$passwort" ] || continue
  echo "$name $(caddy hash-password --plaintext "$passwort")" >> /tmp/users.caddy
done
echo "$(wc -l < /tmp/users.caddy) Login(s) eingerichtet."
exec caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
