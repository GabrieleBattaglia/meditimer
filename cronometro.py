# Meditimer, il cronometro: avvio, pausa, giri depurati dalle pause e statistiche.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 11/09/2026: revisione 1. I giri si misurano sull'orologio interno, che non
# conta le pause; ogni giro dice a parole rispetto a che cosa e' piu' veloce o
# piu' lento; il modulo non stampa e non suona, restituisce cio' che e' successo.

"""Il cronometro di Meditimer.

Tiene il tempo trascorso al netto delle pause e i giri, cioe' le fette di
tempo fra una pressione della barra spaziatrice e l'altra. Fino alla 2.9.1
i giri si misuravano sull'orologio di sistema e la pausa finiva dentro il
giro successivo: ora si misurano sul tempo trascorso, che le pause non
toccano. Ogni giro viene confrontato con il precedente e con la media di
quelli prima, e riceve un esito che dice se e' un primato, se e' nella
media, oppure solo piu' veloce o piu' lento del precedente: e' l'esito che
sceglie il suono. Il modulo non stampa nulla: restituisce oggetti e righe
gia' pensate per lo screen reader, e chi chiama decide cosa dire.
"""

import time
from dataclasses import dataclass

from formati import numero_it, percentuale_it, stringa_tempo_descrittiva, tempo_compatto

# Un giro che sta entro questa distanza dalla media dei precedenti, in
# percentuale, e' nella media: ne' meglio ne' peggio di come si stava andando.
SOGLIA_NELLA_MEDIA = 3.0
# Sotto questa differenza percentuale due giri si dicono uguali.
SOGLIA_UGUALE = 0.05
ESITI = ("primo", "record_veloce", "record_lento", "nella_media", "piu_veloce", "piu_lento", "uguale")


@dataclass
class Giro:
    """Un giro registrato, con il confronto con quelli prima.

    delta_precedente e delta_media sono variazioni percentuali della durata
    rispetto al giro precedente e alla media dei giri precedenti: negative
    quando il giro e' stato piu' veloce, cioe' piu' corto. Valgono None
    quando non c'e' con che cosa confrontare.
    """

    numero: int
    durata: float
    delta_precedente: float | None
    delta_media: float | None
    esito: str

    def compatto(self):
        """La riga breve per lo schermo, entro quaranta caratteri: g3 01:02.345 pv3,1% ml1,2% rv.

        g e' il numero del giro, poi il tempo in cifre; p e' il confronto con
        il giro precedente e m quello con la media dei precedenti, seguiti da
        v se piu' veloce, l se piu' lento, u se uguale, e dalla percentuale;
        rv in fondo e' un nuovo giro piu' veloce di tutti, rl piu' lento.
        E' la forma che Gabriele vuole per i dati in tempo reale: la frase
        per esteso, descrizione, va nel file di testo.
        """
        parti = [f"g{self.numero}", tempo_compatto(self.durata)]
        if self.delta_precedente is not None:
            parti.append("p" + _codice(self.delta_precedente))
        if self.delta_media is not None:
            parti.append("m" + _codice(self.delta_media))
        if self.esito == "record_veloce":
            parti.append("rv")
        elif self.esito == "record_lento":
            parti.append("rl")
        return " ".join(parti)

    def descrizione(self):
        """La frase del giro, per esempio: Giro 3: 1 minuto e 2 secondi, 3,1% più veloce del precedente."""
        testo = f"Giro {self.numero}: {stringa_tempo_descrittiva(self.durata)}"
        if self.delta_precedente is not None:
            testo += ", " + _confronto(self.delta_precedente, "del precedente", "uguale al precedente")
        if self.delta_media is not None:
            testo += ", " + _confronto(self.delta_media, "della media", "pari alla media")
        if self.esito == "record_veloce":
            return testo + ". Nuovo giro più veloce!"
        if self.esito == "record_lento":
            return testo + ". Nuovo giro più lento."
        return testo + "."


