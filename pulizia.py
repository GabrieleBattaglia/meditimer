# Meditimer, la pulizia: i report piu' vecchi di un anno se ne vanno all'avvio.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 11/09/2026: nasce con la revisione 1, su richiesta di Gabriele: i report
# delle sessioni e delle prove crescevano senza limite nella cartella.

"""La pulizia dei report di Meditimer.

Ogni sessione e ogni banco di prova lasciano un file di testo accanto al
programma: Meditimer seguito da data e ora, benchmark seguito dal nome del
computer e dalla data. All'avvio il programma guarda la data di ognuno di
quei file e cancella quelli piu' vecchi di un anno. Si toccano soltanto i
file con quei due nomi e l'estensione txt, nella sola cartella del
programma: l'archivio delle prove, la sua copia di riserva e qualunque
altro file restano dove sono. La data e' quella di ultima modifica del
file, che e' anche la data in cui e' stato scritto.
"""

import fnmatch
import os
import time

ETA_MASSIMA_GIORNI = 365
MOTIVI = ("meditimer-*.txt", "benchmark-*.txt")
SECONDI_AL_GIORNO = 86400


def e_report(nome):
    """Vero se il nome e' quello di un report scritto da Meditimer."""
    minuscolo = str(nome).lower()
    return any(fnmatch.fnmatchcase(minuscolo, motivo) for motivo in MOTIVI)


def report_vecchi(cartella, adesso=None, eta_massima_giorni=ETA_MASSIMA_GIORNI):
    """I percorsi dei report piu' vecchi del limite, in ordine di nome. Mai un'eccezione."""
    adesso = time.time() if adesso is None else adesso
    limite = adesso - eta_massima_giorni * SECONDI_AL_GIORNO
    try:
        nomi = sorted(os.listdir(cartella))
    except OSError:
        return []
    vecchi = []
    for nome in nomi:
        if not e_report(nome):
            continue
        percorso = os.path.join(cartella, nome)
        try:
            if os.path.isfile(percorso) and os.path.getmtime(percorso) < limite:
                vecchi.append(percorso)
        except OSError:
            continue
    return vecchi


def rimuovi_report_vecchi(cartella, adesso=None, eta_massima_giorni=ETA_MASSIMA_GIORNI):
    """Cancella i report vecchi. Restituisce i nomi cancellati e le frasi degli errori."""
    cancellati, errori = [], []
    for percorso in report_vecchi(cartella, adesso, eta_massima_giorni):
        nome = os.path.basename(percorso)
        try:
            os.remove(percorso)
        except OSError as e:
            errori.append(f"Non riesco a cancellare {nome}: {e}.")
        else:
            cancellati.append(nome)
    return cancellati, errori
