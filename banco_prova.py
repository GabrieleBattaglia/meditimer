# Meditimer, il banco di prova: processore, memoria, disco e la scheda della macchina.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 11/09/2026: revisione 1. Alle tre prove del processore su tutti i core si
# aggiungono le stesse su un core solo, la copia in memoria, il disco e la
# scheda della macchina; ogni processo misura da se' la propria durata, cosi'
# l'avvio del pool non diluisce piu' la prima fase; i risultati per processo
# si riassumono in minimo, massimo, media, dispersione e fuori norma.

"""Il banco di prova di Meditimer.

Misura quanto e' veloce la macchina su cui gira, in quattro reparti.
Il processore, con tre prove, interi, decimali e funzioni matematiche, fatte
prima su tutti i processori logici insieme e poi su uno solo: il rapporto
fra le due dice quanto la macchina guadagna dal parallelismo. I corpi dei
cicli sono quelli della 2.9.1, cosi' i numeri restano confrontabili con le
prove gia' in archivio: misurano l'interprete Python quanto il processore,
ed e' per questo che ogni prova porta scritta la versione di Python.
La memoria, copiando blocchi molto piu' grandi della cache del processore,
su un core e su tutti: e' la misura che vede la differenza fra due
frequenze della RAM.
Il disco, scrivendo un file temporaneo accanto al programma con la
sincronizzazione forzata e rileggendolo, su Windows senza la cache del
sistema, cosi' che sia davvero il disco a essere misurato.
La scheda della macchina, processore, core, memoria, sistema e
alimentazione, viaggia con ogni prova.
Il modulo non stampa e non suona: riceve le funzioni con cui annunciare e
segnalare, e restituisce righe gia' pronte per lo screen reader.
"""

import contextlib
import math
import multiprocessing
import os
import platform
import socket
import sys
import time
from datetime import datetime

from formati import data_italiana, formatta_numero_grande, numero_it, ora_breve, riga_blocchi

try:
    import psutil
except ImportError:
    psutil = None

try:
    import sensori
except ImportError:
    sensori = None

MB = 1024 * 1024
PROFILI = {
    "breve": {"cpu_multi": 5.0, "cpu_singolo": 3.0, "memoria": 3.0, "disco_mb": 128},
    "normale": {"cpu_multi": 10.0, "cpu_singolo": 5.0, "memoria": 5.0, "disco_mb": 256},
    "lunga": {"cpu_multi": 20.0, "cpu_singolo": 10.0, "memoria": 10.0, "disco_mb": 512},
}
PROVE_CPU = (("int", "calcoli su interi"), ("float", "calcoli su decimali"), ("math", "funzioni matematiche"))
# Le teste delle righe a blocchi devono stare sotto i quaranta caratteri.
NOMI_BREVI = {"int": "Interi", "float": "Decimali", "math": "Matematiche"}
MEMORIA_SINGOLO_MB = 128
MEMORIA_MULTI_MB = 32
MEMORIA_MULTI_MINIMO_MB = 8
MEMORIA_QUOTA_DISPONIBILE = 0.25
BLOCCO_DISCO = 4 * MB
NOME_FILE_DISCO = "banco_prova_disco.tmp"
# Un processo che si scosta dalla mediana degli altri piu' di tanto e' fuori norma.
# La soglia e' larga apposta: su un processore ibrido i core efficienti stanno
# sotto quelli prestazionali di un dieci per cento sistematico, e quella non e'
# un'anomalia ma una caratteristica, che la dispersione racconta gia'.
SOGLIA_FUORI_NORMA = 20.0
# Oltre questo numero i fuori norma si riassumono invece di essere elencati.
FUORI_NORMA_ELENCATI = 5
SECONDI_DISCO_STIMATI = 10.0