def _codice(delta):
    """Il confronto in lettere per la riga breve: u uguale, v3,1% piu' veloce, l3,1% piu' lento."""
    if abs(delta) < SOGLIA_UGUALE:
        return "u"
    return ("v" if delta < 0 else "l") + percentuale_it(abs(delta))


def _confronto(delta, riferimento, se_uguale):
    if abs(delta) < SOGLIA_UGUALE:
        return se_uguale
    verso = "più veloce" if delta < 0 else "più lento"
    return f"{percentuale_it(abs(delta))} {verso} {riferimento}"


def _variazione(durata, riferimento):
    if riferimento <= 0:
        return None
    return (durata - riferimento) / riferimento * 100.0


def _esito_dal_precedente(delta_precedente):
    if delta_precedente is None or abs(delta_precedente) < SOGLIA_UGUALE:
        return "uguale"
    return "piu_veloce" if delta_precedente < 0 else "piu_lento"


def valuta_giro(numero, durata, precedenti):
    """Costruisce il Giro confrontando la durata con i giri precedenti.

    Con nessun giro prima l'esito e' primo. Con un giro solo prima si
    confronta con quello e basta: dichiarare un primato fra due giri non
    direbbe niente. Da tre giri in su entrano i primati e la media.
    """
    if not precedenti:
        return Giro(numero, durata, None, None, "primo")
    delta_precedente = _variazione(durata, precedenti[-1])
    if len(precedenti) == 1:
        return Giro(numero, durata, delta_precedente, None, _esito_dal_precedente(delta_precedente))
    media = sum(precedenti) / len(precedenti)
    delta_media = _variazione(durata, media)
    if durata < min(precedenti):
        esito = "record_veloce"
    elif durata > max(precedenti):
        esito = "record_lento"
    elif delta_media is not None and abs(delta_media) <= SOGLIA_NELLA_MEDIA:
        esito = "nella_media"
    else:
        esito = _esito_dal_precedente(delta_precedente)
    return Giro(numero, durata, delta_precedente, delta_media, esito)


