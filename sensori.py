# Meditimer, i sensori: potenza, temperatura e frequenze del processore lette da HWiNFO.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 11/09/2026: nasce con la revisione 1, dallo script misura_carico.py scritto
# per la messa a punto del BIOS. Funziona solo su Windows e solo se HWiNFO e'
# in esecuzione in modalita' Sensors-only con Shared Memory Support attivo:
# in ogni altro caso il banco di prova ne fa a meno senza dirlo due volte.

"""I sensori di HWiNFO per il banco di prova.

HWiNFO, quando ha la memoria condivisa attiva, pubblica le sue letture in
una mappa di memoria con nome. Qui la si legge con la libreria standard,
senza dipendenze, e se ne estraggono le poche voci che dicono come sta
lavorando il processore: la potenza del pacchetto, le temperature, i clock
medi dei core prestazionali e di quelli efficienti, e i limiti scattati.
Il campionatore legge a intervalli mentre girano le prove del processore e
alla fine ne fa una sintesi, cosi' il report puo' dire a che potenza e a
che temperatura e' stato ottenuto il risultato: e' cio' che distingue un
processore frenato dal calore da uno frenato dal profilo di potenza.
"""

import mmap
import re
import struct
import threading
import time

NOME_MAPPA = "Global\\HWiNFO_SENS_SM2"
TIPI = {0: "nessuno", 1: "temp", 2: "volt", 3: "ventola", 4: "corrente", 5: "potenza", 6: "clock", 7: "uso", 8: "altro"}
INTERVALLO = 2.0
RE_PCORE = re.compile(r"^(P-core|Core) \d+ Clock", re.IGNORECASE)
RE_ECORE = re.compile(r"^E-core \d+ Clock", re.IGNORECASE)
RE_LIMITI = re.compile(r"Throttling|Limit Exceeded|EDP Limit")


def _stringa(buf, inizio, lunghezza):
    return buf[inizio : inizio + lunghezza].split(b"\0")[0].decode("mbcs", "replace")


def letture():
    """Tutte le letture di HWiNFO come lista di dizionari, oppure None se non e' raggiungibile."""
    try:
        m = mmap.mmap(-1, 44, tagname=NOME_MAPPA, access=mmap.ACCESS_READ)
    except (OSError, ValueError, TypeError):
        return None
    try:
        testa = m.read(44)
    finally:
        m.close()
    firma, _ver, _rev, _poll, off_s, sz_s, n_s, off_r, sz_r, n_r = struct.unpack("<4sIIqIIIIII", testa)
    if firma != b"HWiS" or n_r == 0:
        return None
    totale = off_r + sz_r * n_r
    try:
        m = mmap.mmap(-1, totale, tagname=NOME_MAPPA, access=mmap.ACCESS_READ)
    except (OSError, ValueError, TypeError):
        return None
    try:
        buf = m.read(totale)
    finally:
        m.close()
    sensori = [_stringa(buf, off_s + i * sz_s + 8, 128) for i in range(n_s)]
    voci = []
    for i in range(n_r):
        b = off_r + i * sz_r
        tipo, idx, _rid = struct.unpack_from("<III", buf, b)
        valore, vmin, vmax, vmedia = struct.unpack_from("<dddd", buf, b + 284)
        voci.append(
            {
                "tipo": TIPI.get(tipo, str(tipo)),
                "sensore": sensori[idx] if idx < len(sensori) else "?",
                "nome": _stringa(buf, b + 12, 128),
                "unita": _stringa(buf, b + 268, 16),
                "valore": valore,
                "min": vmin,
                "max": vmax,
                "media": vmedia,
            }
        )
    return voci


def riassunto(voci):
    """Le poche letture che interessano, da una lista completa."""
    r = {"potenza": None, "temp_pkg": None, "temp_core_max": None, "p_clock": None, "e_clock": None, "limiti": []}
    p_clk, e_clk = [], []
    for x in voci:
        nome, tipo, v = x["nome"], x["tipo"], x["valore"]
        if tipo == "potenza" and nome == "CPU Package Power":
            r["potenza"] = v
        elif tipo == "temp" and nome == "CPU Package":
            r["temp_pkg"] = v
        elif tipo == "temp" and nome == "Core Max":
            r["temp_core_max"] = v
        elif tipo == "clock" and RE_ECORE.match(nome):
            e_clk.append(v)
        elif tipo == "clock" and RE_PCORE.match(nome):
            p_clk.append(v)
        elif tipo == "altro" and v >= 1.0 and RE_LIMITI.search(nome):
            r["limiti"].append(nome)
    if p_clk:
        r["p_clock"] = sum(p_clk) / len(p_clk)
    if e_clk:
        r["e_clock"] = sum(e_clk) / len(e_clk)
    return r


def disponibile():
    """Vero se HWiNFO risponde adesso."""
    return letture() is not None


def _media(campioni, chiave):
    valori = [c[chiave] for c in campioni if c.get(chiave) is not None]
    return sum(valori) / len(valori) if valori else None


def _massimo(campioni, chiave):
    valori = [c[chiave] for c in campioni if c.get(chiave) is not None]
    return max(valori) if valori else None


def sintesi(campioni):
    """Medie e massimi di una serie di riassunti, oppure None se non ce ne sono."""
    if not campioni:
        return None
    limiti = sorted({lim for c in campioni for lim in c.get("limiti", [])})
    return {
        "campioni": len(campioni),
        "potenza_media_w": _media(campioni, "potenza"),
        "potenza_max_w": _massimo(campioni, "potenza"),
        "temp_pkg_max": _massimo(campioni, "temp_pkg"),
        "temp_core_max": _massimo(campioni, "temp_core_max"),
        "p_clock_medio_mhz": _media(campioni, "p_clock"),
        "e_clock_medio_mhz": _media(campioni, "e_clock"),
        "limiti": limiti,
    }


class Campionatore:
    """Legge i sensori a intervalli in un thread, finche' non lo si ferma."""

    def __init__(self, intervallo=INTERVALLO):
        self._intervallo = intervallo
        self._fermati = threading.Event()
        self._campioni = []
        self._thread = None

    def avvia(self):
        self._thread = threading.Thread(target=self._corri, daemon=True)
        self._thread.start()

    def _corri(self):
        while not self._fermati.is_set():
            voci = letture()
            if voci:
                self._campioni.append(riassunto(voci))
            self._fermati.wait(self._intervallo)

    def ferma(self):
        """Ferma il thread e restituisce la sintesi dei campioni raccolti, oppure None."""
        self._fermati.set()
        if self._thread is not None:
            self._thread.join(timeout=self._intervallo + 1.0)
        return sintesi(self._campioni)


if __name__ == "__main__":
    voci = letture()
    if voci is None:
        print("HWiNFO non raggiungibile: deve girare in Sensors-only con Shared Memory Support attivo.")
    else:
        for chiave, valore in riassunto(voci).items():
            print(f"{chiave}: {valore}")
        time.sleep(0)