def lavoro_cpu(durata, tipo):
    """Un processo del banco: conta le operazioni fatte in durata secondi.

    Restituisce la coppia (operazioni, secondi davvero impiegati): il tempo
    lo misura ognuno per conto suo, cosi' l'avvio del pool e la coda della
    fase non entrano nel rapporto. I corpi dei cicli sono quelli della
    2.9.1 e non vanno toccati, altrimenti i risultati nuovi non sarebbero
    piu' confrontabili con quelli gia' in archivio: l'assegnazione a una
    variabile che nessuno legge e' il lavoro che si sta misurando.
    """
    operazioni = 0
    inizio = time.perf_counter()
    if tipo == "int":
        while (time.perf_counter() - inizio) < durata:
            for i in range(1000):
                _risultato = (i * i * 2 + 15) // 3
            operazioni += 1000
    elif tipo == "float":
        while (time.perf_counter() - inizio) < durata:
            for i in range(1000):
                _risultato = (float(i) * 3.14159) / 2.71828
            operazioni += 1000
    elif tipo == "math":
        while (time.perf_counter() - inizio) < durata:
            for i in range(1, 1001):
                _risultato = math.sqrt(i) + math.sin(i / 100.0)
            operazioni += 1000
    else:
        raise ValueError(f"prova sconosciuta: {tipo}")
    return operazioni, time.perf_counter() - inizio


def lavoro_memoria(durata, megabyte):
    """Copia un blocco di memoria su un altro, di continuo, per durata secondi.

    Restituisce (byte copiati, secondi). I due blocchi devono essere molto
    piu' grandi della cache del processore, altrimenti si misura quella e
    non la memoria. Le pagine vengono toccate prima di partire, perche' il
    sistema le assegna davvero solo alla prima scrittura.
    """
    n = max(1, int(megabyte)) * MB
    origine = bytearray(n)
    destinazione = bytearray(n)
    for i in range(0, n, 4096):
        origine[i] = 1
    destinazione[:] = origine
    copie = 0
    inizio = time.perf_counter()
    while (time.perf_counter() - inizio) < durata:
        destinazione[:] = origine
        copie += 1
    return copie * n, time.perf_counter() - inizio


def _leggi_con_cache(percorso):
    letti = 0
    inizio = time.perf_counter()
    with open(percorso, "rb", buffering=0) as f:
        while True:
            blocco = f.read(BLOCCO_DISCO)
            if not blocco:
                break
            letti += len(blocco)
    return letti, time.perf_counter() - inizio


def _leggi_senza_cache_windows(percorso):
    """Legge il file scavalcando la cache di Windows, con la libreria di sistema.

    Serve il flag di apertura senza buffer, che open di Python non espone:
    si passa da CreateFileW e ReadFile con ctypes. Con quel flag il buffer
    deve essere allineato al settore, quindi se ne alloca uno piu' grande
    e si usa il primo indirizzo multiplo di 4096.
    """
    import ctypes
    from ctypes import wintypes

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    k32.CreateFileW.restype = wintypes.HANDLE
    k32.ReadFile.argtypes = [wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID]
    k32.ReadFile.restype = wintypes.BOOL
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    k32.CloseHandle.restype = wintypes.BOOL
    generic_read = 0x80000000
    file_share_read = 0x00000001
    open_existing = 3
    flags = 0x20000000 | 0x08000000  # FILE_FLAG_NO_BUFFERING | FILE_FLAG_SEQUENTIAL_SCAN
    non_valido = wintypes.HANDLE(-1).value
    handle = k32.CreateFileW(percorso, generic_read, file_share_read, None, open_existing, flags, None)
    if handle is None or handle == non_valido:
        raise OSError(ctypes.get_last_error(), "apertura senza cache non riuscita")
    try:
        grezzo = ctypes.create_string_buffer(BLOCCO_DISCO + 4096)
        indirizzo = (ctypes.addressof(grezzo) + 4095) & ~4095
        letti = wintypes.DWORD(0)
        totale = 0
        inizio = time.perf_counter()
        while True:
            if not k32.ReadFile(handle, indirizzo, BLOCCO_DISCO, ctypes.byref(letti), None):
                raise OSError(ctypes.get_last_error(), "lettura senza cache non riuscita")
            if letti.value == 0:
                break
            totale += letti.value
        return totale, time.perf_counter() - inizio
    finally:
        k32.CloseHandle(handle)


