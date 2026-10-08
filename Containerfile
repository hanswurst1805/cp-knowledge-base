FROM docker.io/library/python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    TZ=Europe/Berlin \
    CMK_DATEN_DIR=/daten \
    CMK_WEB_DIR=/web \
    CMK_UHRZEIT=07:00

WORKDIR /app
COPY checkmates.py digest.py config.toml ./

# Laeuft als unprivilegierter Nutzer; UID/GID beim Start per --user / compose anpassbar
RUN useradd --uid 1000 --create-home cmk && mkdir -p /daten /web && chown cmk:cmk /daten /web
USER cmk
VOLUME ["/daten", "/web"]

CMD ["python3", "checkmates.py", "dienst"]
