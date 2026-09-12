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

from GBUtils import cartella_applicazione
from GBUtils import percorso_risorsa as percorso_risorsa_condivisa


def cartella_programma():
    """La cartella dell'eseguibile compilato, oppure quella del sorgente.
    La logica sta in GBUtils, come tutte le utilita' condivise: qui restano i
    nomi con cui Meditimer la chiama."""
    return cartella_applicazione()


def percorso_dati(nome):
    """Un file che il programma scrive: sta sempre accanto al programma."""
    return os.path.join(cartella_programma(), nome)


def percorso_risorsa(nome):
    """Un file in sola lettura, come il manuale: da compilato sta dentro il pacchetto."""
    return percorso_risorsa_condivisa(nome)