class Cronometro:
    """Il cronometro: parte, si ferma, riparte e registra i giri.

    orologio e' la funzione che da' il tempo, di norma time.perf_counter,
    che non risente delle regolazioni dell'orologio di sistema. Le prove
    automatiche ne passano una finta.
    """

    def __init__(self, orologio=time.perf_counter):
        self._orologio = orologio
        self.azzera()

    def azzera(self):
        """Torna allo stato di partenza: fermo, senza tempo e senza giri."""
        self._avviato = False
        self._in_corsa = False
        self._accumulato = 0.0
        self._ripartenza = 0.0
        self._tempo_ultimo_giro = 0.0
        self._giri = []
        self._registro = []

    @property
    def avviato(self):
        """Vero se e' partito almeno una volta dall'ultimo azzeramento."""
        return self._avviato

    @property
    def in_corsa(self):
        return self._in_corsa

    @property
    def giri(self):
        """Le durate dei giri, in secondi."""
        return list(self._giri)

    @property
    def registro(self):
        """I giri come oggetti Giro, nell'ordine in cui sono stati registrati."""
        return list(self._registro)

    def tempo_trascorso(self):
        """I secondi passati dall'avvio, senza le pause."""
        if not self._avviato:
            return 0.0
        if self._in_corsa:
            return self._accumulato + (self._orologio() - self._ripartenza)
        return self._accumulato

    def avvia_pausa(self):
        """Avvia, mette in pausa o riprende. Restituisce avviato, pausa o ripreso."""
        adesso = self._orologio()
        if self._in_corsa:
            self._accumulato += adesso - self._ripartenza
            self._in_corsa = False
            return "pausa"
        self._in_corsa = True
        self._ripartenza = adesso
        if self._avviato:
            return "ripreso"
        self._avviato = True
        return "avviato"

    def ferma(self):
        """Mette in pausa. Restituisce fermato, oppure None se non c'era niente da fermare."""
        if not self._in_corsa:
            return None
        self.avvia_pausa()
        return "fermato"

    def giro(self):
        """Registra un giro e lo restituisce, oppure None se il cronometro non sta andando."""
        if not self._in_corsa:
            return None
        trascorso = self.tempo_trascorso()
        durata = trascorso - self._tempo_ultimo_giro
        self._tempo_ultimo_giro = trascorso
        giro = valuta_giro(len(self._giri) + 1, durata, self._giri)
        self._giri.append(durata)
        self._registro.append(giro)
        return giro

    def statistiche(self):
        """I numeri dei giri, oppure None se i giri sono meno di due."""
        giri = self._giri
        if len(giri) < 2:
            return None
        veloce, lento = min(giri), max(giri)
        media = sum(giri) / len(giri)
        ordinati = sorted(giri)
        meta = len(ordinati) // 2
        mediana = ordinati[meta] if len(ordinati) % 2 else (ordinati[meta - 1] + ordinati[meta]) / 2
        scarto = sum(abs(g - media) for g in giri) / len(giri)
        return {
            "quanti": len(giri),
            "veloce": veloce,
            "numeri_veloce": [i + 1 for i, g in enumerate(giri) if g == veloce],
            "lento": lento,
            "numeri_lento": [i + 1 for i, g in enumerate(giri) if g == lento],
            "media": media,
            "mediana": mediana,
            "differenza": lento - veloce,
            "scarto_medio": scarto,
            "scarto_percentuale": (scarto / media * 100.0) if media > 0 else 0.0,
            "totale": sum(giri),
        }

    def righe_statistiche(self):
        """Le statistiche dei giri, una per riga, oppure una riga che dice perche' non ci sono."""
        s = self.statistiche()
        if s is None:
            return ["Servono almeno due giri registrati per le statistiche."]
        return [
            f"Statistiche di {s['quanti']} giri.",
            f"Giro più veloce: {stringa_tempo_descrittiva(s['veloce'])}, {_quali_giri(s['numeri_veloce'])}.",
            f"Giro più lento: {stringa_tempo_descrittiva(s['lento'])}, {_quali_giri(s['numeri_lento'])}.",
            f"Differenza fra il più lento e il più veloce: {stringa_tempo_descrittiva(s['differenza'])}.",
            f"Media: {stringa_tempo_descrittiva(s['media'])}.",
            f"Mediana: {stringa_tempo_descrittiva(s['mediana'])}.",
            f"Scarto medio dalla media: {stringa_tempo_descrittiva(s['scarto_medio'])}, il {numero_it(s['scarto_percentuale'])}%.",
            f"Tempo totale dei giri: {stringa_tempo_descrittiva(s['totale'])}.",
        ]


def _quali_giri(numeri):
    if len(numeri) == 1:
        return f"giro {numeri[0]}"
    elenco = ", ".join(str(n) for n in numeri[:-1]) + f" e {numeri[-1]}"
    return f"giri {elenco} a pari merito"


def righe_report(cronometro, versione, nota, tempo_esecuzione, adesso):
    """Il testo del report di una sessione, una frase per riga, senza decorazioni."""
    from formati import data_italiana, ora_breve

    righe = [
        f"Report di Meditimer versione {versione}.",
        f"Creato {data_italiana(adesso)} alle {ora_breve(adesso)}.",
    ]
    registro = cronometro.registro
    if registro:
        righe.append(f"Giri registrati: {len(registro)}.")
        righe.extend(g.descrizione() for g in registro)
        if len(registro) >= 2:
            righe.extend(cronometro.righe_statistiche())
    trascorso = cronometro.tempo_trascorso()
    if trascorso > 0:
        righe.append(f"Tempo totale trascorso: {stringa_tempo_descrittiva(trascorso)}.")
    if tempo_esecuzione > 0:
        righe.append(f"Tempo complessivo di esecuzione del programma: {stringa_tempo_descrittiva(tempo_esecuzione)}.")
    righe.append(f"Nota: {nota or 'nessuna'}.")
    return righe