def _leggi(percorso):
    """La rilettura del file: senza cache dove si puo', altrimenti normale. Restituisce (byte, secondi, senza_cache)."""
    if os.name == "nt":
        try:
            letti, secondi = _leggi_senza_cache_windows(percorso)
        except OSError:
            pass
        else:
            return letti, secondi, True
    letti, secondi = _leggi_con_cache(percorso)
    return letti, secondi, False


def misura_disco(cartella, megabyte, passate=2):
    """Scrive e rilegge un file temporaneo nella cartella. Solleva OSError se il disco non collabora.

    La scrittura comprende la sincronizzazione su disco, altrimenti si
    misurerebbe la cache di scrittura del sistema. La rilettura, su
    Windows, scavalca la cache: se non ci riesce legge normalmente e lo
    dichiara nel risultato, perche' un numero preso dalla cache non e' una
    misura del disco. Si fanno due passate e si tiene la migliore di
    ciascuna: sui dischi a stato solido la scrittura oscilla con lo stato
    della loro cache interna, misurato qui fra 400 e 1.600 megabyte al
    secondo sullo stesso disco a pochi minuti di distanza.
    """
    percorso = os.path.join(cartella, NOME_FILE_DISCO)
    blocco = os.urandom(BLOCCO_DISCO)
    n_blocchi = max(1, int(megabyte) * MB // BLOCCO_DISCO)
    byte = n_blocchi * BLOCCO_DISCO
    scrittura = lettura = 0.0
    senza_cache = False
    try:
        for _ in range(max(1, passate)):
            inizio = time.perf_counter()
            with open(percorso, "wb") as f:
                f.writelines(blocco for _ in range(n_blocchi))
                f.flush()
                os.fsync(f.fileno())
            scrittura = max(scrittura, byte / max(time.perf_counter() - inizio, 1e-9) / 1e6)
            letti, secondi, senza_cache = _leggi(percorso)
            lettura = max(lettura, letti / max(secondi, 1e-9) / 1e6)
        return {
            "scrittura_mb_s": scrittura,
            "lettura_mb_s": lettura,
            "senza_cache": senza_cache,
            "megabyte": byte // MB,
        }
    finally:
        with contextlib.suppress(OSError):
            os.remove(percorso)


def _nome_processore():
    if os.name == "nt":
        try:
            import winreg

            chiave = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            nome = winreg.QueryValueEx(chiave, "ProcessorNameString")[0]
            return " ".join(str(nome).split())
        except OSError:
            pass
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as f:
            for riga in f:
                if riga.lower().startswith("model name"):
                    return riga.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or platform.machine() or "sconosciuto"


def _frequenza_mhz():
    if psutil is not None:
        try:
            freq = psutil.cpu_freq()
            if freq and (freq.max or freq.current):
                return round(freq.max or freq.current)
        except (OSError, RuntimeError, AttributeError):
            pass
    if os.name == "nt":
        try:
            import winreg

            chiave = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            return int(winreg.QueryValueEx(chiave, "~MHz")[0])
        except (OSError, ValueError):
            pass
    return None


def _memoria_totale_byte():
    if psutil is not None:
        try:
            return int(psutil.virtual_memory().total)
        except (OSError, RuntimeError):
            pass
    if os.name == "nt":
        try:
            import ctypes

            class MemoryStatusEx(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stato = MemoryStatusEx()
            stato.dwLength = ctypes.sizeof(MemoryStatusEx)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stato)):
                return int(stato.ullTotalPhys)
        except (OSError, AttributeError):
            pass
    return None


def _memoria_disponibile_byte():
    if psutil is not None:
        try:
            return int(psutil.virtual_memory().available)
        except (OSError, RuntimeError):
            pass
    return None


def _alimentazione():
    if psutil is None:
        return None
    try:
        batteria = psutil.sensors_battery()
    except (OSError, RuntimeError, AttributeError):
        return None
    if batteria is None:
        return "rete"
    carica = f"batteria al {round(batteria.percent)}%"
    return f"rete, {carica}" if batteria.power_plugged else carica


