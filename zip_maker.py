# Meditimer, utilita': prepara l'archivio per la distribuzione.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5, modalita' auto).
# 04/09/2026: primo chiamante, il mestiere sta in crea_archivio_release di GBUtils V104.

"""Comprime il risultato di PyInstaller in un solo archivio.

Tutto il mestiere sta in GBUtils, cosi' la regola sulle esclusioni e' una
sola per tutti i progetti. Qui restano soltanto i nomi di Meditimer.

Meditimer si compila in un file unico, quindi dentro dist c'e' soltanto
l'eseguibile e tutto il resto viaggia dentro di lui.

Si lasciano fuori i risultati dei benchmark e i rapporti delle sessioni,
che nascono accanto all'eseguibile appena lo si prova: i primi portano il
nome del computer di chi ha compilato, i secondi la data e l'ora delle sue
meditazioni.
"""

import sys

from GBUtils import crea_archivio_release

FUORI = [
    "benchmark_results.json",
    "benchmark-multicore-*.txt",
    "meditimer-*.txt",
]


def main():
    try:
        crea_archivio_release("meditimer", cartella_dist="dist", escludi=FUORI)
    except (FileNotFoundError, OSError) as e:
        print(f"Archivio non creato: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
