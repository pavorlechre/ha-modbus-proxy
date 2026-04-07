import asyncio
import json
import logging
import os
import sys

# --- Konfigurace z HA add-on options ---
OPTIONS_FILE = "/data/options.json"

def load_options():
    try:
        with open(OPTIONS_FILE) as f:
            return json.load(f)
    except Exception:
        return {}

options = load_options()

TARGET_HOST = options.get("target_host", "192.168.1.100")
TARGET_PORT = int(options.get("target_port", 502))
LISTEN_PORT = int(options.get("listen_port", 5020))
LOG_LEVEL   = options.get("log_level", "info").upper()

# --- Logging ---
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("modbus_proxy")

# Semafor – pouze jeden přístup k Acondu najednou
_lock = asyncio.Lock()

async def pipe(reader, writer, label):
    """Přeposílá data ze čtecího streamu do zapisovacího."""
    try:
        while True:
            data = await reader.read(4096)
            if not data:
                break
            log.debug("%s %d bajtů", label, len(data))
            writer.write(data)
            await writer.drain()
    except (ConnectionResetError, asyncio.IncompleteReadError, BrokenPipeError):
        pass
    except Exception as e:
        log.warning("%s chyba: %s", label, e)

async def handle_client(client_r, client_w):
    """Obsluha jednoho připojeného klienta."""
    peer = client_w.get_extra_info("peername", ("?", 0))
    log.info("Nové připojení od %s:%s", peer[0], peer[1])

    async with _lock:
        try:
            target_r, target_w = await asyncio.wait_for(
                asyncio.open_connection(TARGET_HOST, TARGET_PORT),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            log.error("Timeout při připojení na %s:%s", TARGET_HOST, TARGET_PORT)
            client_w.close()
            return
        except OSError as e:
            log.error("Nelze se připojit na %s:%s – %s", TARGET_HOST, TARGET_PORT, e)
            client_w.close()
            return

        log.debug("Spojeno s Acondem %s:%s", TARGET_HOST, TARGET_PORT)

        try:
            await asyncio.gather(
                pipe(client_r, target_w, "klient→Acond"),
                pipe(target_r, client_w, "Acond→klient"),
            )
        finally:
            target_w.close()
            try:
                await target_w.wait_closed()
            except Exception:
                pass

    client_w.close()
    log.info("Spojení od %s:%s ukončeno", peer[0], peer[1])

async def main():
    log.info("=== Modbus Proxy start ===")
    log.info("Poslouchám na portu %s", LISTEN_PORT)
    log.info("Cíl: %s:%s", TARGET_HOST, TARGET_PORT)

    server = await asyncio.start_server(
        handle_client,
        "0.0.0.0",
        LISTEN_PORT,
    )

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Proxy zastavena.")