def scheda_macchina():
    """Chi e' la macchina: nome, processore, core, memoria, sistema, Python e alimentazione.

    Ogni voce si prende come viene: cio' che non si riesce a leggere manca
    e basta, senza far cadere il banco di prova.
    """
    scheda = {
        "nome_computer": socket.gethostname(),
        "processore": _nome_processore(),
        "architettura": platform.machine(),
        "processori_logici": os.cpu_count() or 1,
        "sistema": platform.platform(),
        "python": platform.python_version(),
        "python_completo": sys.version.splitlines()[0],
    }
    if psutil is not None:
        try:
            fisici = psutil.cpu_count(logical=False)
            if fisici:
                scheda["core_fisici"] = int(fisici)
        except (OSError, RuntimeError):
            pass
    frequenza = _frequenza_mhz()
    if frequenza:
        scheda["frequenza_mhz"] = frequenza
    memoria = _memoria_totale_byte()
    if memoria:
        # In gigabyte binari, che e' come la memoria si compra e si nomina.
        scheda["ram_gb"] = round(memoria / (1024**3), 1)
    alimentazione = _alimentazione()
    if alimentazione:
        scheda["alimentazione"] = alimentazione
    return scheda


def aggregati(valori):
    """Minimo, massimo, media, mediana, dispersione e fuori norma di una serie di numeri.

    La dispersione e' la deviazione standard in percentuale della media. I
    fuori norma sono i valori che si scostano dalla mediana piu' della
    soglia, con il loro scarto percentuale, e si cercano solo da tre valori
    in su. Restituisce None per una serie vuota.
    """
    if not valori:
        return None
    n = len(valori)
    media = sum(valori) / n
    ordinati = sorted(valori)
    meta = n // 2
    mediana = ordinati[meta] if n % 2 else (ordinati[meta - 1] + ordinati[meta]) / 2
    deviazione = math.sqrt(sum((v - media) ** 2 for v in valori) / n)
    fuori = []
    if n >= 3 and mediana > 0:
        for i, v in enumerate(valori, 1):
            scarto = (v - mediana) / mediana * 100.0
            if abs(scarto) > SOGLIA_FUORI_NORMA:
                fuori.append((i, scarto))
    return {
        "quanti": n,
        "minimo": min(valori),
        "indice_minimo": valori.index(min(valori)) + 1,
        "massimo": max(valori),
        "indice_massimo": valori.index(max(valori)) + 1,
        "media": media,
        "mediana": mediana,
        "dispersione": (deviazione / media * 100.0) if media > 0 else 0.0,
        "fuori_norma": fuori,
    }


def profilo_di(profilo):
    """Il dizionario delle durate, da un nome fra breve, normale e lunga o da un dizionario gia' fatto."""
    if isinstance(profilo, dict):
        return dict(profilo)
    return dict(PROFILI[profilo])


def secondi_stimati(profilo, con_disco=True):
    p = profilo_di(profilo)
    totale = 3 * p["cpu_multi"] + 3 * p["cpu_singolo"] + 2 * p["memoria"]
    if con_disco:
        totale += SECONDI_DISCO_STIMATI * p["disco_mb"] / PROFILI["normale"]["disco_mb"]
    return round(totale)


def _megabyte_memoria_multi(processi):
    """Quanto blocco per processo nella prova di memoria su tutti i core, senza esagerare con la RAM."""
    megabyte = MEMORIA_MULTI_MB
    disponibile = _memoria_disponibile_byte()
    if disponibile:
        tetto = int(disponibile * MEMORIA_QUOTA_DISPONIBILE / (2 * processi) / MB)
        megabyte = min(megabyte, tetto)
    return max(MEMORIA_MULTI_MINIMO_MB, megabyte)


def _fase_cpu_multi(pool, processi, durata, tipo):
    risultati = pool.starmap(lavoro_cpu, [(durata, tipo)] * processi)
    per_processo = [op / max(sec, 1e-9) for op, sec in risultati]
    return {"op_s": sum(per_processo), "per_processo": per_processo, "durata": sum(sec for _, sec in risultati) / len(risultati)}


def _fase_cpu_singolo(pool, durata, tipo):
    op, sec = pool.apply(lavoro_cpu, (durata, tipo))
    return op / max(sec, 1e-9)


