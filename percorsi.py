# Meditimer, i percorsi: dove stanno i file, da sorgente e da eseguibile.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 11/09/2026: nasce con la revisione 1. Fino alla 2.9.1 i file nascevano nella
# directory di lavoro, cioe' in una cartella diversa a seconda di come si
# avviava il programma.

"""I percorsi di Meditimer.

Due regole, prese dal memorandum sui percorsi in docs. Cio' che il programma
scrive, cioe' i report e il file delle classifiche, sta accanto al programma:
accanto all'eseguibile quando e' compilato, accanto ai sorgenti altrimenti.
Cio' che il programma legge soltanto, cioe' il manuale, da compilato viaggia
dentro il pacchetto, nella cartella temporanea che PyInstaller apre all'avvio,
e li' va cercato per primo.
"""

import os
import sys


def cartella_programma():
    """La cartella dell'eseguibile compilato, oppure quella del sorgente."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def percorso_dati(nome):
    """Un file che il programma scrive: sta sempre accanto al programma."""
    return os.path.join(cartella_programma(), nome)


def percorso_risorsa(nome):
    """Un file in sola lettura, come il manuale: da compilato sta dentro il pacchetto."""
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", None)
        if base and os.path.isfile(os.path.join(base, nome)):
            return os.path.join(base, nome)
    return percorso_dati(nome)
