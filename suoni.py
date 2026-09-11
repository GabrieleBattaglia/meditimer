# Meditimer, i suoni: la mappa fra gli eventi del programma e i preset della collezione condivisa.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 11/09/2026: nasce con la revisione 1. Fino alla 2.9.1 l'unico suono era il
# campanello del terminale, muto in certe configurazioni di Windows: ora ogni
# tasto e ogni funzione ha un preset suo in Acu_Collection.json, la collezione
# di Acusticator che tutto il parco software condivide.

"""Collega gli eventi di Meditimer ai suoni della collezione condivisa.

I suoni sono brevi e poco invasivi, per lo piu' sinusoidi: un cronometro si
sente decine di volte in una sessione e non deve stancare. Il giro ha un
suono per ogni esito, cosi' senza ascoltare la frase si sa gia' se e' stato
piu' veloce o piu' lento del precedente, se e' nella media, o se e' un
primato in un verso o nell'altro. La suoneria di timer e sveglie e' l'unico
suono pensato per farsi notare, e la ripete chi la chiama finche' non viene
zittita.
Il modulo non solleva mai: se l'audio manca o si rompe, il cronometro resta
vivo e muto. E' la sola rinuncia che il programma si concede, perche' una
sessione di cronometraggio persa per la scheda audio non e' accettabile.
"""

import contextlib

try:
    from GBUtils import Acusticator
except ImportError:
    Acusticator = None

EVENTI = {
    "avvio": "meditimer_avvio",
    "chiusura": "meditimer_chiusura",
    "cronometro_avviato": "meditimer_cronometro_avviato",
    "cronometro_pausa": "meditimer_cronometro_pausa",
    "cronometro_ripreso": "meditimer_cronometro_ripreso",
    "cronometro_fermato": "meditimer_cronometro_fermato",
    "cronometro_azzerato": "meditimer_cronometro_azzerato",
    "giro": "meditimer_giro",
    "giro_piu_veloce": "meditimer_giro_piu_veloce",
    "giro_piu_lento": "meditimer_giro_piu_lento",
    "giro_nella_media": "meditimer_giro_nella_media",
    "giro_uguale": "meditimer_giro_uguale",
    "record_veloce": "meditimer_record_veloce",
    "record_lento": "meditimer_record_lento",
    "statistiche": "meditimer_statistiche",
    "data": "meditimer_data",
    "ora": "meditimer_ora",
    "tempo_trascorso": "meditimer_tempo_trascorso",
    "tempo_esecuzione": "meditimer_tempo_esecuzione",
    "timer_impostato": "meditimer_timer_impostato",
    "sveglia_impostata": "meditimer_sveglia_impostata",
    "elenco": "meditimer_elenco",
    "annullato": "meditimer_annullato",
    "allarme": "meditimer_allarme",
    "allarme_zittito": "meditimer_allarme_zittito",
    "report_salvato": "meditimer_report_salvato",
    "banco_avvio": "meditimer_banco_avvio",
    "banco_fase": "meditimer_banco_fase",
    "banco_fase_conclusa": "meditimer_banco_fase_conclusa",
    "banco_concluso": "meditimer_banco_concluso",
    "banco_annullato": "meditimer_banco_annullato",
    "banco_salvato": "meditimer_banco_salvato",
    "classifiche": "meditimer_classifiche",
    "primato_macchina": "meditimer_primato_macchina",
    "manuale": "meditimer_manuale",
    "tasto_sconosciuto": "meditimer_tasto_sconosciuto",
    "errore": "meditimer_errore",
}

# L'esito di un giro, come lo chiama il cronometro, e il suo evento.
SUONI_GIRO = {
    "primo": "giro",
    "piu_veloce": "giro_piu_veloce",
    "piu_lento": "giro_piu_lento",
    "nella_media": "giro_nella_media",
    "uguale": "giro_uguale",
    "record_veloce": "record_veloce",
    "record_lento": "record_lento",
}


def suona(evento, sync=False):
    """Suona il preset dell'evento. Vero se e' partito, falso in ogni altro caso.

    Con sync vero aspetta la fine del suono: serve prima di chiudere il
    programma e nella suoneria, dove i rintocchi vanno uno dopo l'altro.
    Per tutto il resto il suono parte e il controllo torna subito, cosi' un
    giro registrato di fretta non aspetta il suono del giro prima.
    """
    nome = EVENTI.get(evento)
    if nome is None or Acusticator is None:
        return False
    try:
        return bool(Acusticator.play(nome, sync=sync))
    except Exception:  # noqa: BLE001 - l'audio non deve mai fermare il cronometro
        return False


def suona_giro(esito, sync=False):
    """Il suono che spetta all'esito di un giro."""
    return suona(SUONI_GIRO.get(esito, "giro"), sync=sync)


def chiudi():
    """Libera la scheda audio, all'uscita: un errore qui non ha piu' niente da rovinare."""
    if Acusticator is None:
        return
    with contextlib.suppress(Exception):
        Acusticator.close()