def _fase_memoria_multi(pool, processi, durata, megabyte):
    risultati = pool.starmap(lavoro_memoria, [(durata, megabyte)] * processi)
    return sum(byte / max(sec, 1e-9) for byte, sec in risultati) / 1e9


def esegui(profilo, annuncia, segnale, annullato, cartella_disco, versione, con_disco=True, con_sensori=True, pool=None):
    """Esegue tutte le fasi e restituisce la prova, oppure None se e' stata annullata.

    annuncia riceve le frasi da dire, segnale i nomi degli eventi da
    suonare, annullato viene interrogata fra una fase e l'altra e risponde
    vero se l'utente ha chiesto di smettere. pool, se dato, sostituisce il
    pool di processi: serve alle prove automatiche.
    """
    p = profilo_di(profilo)
    scheda = scheda_macchina()
    processi = int(scheda["processori_logici"])
    adesso = datetime.now()
    prova = {
        "data": adesso.isoformat(timespec="seconds"),
        "versione": versione,
        "profilo": profilo if isinstance(profilo, str) else "personalizzato",
        "python": scheda["python"],
        "scheda": scheda,
        "cpu_multi": {},
        "cpu_singolo": {},
        "memoria": {},
        "nota": "",
    }
    fasi = 3 + 3 + 2 + (1 if con_disco else 0)
    numero = 0

    def apri_fase(testo):
        nonlocal numero
        numero += 1
        segnale("banco_fase")
        annuncia(f"Fase {numero} di {fasi}: {testo}.")

    def chiudi_fase(testo):
        annuncia(testo)
        segnale("banco_fase_conclusa")
        if annullato():
            annuncia("Banco di prova annullato: niente viene salvato.")
            segnale("banco_annullato")
            return True
        return False

    campionatore = None
    if con_sensori and sensori is not None and sensori.disponibile():
        campionatore = sensori.Campionatore()
        campionatore.avvia()
        annuncia("Sensori di HWiNFO collegati: potenza, temperature e clock verranno registrati.")
    pool_proprio = pool is None
    if pool_proprio:
        pool = multiprocessing.Pool(processes=processi)
    try:
        for tipo, nome in PROVE_CPU:
            apri_fase(f"{nome} su {processi} processori, {numero_it(p['cpu_multi'], 0)} secondi")
            risultato = _fase_cpu_multi(pool, processi, p["cpu_multi"], tipo)
            prova["cpu_multi"][tipo] = risultato
            if chiudi_fase(f"Tutti i processori, {nome}: {formatta_numero_grande(risultato['op_s'])}."):
                return None
        for tipo, nome in PROVE_CPU:
            apri_fase(f"{nome} su un processore, {numero_it(p['cpu_singolo'], 0)} secondi")
            op_s = _fase_cpu_singolo(pool, p["cpu_singolo"], tipo)
            prova["cpu_singolo"][tipo] = op_s
            scala = prova["cpu_multi"][tipo]["op_s"] / op_s if op_s > 0 else 0
            if chiudi_fase(f"Un processore, {nome}: {formatta_numero_grande(op_s)}, fattore di scala {numero_it(scala, 1)}."):
                return None
        if campionatore is not None:
            prova["sensori"] = campionatore.ferma()
            campionatore = None
            if prova["sensori"] is None:
                del prova["sensori"]
        apri_fase(f"copia in memoria su un core, blocchi da {MEMORIA_SINGOLO_MB} megabyte, {numero_it(p['memoria'], 0)} secondi")
        byte, sec = pool.apply(lavoro_memoria, (p["memoria"], MEMORIA_SINGOLO_MB))
        prova["memoria"] = {"singolo_gb_s": byte / max(sec, 1e-9) / 1e9, "megabyte_singolo": MEMORIA_SINGOLO_MB}
        if chiudi_fase(f"Copia in memoria su un core: {numero_it(prova['memoria']['singolo_gb_s'], 1)} GB/s."):
            return None
        megabyte = _megabyte_memoria_multi(processi)
        apri_fase(
            f"copia in memoria su {processi} processori, blocchi da {megabyte} megabyte ciascuno, {numero_it(p['memoria'], 0)} secondi"
        )
        prova["memoria"]["multi_gb_s"] = _fase_memoria_multi(pool, processi, p["memoria"], megabyte)
        prova["memoria"]["megabyte_multi"] = megabyte
        prova["memoria"]["processi"] = processi
        if chiudi_fase(f"Copia in memoria su tutti i processori: {numero_it(prova['memoria']['multi_gb_s'], 1)} GB/s."):
            return None
        if con_disco:
            apri_fase(f"disco, scrittura e rilettura di un file da {p['disco_mb']} megabyte accanto al programma")
            try:
                prova["disco"] = misura_disco(cartella_disco, p["disco_mb"])
            except OSError as e:
                annuncia(f"Prova del disco non riuscita: {e}.")
            else:
                d = prova["disco"]
                cache = "senza cache di sistema" if d["senza_cache"] else "dalla cache di sistema"
                if chiudi_fase(
                    f"Disco: scrittura {numero_it(d['scrittura_mb_s'], 0)} MB/s, lettura {numero_it(d['lettura_mb_s'], 0)} MB/s {cache}."
                ):
                    return None
    finally:
        if campionatore is not None:
            campionatore.ferma()
        if pool_proprio:
            pool.close()
            pool.join()
    return prova


