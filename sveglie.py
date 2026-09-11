# Meditimer, timer e sveglie: il registro degli avvisi attivi, l'attesa e la suoneria.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 11/09/2026: revisione 1. Fino alla 2.9.1 un timer partiva e spariva: non si
# poteva elencare, annullare ne' zittire. Ora ogni avviso sta in un registro,
# l'attesa controlla l'orologio ogni secondo e la sveglia con un numero solo
# segue la regola di Gabriele: 5 e' il minuto, 13 e' l'ora, +5 e' fra cinque minuti.

"""Timer e sveglie di Meditimer.

Un timer scade dopo una durata, una sveglia a un orario: dentro sono la
stessa cosa, un istante di scadenza. Ogni avviso vive in un thread demone
che dorme a passi di un secondo e a ogni passo confronta la scadenza con
l'orologio di sistema: cosi' l'annullamento arriva entro un secondo e una
sveglia resta all'orario giusto anche se la macchina e' stata sospesa,
mentre una sola dormita lunga avrebbe contato solo il tempo da sveglia.
Alla scadenza il registro chiama la funzione ricevuta alla nascita, che e'
di chi usa il modulo: e' lei che stampa e suona. Le riceve insieme un
evento di silenzio: finche' non e' impostato la suoneria puo' continuare,
quando lo e' deve smettere. Il modulo non stampa e non suona da solo.
"""

import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from formati import data_breve, ora_breve, stringa_tempo_descrittiva

PASSO_ATTESA = 1.0
GUIDA_ORARIO = "13:02 alle 13:02, 13 alle 13, 5 al minuto 5, +5 fra 5 minuti, +2:08 fra 2 ore e 8 minuti"
GUIDA_DURATA = "secondi, minuti:secondi oppure ore:minuti:secondi"


@dataclass
class Avviso:
    """Un timer o una sveglia in attesa, oppure gia' suonato o annullato."""

    numero: int
    tipo: str
    scadenza: datetime
    creazione: datetime
    annulla: threading.Event = field(default_factory=threading.Event)
    suonato: bool = False

    @property
    def durata(self):
        return (self.scadenza - self.creazione).total_seconds()

    def mancante(self, adesso):
        return max(0.0, (self.scadenza - adesso).total_seconds())

    def _quando(self, adesso):
        testo = f"alle {ora_breve(self.scadenza)}"
        if self.scadenza.date() != adesso.date():
            testo += f" di {data_breve(self.scadenza)}"
        return testo

    def descrizione(self, adesso):
        """Una riga per l'elenco: che cos'e', quando scade e quanto manca."""
        if self.tipo == "timer":
            testa = f"Timer {self.numero} di {stringa_tempo_descrittiva(round(self.durata))}"
        else:
            testa = f"Sveglia {self.numero}"
        return f"{testa}, {self._quando(adesso)}, mancano {stringa_tempo_descrittiva(round(self.mancante(adesso)))}."

    def annuncio(self, adesso):
        """La frase con cui l'avviso viene confermato appena impostato."""
        if self.tipo == "timer":
            return f"Timer {self.numero} di {stringa_tempo_descrittiva(round(self.durata))} impostato, suonerà {self._quando(adesso)}."
        return f"Sveglia {self.numero} impostata {self._quando(adesso)}, fra {stringa_tempo_descrittiva(round(self.mancante(adesso)))}."

    def conclusione(self, adesso):
        """La frase da dire quando suona."""
        if self.tipo == "timer":
            return f"Timer {self.numero} di {stringa_tempo_descrittiva(round(self.durata))} concluso alle {ora_breve(adesso)}."
        return f"Sveglia {self.numero} delle {ora_breve(self.scadenza)}: sono le {ora_breve(adesso)}."


