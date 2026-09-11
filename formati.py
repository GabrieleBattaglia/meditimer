# Meditimer, i formati: tempi a parole, numeri all'italiana, date e blocchi per il braille.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 11/09/2026: nasce con la revisione 1, raccogliendo le funzioni che stavano
# sparse nel file unico. I numeri grandi si dicono a parole, milioni e
# miliardi, invece che con le lettere K, M e G, che la sintesi vocale legge
# come sillabe senza senso.

"""I formati di Meditimer.

Tutto cio' che il programma dice a numeri passa da qui, cosi' la virgola
decimale, il punto delle migliaia e le parole per i tempi sono gli stessi
in ogni schermata e in ogni file. Le righe fatte di piu' blocchi sono
pensate per il display braille: ogni blocco comincia a un multiplo di
quaranta caratteri, che e' una lettura sola delle dita.
"""

GIORNI_SETTIMANA = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
LARGHEZZA_BLOCCO = 40
# Da un milione in su i numeri si dicono a parole, con tre cifre significative.
SCALE = ((1_000_000_000_000, "bilione", "bilioni"), (1_000_000_000, "miliardo", "miliardi"), (1_000_000, "milione", "milioni"))


def stringa_tempo_descrittiva(secondi):
    """Un tempo in secondi detto a parole, saltando le parti che valgono zero.

    Per esempio 75,321 secondi diventa "1 minuto, 15 secondi e 321
    millisecondi". Singolare e plurale sono accordati e la congiunzione sta
    prima dell'ultima parte, che e' come si dice un tempo a chi ascolta.
    """
    secondi = max(0.0, float(secondi))
    interi = int(secondi)
    millisecondi = round((secondi - interi) * 1000)
    if millisecondi >= 1000:
        interi += 1
        millisecondi -= 1000
    ore, resto = divmod(interi, 3600)
    minuti, sec = divmod(resto, 60)
    parti = []
    if ore:
        parti.append(f"{ore} {'ora' if ore == 1 else 'ore'}")
    if minuti:
        parti.append(f"{minuti} {'minuto' if minuti == 1 else 'minuti'}")
    if sec:
        parti.append(f"{sec} {'secondo' if sec == 1 else 'secondi'}")
    if millisecondi:
        parti.append(f"{millisecondi} {'millisecondo' if millisecondi == 1 else 'millisecondi'}")
    if not parti:
        return "0 secondi"
    if len(parti) == 1:
        return parti[0]
    return ", ".join(parti[:-1]) + " e " + parti[-1]


def numero_it(valore, decimali=1):
    """Un numero con la virgola decimale e il punto delle migliaia, all'italiana."""
    testo = f"{float(valore):,.{decimali}f}"
    return testo.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def percentuale_it(valore, decimali=1, segno=False):
    """Una percentuale all'italiana, con il segno davanti se richiesto."""
    testo = numero_it(abs(valore) if not segno else valore, decimali)
    if segno and valore > 0:
        testo = "+" + testo
    return testo + "%"


def formatta_numero_grande(n, suffisso="op/s"):
    """Un numero grande detto a parole: 402.691.429 op/s diventa "403 milioni op/s".

    Sotto il milione il numero si scrive per intero con i punti delle
    migliaia. Da un milione in su si usano milioni, miliardi e bilioni con
    tre cifre significative, arrotondando prima di scegliere la scala:
    999.600.000 e' un miliardo, non mille milioni.
    """
    valore = float(n)
    for soglia, singolare, plurale in SCALE:
        ridotto = valore / soglia
        testo = f"{ridotto:.3g}"
        arrotondato = float(testo)
        if abs(arrotondato) >= 1.0:
            decimali = len(testo.split(".")[1]) if "." in testo and "e" not in testo else 0
            parola = singolare if arrotondato == 1.0 else plurale
            return f"{numero_it(arrotondato, decimali)} {parola} {suffisso}".strip()
    return f"{numero_it(round(valore), 0)} {suffisso}".strip()


def riga_blocchi(*blocchi):
    """Unisce i blocchi in una riga in cui ognuno comincia a un multiplo di quaranta.

    Ogni blocco tranne l'ultimo viene riempito di spazi fino al multiplo di
    quaranta successivo alla sua lunghezza, cosi' sul display braille il
    blocco dopo parte sempre dal quarantunesimo carattere, o dall'ottantunesimo.
    """
    pezzi = [str(b) for b in blocchi if str(b)]
    if not pezzi:
        return ""
    riga = ""
    for pezzo in pezzi[:-1]:
        riga += pezzo
        larghezza = ((len(riga) // LARGHEZZA_BLOCCO) + 1) * LARGHEZZA_BLOCCO
        riga = riga.ljust(larghezza)
    return riga + pezzi[-1]


def data_italiana(quando):
    """La data a parole: venerdì 11 settembre 2026."""
    return f"{GIORNI_SETTIMANA[quando.weekday()]} {quando.day} {MESI[quando.month - 1]} {quando.year}"


def data_breve(quando):
    return quando.strftime("%d/%m/%Y")


def ora_breve(quando):
    return quando.strftime("%H:%M:%S")
