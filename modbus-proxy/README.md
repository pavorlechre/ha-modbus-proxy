# Modbus Proxy – HA Add-on

Jednoduchý Modbus TCP proxy který umožňuje více klientům
přistupovat k jednomu Modbus zařízení (např. tepelné čerpadlo Acond).

Požadavky jsou serializovány – zařízení vidí vždy jen jednoho mastera.

## Instalace

1. V HA otevři **File editor** (nebo Samba share)
2. Zkopíruj složku `modbus_proxy` do `/addons/`
3. **Nastavení → Doplňky → ⋮ → Znovu načíst doplňky**
4. Nový add-on se objeví v **Lokální doplňky** → Instalovat

## Konfigurace

Po instalaci nastav v záložce **Konfigurace**:

| Parametr | Popis | Výchozí |
|---|---|---|
| `target_host` | IP adresa Acondu | `192.168.1.100` |
| `target_port` | Modbus port Acondu | `502` |
| `listen_port` | Port na kterém proxy poslouchá | `5020` |
| `log_level` | Úroveň logování | `info` |

## Použití

Po spuštění add-onu přesměruj YAML modbus na proxy:

```yaml
modbus:
  - name: acond
    type: tcp
    host: localhost   # nebo IP adresa HA
    port: 5020        # proxy port
```

Integrace Acond míří přímo na zařízení (IP:502).
Proxy se postará o serializaci přístupů.

## Jak to funguje

```
YAML modbus      ──┐
                   ├──► proxy :5020 ──► Acond :502
Acond integrace  ──┘      (semafor)
```

Semafor zajistí že v jeden okamžik komunikuje s Acondem
vždy jen jeden klient.