class Registro:
    """Gli avvisi attivi, con i loro thread, e la suoneria in corso.

    al_suono viene chiamata nel thread dell'avviso con l'avviso e l'evento
    di silenzio. adesso e' la funzione che da' l'ora, di norma datetime.now.
    """

    def __init__(self, al_suono, adesso=datetime.now):
        self._al_suono = al_suono
        self._adesso = adesso
        self._avvisi = []
        self._prossimo = 1
        self._lock = threading.Lock()
        self._silenzio = threading.Event()
        self._in_suoneria = None

    def aggiungi_timer(self, secondi):
        adesso = self._adesso()
        return self._aggiungi("timer", adesso + timedelta(seconds=secondi), adesso)

    def aggiungi_sveglia(self, scadenza):
        return self._aggiungi("sveglia", scadenza, self._adesso())

    def _aggiungi(self, tipo, scadenza, adesso):
        with self._lock:
            avviso = Avviso(self._prossimo, tipo, scadenza, adesso)
            self._prossimo += 1
            self._avvisi.append(avviso)
        threading.Thread(target=self._attendi, args=(avviso,), daemon=True).start()
        return avviso

    def _attendi(self, avviso):
        while not avviso.annulla.is_set():
            resto = (avviso.scadenza - self._adesso()).total_seconds()
            if resto <= 0:
                break
            avviso.annulla.wait(min(PASSO_ATTESA, resto))
        if avviso.annulla.is_set():
            return
        avviso.suonato = True
        self._silenzio.clear()
        with self._lock:
            self._in_suoneria = avviso
        try:
            self._al_suono(avviso, self._silenzio)
        finally:
            with self._lock:
                self._in_suoneria = None

    def attivi(self):
        """Gli avvisi che devono ancora suonare, dal piu' vicino al piu' lontano."""
        with self._lock:
            vivi = [a for a in self._avvisi if not a.suonato and not a.annulla.is_set()]
        return sorted(vivi, key=lambda a: a.scadenza)

    def annulla(self, numero):
        """Annulla l'avviso con quel numero. Restituisce l'avviso, o None se non era attivo."""
        for avviso in self.attivi():
            if avviso.numero == numero:
                avviso.annulla.set()
                return avviso
        return None

    def in_suoneria(self):
        """L'avviso che sta suonando in questo momento, oppure None."""
        with self._lock:
            return self._in_suoneria

    def zittisci(self):
        """Ferma la suoneria in corso. Vero se ce n'era una.

        La suoneria viene dichiarata finita subito, qui, e non quando il
        thread se ne accorge: altrimenti il tasto premuto un attimo dopo
        verrebbe preso ancora per un tasto di silenzio.
        """
        with self._lock:
            if self._in_suoneria is None:
                return False
            self._in_suoneria = None
        self._silenzio.set()
        return True

    def chiudi(self):
        """Annulla tutto e tace: si chiama all'uscita dal programma."""
        for avviso in self.attivi():
            avviso.annulla.set()
        with self._lock:
            self._in_suoneria = None
        self._silenzio.set()


def _interi(parti):
    try:
        numeri = [int(p) for p in parti]
    except ValueError:
        return None
    if any(n < 0 for n in numeri):
        return None
    return numeri


def interpreta_durata(testo):
    """Una durata scritta come secondi, minuti:secondi o ore:minuti:secondi, in secondi.

    Restituisce None se il testo non e' una durata valida o vale zero.
    Piu' di tre campi sono un errore, non un eccesso da ignorare: fino alla
    2.9.1 il primo campo di quattro spariva in silenzio.
    """
    parti = str(testo).strip().split(":")
    if not 1 <= len(parti) <= 3:
        return None
    numeri = _interi(parti)
    if numeri is None:
        return None
    ore, minuti, secondi = [0] * (3 - len(numeri)) + numeri
    totale = ore * 3600 + minuti * 60 + secondi
    return totale if totale > 0 else None


def interpreta_orario(testo, adesso):
    """L'istante di una sveglia scritto come vuole Gabriele, oppure None.

    Con il piu' davanti e' un intervallo da adesso: +5 fra cinque minuti,
    +2:08 fra due ore e otto minuti, +0:0:30 fra trenta secondi.
    Senza, e' un orario: 13:02 o 13:02:30 sono l'orario esatto; un numero
    solo di due cifre che sia un'ora valida, da 00 a 23, e' quell'ora in
    punto; qualunque altro numero solo, da 0 a 59, e' un minuto dell'ora in
    corso, o della prossima se e' gia' passato. Un orario gia' passato oggi
    vale per domani.
    """
    testo = str(testo).strip()
    if not testo:
        return None
    if testo.startswith("+"):
        return _orario_relativo(testo[1:], adesso)
    parti = testo.split(":")
    numeri = _interi(parti)
    if numeri is None:
        return None
    if len(parti) == 1:
        return _orario_da_numero_solo(parti[0].strip(), numeri[0], adesso)
    if len(parti) == 2:
        ore, minuti = numeri
        secondi = 0
    elif len(parti) == 3:
        ore, minuti, secondi = numeri
    else:
        return None
    if ore > 23 or minuti > 59 or secondi > 59:
        return None
    scadenza = adesso.replace(hour=ore, minute=minuti, second=secondi, microsecond=0)
    if scadenza <= adesso:
        scadenza += timedelta(days=1)
    return scadenza


def _orario_relativo(testo, adesso):
    parti = testo.split(":")
    if not 1 <= len(parti) <= 3:
        return None
    numeri = _interi(parti)
    if numeri is None:
        return None
    if len(numeri) == 1:
        secondi = numeri[0] * 60
    elif len(numeri) == 2:
        secondi = numeri[0] * 3600 + numeri[1] * 60
    else:
        secondi = numeri[0] * 3600 + numeri[1] * 60 + numeri[2]
    if secondi <= 0:
        return None
    return adesso + timedelta(seconds=secondi)


def _orario_da_numero_solo(cifre, numero, adesso):
    if len(cifre) == 2 and 0 <= numero <= 23:
        scadenza = adesso.replace(hour=numero, minute=0, second=0, microsecond=0)
        if scadenza <= adesso:
            scadenza += timedelta(days=1)
        return scadenza
    if 0 <= numero <= 59:
        scadenza = adesso.replace(minute=numero, second=0, microsecond=0)
        if scadenza <= adesso:
            scadenza += timedelta(hours=1)
        return scadenza
    return None
