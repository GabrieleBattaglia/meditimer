# Meditimer, utilita': fa sentire uno per uno i suoni del programma.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 11/09/2026: nasce con la revisione 1, per collaudare i trentasette preset nuovi.

"""Ascolto guidato dei suoni di Meditimer.

Per ogni evento scrive il nome, il preset e la sua descrizione, aspetta un
tasto e suona. Spazio ripete il suono, invio passa al successivo, escape
chiude. I suoni si sentono nell'ordine in cui capitano usando il programma:
prima il cronometro con tutti gli esiti dei giri, poi timer e sveglie con
la suoneria, poi il banco di prova e le classifiche, infine gli errori.
"""

import sys

from GBUtils import Acusticator, key

from suoni import EVENTI, suona

ORDINE = (
    "avvio",
    "cronometro_avviato",
    "giro",
    "giro_piu_veloce",
    "giro_piu_lento",
    "giro_nella_media",
    "giro_uguale",
    "record_veloce",
    "record_lento",
    "cronometro_pausa",
    "cronometro_ripreso",
    "cronometro_fermato",
    "statistiche",
    "tempo_trascorso",
    "report_salvato",
    "cronometro_azzerato",
    "timer_impostato",
    "sveglia_impostata",
    "elenco",
    "annullato",
    "allarme",
    "allarme_zittito",
    "data",
    "ora",
    "tempo_esecuzione",
    "banco_avvio",
    "banco_fase",
    "banco_fase_conclusa",
    "banco_concluso",
    "banco_annullato",
    "primato_macchina",
    "banco_salvato",
    "classifiche",
    "manuale",
    "tasto_sconosciuto",
    "errore",
    "chiusura",
)


def main():
    mancanti = [e for e in EVENTI if e not in ORDINE]
    if mancanti:
        print("Eventi fuori dall'ordine di ascolto: " + ", ".join(mancanti) + ".")
    print(f"{len(ORDINE)} suoni. Invio suona e passa oltre, spazio ripete, escape chiude.")
    for numero, evento in enumerate(ORDINE, 1):
        preset = EVENTI[evento]
        print(f"{numero}. Evento {evento}, preset {preset}.")
        print(Acusticator.descrizione(preset) or "Senza descrizione.")
        tasto = key("\rPremi invio per sentirlo.\r")
        print()
        if tasto == "\x1b":
            return 0
        while True:
            suona(evento, sync=True)
            tasto = key("\rSpazio ripete, invio prosegue.\r")
            print()
            if tasto == "\x1b":
                return 0
            if tasto != " ":
                break
    print("Fine dei suoni.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