def _riga_scheda(scheda):
    parti = [scheda.get("nome_computer", "?"), scheda.get("processore", "processore sconosciuto")]
    fisici = scheda.get("core_fisici")
    logici = scheda.get("processori_logici")
    if fisici and logici and fisici != logici:
        parti.append(f"{fisici} core e {logici} processori logici")
    elif logici:
        parti.append(f"{logici} processori logici")
    if scheda.get("frequenza_mhz"):
        parti.append(f"frequenza base {numero_it(scheda['frequenza_mhz'], 0)} MHz")
    if scheda.get("ram_gb"):
        parti.append(f"{numero_it(scheda['ram_gb'], 1)} GB di memoria")
    return "Macchina: " + ", ".join(str(x) for x in parti) + "."


def righe_riepilogo(prova):
    """Il resoconto della prova, una frase per riga, uguale a schermo e nel file."""
    scheda = prova.get("scheda", {})
    adesso = datetime.fromisoformat(prova["data"])
    righe = [
        f"Banco di prova di Meditimer {prova.get('versione', '')}, profilo {prova.get('profilo', '')}, {data_italiana(adesso)} alle {ora_breve(adesso)}.",
        _riga_scheda(scheda),
    ]
    sistema = [f"Sistema: {scheda.get('sistema', 'sconosciuto')}", f"Python {prova.get('python', '')}"]
    if scheda.get("alimentazione"):
        sistema.append(f"alimentazione da {scheda['alimentazione']}")
    righe.append(", ".join(sistema) + ".")
    for tipo, _nome in PROVE_CPU:
        voce = prova["cpu_multi"].get(tipo)
        if not voce:
            continue
        testa = f"{NOMI_BREVI[tipo]}, tutti i processori:"
        valore = formatta_numero_grande(voce["op_s"])
        a = aggregati(voce.get("per_processo", []))
        if a and a["quanti"] > 1:
            coda = (
                f"per processo da {formatta_numero_grande(a['minimo'], '')} a {formatta_numero_grande(a['massimo'], '')}, "
                f"media {formatta_numero_grande(a['media'], '')}, dispersione {numero_it(a['dispersione'], 1)}%"
            )
            righe.append(riga_blocchi(testa, valore, coda))
            if a["fuori_norma"]:
                righe.append(_riga_fuori_norma(a["fuori_norma"]))
        else:
            righe.append(riga_blocchi(testa, valore))
    for tipo, _nome in PROVE_CPU:
        op_s = prova.get("cpu_singolo", {}).get(tipo)
        if not op_s:
            continue
        multi = prova["cpu_multi"].get(tipo, {}).get("op_s")
        coda = f"fattore di scala {numero_it(multi / op_s, 1)} su {scheda.get('processori_logici', '?')} processori" if multi else ""
        righe.append(riga_blocchi(f"{NOMI_BREVI[tipo]}, un processore:", formatta_numero_grande(op_s), coda))
    memoria = prova.get("memoria") or {}
    if memoria.get("singolo_gb_s"):
        righe.append(
            f"Copia in memoria su un core: {numero_it(memoria['singolo_gb_s'], 1)} GB/s, blocchi da {memoria.get('megabyte_singolo', '?')} megabyte."
        )
    if memoria.get("multi_gb_s"):
        fattore = memoria["multi_gb_s"] / memoria["singolo_gb_s"] if memoria.get("singolo_gb_s") else None
        coda = f", {numero_it(fattore, 1)} volte quella di un core" if fattore else ""
        righe.append(f"Copia in memoria su tutti i processori: {numero_it(memoria['multi_gb_s'], 1)} GB/s{coda}.")
    disco = prova.get("disco")
    if disco:
        cache = "senza cache di sistema" if disco.get("senza_cache") else "dalla cache di sistema"
        righe.append(
            f"Disco: scrittura {numero_it(disco['scrittura_mb_s'], 0)} MB/s, lettura {numero_it(disco['lettura_mb_s'], 0)} MB/s {cache}, "
            f"file da {disco.get('megabyte', '?')} megabyte."
        )
    righe.extend(righe_sensori(prova.get("sensori")))
    if prova.get("nota"):
        righe.append(f"Nota: {prova['nota']}.")
    return righe


def _riga_fuori_norma(fuori):
    """I processi fuori norma, elencati se sono pochi, riassunti se sono tanti."""
    if len(fuori) <= FUORI_NORMA_ELENCATI:
        elenco = ", ".join(f"processo {i} a {'meno' if s < 0 else 'più'} {numero_it(abs(s), 1)}%" for i, s in fuori)
        return f"Fuori norma: {elenco}."
    sotto = [s for _, s in fuori if s < 0]
    sopra = [s for _, s in fuori if s > 0]
    parti = []
    if sotto:
        parti.append(
            f"{len(sotto)} sotto la mediana, da meno {numero_it(min(abs(s) for s in sotto), 1)}% a meno {numero_it(max(abs(s) for s in sotto), 1)}%"
        )
    if sopra:
        parti.append(f"{len(sopra)} sopra, da più {numero_it(min(sopra), 1)}% a più {numero_it(max(sopra), 1)}%")
    return f"Fuori norma {len(fuori)} processi: " + "; ".join(parti) + "."


def righe_sensori(s):
    if not s:
        return []
    parti = []
    if s.get("potenza_media_w") is not None:
        parti.append(f"potenza media {numero_it(s['potenza_media_w'], 0)} W, massima {numero_it(s['potenza_max_w'], 0)} W")
    if s.get("temp_pkg_max") is not None:
        parti.append(f"temperatura massima del pacchetto {numero_it(s['temp_pkg_max'], 0)} gradi")
    if s.get("temp_core_max") is not None:
        parti.append(f"del core più caldo {numero_it(s['temp_core_max'], 0)} gradi")
    if s.get("p_clock_medio_mhz") is not None:
        parti.append(f"clock medio dei P-core {numero_it(s['p_clock_medio_mhz'], 0)} MHz")
    if s.get("e_clock_medio_mhz") is not None:
        parti.append(f"degli E-core {numero_it(s['e_clock_medio_mhz'], 0)} MHz")
    if not parti:
        return []
    righe = [f"Sensori di HWiNFO durante le prove del processore, {s.get('campioni', 0)} letture: " + ", ".join(parti) + "."]
    if s.get("limiti"):
        righe.append("Limiti scattati: " + ", ".join(s["limiti"]) + ".")
    return righe


def righe_dettaglio(prova):
    """Le velocita' di ogni processo, in milioni di operazioni al secondo: vanno nel file, non a schermo."""
    righe = []
    for tipo, nome in PROVE_CPU:
        per_processo = prova["cpu_multi"].get(tipo, {}).get("per_processo")
        if per_processo:
            valori = " ".join(numero_it(v / 1e6, 1) for v in per_processo)
            righe.append(f"Dettaglio per processo, {nome}, in milioni di op/s: {valori}.")
    return righe
