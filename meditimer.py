# Meditimer, l'affetta tempo: cronometro con giri, timer, sveglia e banco di prova della macchina.
# Studiato per chi usa uno screen reader e per il display braille.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# Concepito il 05/11/2015, portato a Python 3 nel 2017, rifatto nel 2022 e nel
# 2024, con le classifiche del banco di prova dal 01/10/2025.
# 11/09/2026: revisione 1 del refactoring generale. Il file unico si divide in
# moduli, i giri non contano piu' le pause, timer e sveglie si elencano, si
# annullano e si zittiscono, ogni tasto ha un suono, il banco di prova misura
# anche un processore solo, la memoria e il disco, e l'archivio delle prove
# tiene la cronologia di ogni macchina.

"""Meditimer, il programma principale.

Qui stanno il ciclo dei tasti e le frasi dette all'utente: il cronometro,
gli avvisi, il banco di prova e l'archivio vivono nei loro moduli e non
stampano. Ogni messaggio va a capo prima e non dopo, cosi' il cursore, e
con lui il display braille, resta sull'ultima cosa scritta; il prompt
comincia e finisce con un ritorno carrello, che riporta il cursore al suo
inizio. I prompt che aspettano un tasto solo passano da key, quelli che
aspettano una riga da dgt, entrambi di GBUtils.
"""

import contextlib
import multiprocessing
import sys
import time
from datetime import datetime

from GBUtils import dgt, gestisci_aggiornamento, key, manuale

import banco_prova
import classifiche
import suoni
from cronometro import Cronometro, righe_report
from formati import data_italiana, ora_breve, stringa_tempo_descrittiva
from percorsi import cartella_programma, percorso_dati, percorso_risorsa
from sveglie import GUIDA_DURATA, GUIDA_ORARIO, Registro, interpreta_durata, interpreta_orario
from version import AUTHOR, DATE, VERSION

APP_NAME = "meditimer"
API_RELEASE = "https://api.github.com/repos/GabrieleBattaglia/meditimer/releases/latest"
MANUALE = "manuale.txt"
PROMPT = "\rMenu principale, ? per i comandi > \r"
PROMPT_PROFILO = "\rDurata del banco di prova: b breve, n normale, l lunga, invio per normale, escape per annullare. \r"
PROFILI_TASTI = {"b": "breve", "n": "normale", "l": "lunga", "\r": "normale"}
# La suoneria: serie di rintocchi con le pause, finche' un tasto non la zittisce.
SERIE_SUONERIA = 3
RINTOCCHI_PER_SERIE = 5
PAUSA_RINTOCCHI = 2.0
PAUSA_SERIE = 4.0
COMANDI = (
    ("a", "avvia il cronometro, lo mette in pausa e lo riprende"),
    ("spazio", "registra un giro"),
    ("s", "registra l'ultimo giro e ferma il cronometro"),
    ("f", "statistiche dei giri"),
    ("c", "tempo trascorso dal cronometro"),
    ("z", "salva il report e azzera il cronometro"),
    ("x", "imposta un timer"),
    ("w", "imposta una sveglia"),
    ("l", "elenca timer e sveglie e ne annulla uno"),
    ("d", "data di oggi"),
    ("o", "ora"),
    ("v", "da quanto tempo gira il programma"),
    ("b", "banco di prova della macchina"),
    ("n", "classifiche dei banchi di prova"),
    ("m", "manuale"),
    ("?", "questo elenco"),
    ("q", "salva il report ed esce"),
    ("un tasto qualsiasi", "zittisce la suoneria di un timer o di una sveglia"),
)
TINIZIO = time.monotonic()


def dire(testo):
    """Una frase all'utente: a capo prima, non dopo, cosi' il cursore le resta sopra."""
    print("\n" + testo, end="", flush=True)


def dire_righe(righe):
    for riga in righe:
        dire(riga)


def scrivi_righe(percorso, righe):
    """Scrive le righe in un file di testo, una per riga. Solleva OSError."""
    with open(percorso, "w", encoding="utf-8") as f:
        f.write("\n".join(righe) + "\n")


NOMI_TASTI = {
    " ": "spazio",
    "\r": "invio",
    "\x1b": "escape",
    "\t": "tab",
    "\x08": "backspace",
    "up": "freccia su",
    "down": "freccia giù",
    "left": "freccia sinistra",
    "right": "freccia destra",
    "home": "inizio",
    "end": "fine",
    "pageup": "pagina su",
    "pagedown": "pagina giù",
    "insert": "ins",
    "delete": "canc",
}


def nome_tasto(tasto):
    """Come chiamare un tasto quando non e' fra quelli previsti."""
    if tasto in NOMI_TASTI:
        return NOMI_TASTI[tasto]
    if len(tasto) == 1 and not tasto.isprintable():
        return f"con codice {ord(tasto)}"
    return tasto


class Sessione:
    """Lo stato di una sessione di Meditimer e i comandi che lo cambiano."""

    def __init__(self):
        self.crono = Cronometro()
        self.registro = Registro(self._suoneria)
        self._archivio_dati = None
        self.comandi = {
            "a": self.avvia_pausa,
            " ": self.giro,
            "s": self.ferma,
            "f": self.statistiche,
            "c": self.tempo_trascorso,
            "z": self.azzera,
            "x": self.timer,
            "w": self.sveglia,
            "l": self.elenco,
            "d": self.data,
            "o": self.ora,
            "v": self.tempo_esecuzione,
            "b": self.banco,
            "n": self.classifiche,
            "m": self.manuale,
            "?": self.aiuto,
        }

    # --- Il dialogo -------------------------------------------------------

    @staticmethod
    def _chiedi(prompt, **parametri):
        """Una riga di testo dall'utente; la fine dello standard input vale come risposta vuota."""
        try:
            return dgt(prompt, **parametri)
        except EOFError:
            return parametri.get("default", "")

    def _archivio(self):
        """L'archivio delle prove, letto una volta sola; l'avviso della lettura si dice subito."""
        if self._archivio_dati is None:
            self._archivio_dati, avviso = classifiche.carica(percorso_dati(classifiche.NOME_FILE))
            if avviso:
                dire(avviso)
        return self._archivio_dati

    # --- La suoneria ------------------------------------------------------

    def _suoneria(self, avviso, silenzio):
        """Suona un timer o una sveglia scaduti, dal thread dell'avviso, finche' non viene zittita."""
        dire(avviso.conclusione(datetime.now()) + " Un tasto qualsiasi zittisce la suoneria.")
        for serie in range(SERIE_SUONERIA):
            for _ in range(RINTOCCHI_PER_SERIE):
                if silenzio.is_set():
                    return
                if not suoni.suona("allarme", sync=True):
                    print("\a", end="", flush=True)
                if silenzio.wait(PAUSA_RINTOCCHI):
                    return
            if serie < SERIE_SUONERIA - 1 and silenzio.wait(PAUSA_SERIE):
                return

    # --- Il cronometro ----------------------------------------------------

    def avvia_pausa(self):
        esito = self.crono.avvia_pausa()
        if esito == "avviato":
            dire("Cronometro avviato.")
            suoni.suona("cronometro_avviato")
        elif esito == "pausa":
            dire(f"Cronometro in pausa a {stringa_tempo_descrittiva(self.crono.tempo_trascorso())}.")
            suoni.suona("cronometro_pausa")
        else:
            dire("Cronometro ripreso.")
            suoni.suona("cronometro_ripreso")
        return False

    def giro(self):
        giro = self.crono.giro()
        if giro is None:
            dire("Il cronometro non sta andando: premi a per avviarlo.")
            suoni.suona("errore")
            return False
        suoni.suona_giro(giro.esito)
        dire(giro.descrizione())
        return False

    def ferma(self):
        if not self.crono.in_corsa:
            dire("Il cronometro non sta andando.")
            suoni.suona("errore")
            return False
        giro = self.crono.giro()
        self.crono.ferma()
        dire(giro.descrizione())
        dire(f"Cronometro fermato a {stringa_tempo_descrittiva(self.crono.tempo_trascorso())}.")
        suoni.suona("cronometro_fermato")
        return False

    def statistiche(self):
        righe = self.crono.righe_statistiche()
        suoni.suona("statistiche" if len(righe) > 1 else "errore")
        dire_righe(righe)
        return len(righe) > 1

    def tempo_trascorso(self):
        if not self.crono.avviato:
            dire("Il cronometro non è mai partito: premi a per avviarlo.")
            suoni.suona("errore")
            return False
        stato = "" if self.crono.in_corsa else ", in pausa"
        dire(f"Tempo trascorso: {stringa_tempo_descrittiva(self.crono.tempo_trascorso())}{stato}.")
        suoni.suona("tempo_trascorso")
        return False

    def azzera(self):
        if self.crono.in_corsa:
            dire("Metti in pausa il cronometro prima di azzerarlo, con a oppure s.")
            suoni.suona("errore")
            return False
        chiesto = self.salva_report()
        self.crono.azzera()
        dire("Cronometro azzerato.")
        suoni.suona("cronometro_azzerato")
        return chiesto

    def salva_report(self):
        """Scrive il report della sessione, se c'e' qualcosa da scrivere. Vero se ha chiesto la nota."""
        if not self.crono.avviato and not self.crono.giri:
            return False
        nota = self._chiedi("\nNota per il report del cronometro, invio per nessuna: ").strip()
        adesso = datetime.now()
        righe = righe_report(self.crono, VERSION, nota, time.monotonic() - TINIZIO, adesso)
        nome = f"Meditimer-{adesso.strftime('%y%m%d-%H%M%S')}.txt"
        percorso = percorso_dati(nome)
        try:
            scrivi_righe(percorso, righe)
        except OSError as e:
            dire(f"Report non salvato: {e}.")
            suoni.suona("errore")
            return True
        dire(f"Report salvato in {nome}, nella cartella {cartella_programma()}.")
        suoni.suona("report_salvato")
        return True

    # --- Timer e sveglie --------------------------------------------------

    def timer(self):
        testo = self._chiedi(f"\nDurata del timer, {GUIDA_DURATA}, invio per annullare: ")
        if not testo.strip():
            dire("Nessun timer impostato.")
            suoni.suona("annullato")
            return True
        secondi = interpreta_durata(testo)
        if secondi is None:
            dire(f"Durata non valida. Si scrive come {GUIDA_DURATA}, per esempio 90 oppure 2:30.")
            suoni.suona("errore")
            return True
        avviso = self.registro.aggiungi_timer(secondi)
        dire(avviso.annuncio(datetime.now()))
        suoni.suona("timer_impostato")
        return True

    def sveglia(self):
        testo = self._chiedi("\nOrario della sveglia, per esempio 13:02, 13, 5 oppure +5, invio per annullare: ")
        if not testo.strip():
            dire("Nessuna sveglia impostata.")
            suoni.suona("annullato")
            return True
        adesso = datetime.now()
        scadenza = interpreta_orario(testo, adesso)
        if scadenza is None:
            dire(f"Orario non valido. Si scrive cosi': {GUIDA_ORARIO}.")
            suoni.suona("errore")
            return True
        avviso = self.registro.aggiungi_sveglia(scadenza)
        dire(avviso.annuncio(adesso))
        suoni.suona("sveglia_impostata")
        return True

    def elenco(self):
        attivi = self.registro.attivi()
        suoni.suona("elenco")
        if not attivi:
            dire("Nessun timer e nessuna sveglia in attesa.")
            return False
        adesso = datetime.now()
        dire_righe([a.descrizione(adesso) for a in attivi])
        massimo = max(a.numero for a in attivi)
        numero = self._chiedi("\nNumero da annullare, invio per nessuno: ", kind="i", imin=0, imax=massimo, default=0)
        if not numero:
            return True
        avviso = self.registro.annulla(numero)
        if avviso is None:
            dire(f"Nessun timer o sveglia con il numero {numero} in attesa.")
            suoni.suona("errore")
            return True
        dire(f"{'Timer' if avviso.tipo == 'timer' else 'Sveglia'} {avviso.numero} annullato.")
        suoni.suona("annullato")
        return True

    # --- Data e tempi -----------------------------------------------------

    def data(self):
        adesso = datetime.now()
        dire(f"Oggi è {data_italiana(adesso)}, giorno {adesso.timetuple().tm_yday} dell'anno.")
        suoni.suona("data")
        return False

    def ora(self):
        dire(f"Sono le {ora_breve(datetime.now())}.")
        suoni.suona("ora")
        return False

    def tempo_esecuzione(self):
        dire(f"Il programma gira da {stringa_tempo_descrittiva(time.monotonic() - TINIZIO)}.")
        suoni.suona("tempo_esecuzione")
        return False

    # --- Il banco di prova ------------------------------------------------

    @staticmethod
    def _escape_premuto():
        """Vero se in coda c'e' un escape: si guarda fra una fase e l'altra del banco."""
        with contextlib.suppress(EOFError):
            return key(attesa=0, alla_scadenza=None) == "\x1b"
        return False

    def banco(self):
        tasto = key(PROMPT_PROFILO)
        print()
        profilo = PROFILI_TASTI.get(tasto.lower() if len(tasto) == 1 else tasto)
        if profilo is None:
            dire("Banco di prova annullato.")
            suoni.suona("annullato")
            return True
        secondi = banco_prova.secondi_stimati(profilo)
        dire(f"Banco di prova, profilo {profilo}: nove fasi, circa {secondi} secondi.")
        dire("Non usare il computer durante la prova. Fra una fase e l'altra escape annulla.")
        suoni.suona("banco_avvio", sync=True)
        prova = banco_prova.esegui(profilo, dire, suoni.suona, self._escape_premuto, cartella_programma(), VERSION)
        if prova is None:
            return True
        suoni.suona("banco_concluso", sync=True)
        righe = banco_prova.righe_riepilogo(prova)
        dire_righe(righe)
        dati = self._archivio()
        nome = prova["scheda"]["nome_computer"]
        classifiche.registra_prova(dati, nome, prova)
        confronto, primato = classifiche.righe_confronto(dati, nome, prova)
        dire_righe(confronto)
        if primato:
            suoni.suona("primato_macchina")
        prova["nota"] = self._chiedi("\nNota per questa prova, invio per nessuna: ").strip()
        percorso_archivio = percorso_dati(classifiche.NOME_FILE)
        try:
            classifiche.salva(percorso_archivio, dati)
        except OSError as e:
            dire(f"Archivio delle prove non salvato: {e}.")
            suoni.suona("errore")
        else:
            dire(f"Prova salvata nell'archivio {classifiche.NOME_FILE}, nella cartella {cartella_programma()}.")
            suoni.suona("banco_salvato")
        nome_file = f"benchmark-{nome}-{datetime.fromisoformat(prova['data']).strftime('%Y%m%d-%H%M%S')}.txt"
        try:
            scrivi_righe(percorso_dati(nome_file), banco_prova.righe_riepilogo(prova) + banco_prova.righe_dettaglio(prova))
        except OSError as e:
            dire(f"Report della prova non salvato: {e}.")
            suoni.suona("errore")
        else:
            dire(f"Report della prova salvato in {nome_file}.")
        return True

    def classifiche(self):
        suoni.suona("classifiche")
        dire_righe(classifiche.righe_classifiche(self._archivio()))
        return True

    # --- Aiuto ------------------------------------------------------------

    def manuale(self):
        suoni.suona("manuale")
        print()
        try:
            manuale(nf=percorso_risorsa(MANUALE), nome="Manuale di Meditimer")
        except (OSError, ValueError, EOFError) as e:
            dire(f"Manuale non disponibile: {e}.")
            suoni.suona("errore")
        return True

    @staticmethod
    def aiuto():
        dire_righe([f"{tasto}: {descrizione}." for tasto, descrizione in COMANDI])
        return True

    # --- Il ciclo ---------------------------------------------------------

    def esegui(self, tasto):
        """Esegue il comando del tasto. Vero se dopo va ristampato il prompt."""
        if self.registro.in_suoneria():
            self.registro.zittisci()
            dire("Suoneria zittita.")
            suoni.suona("allarme_zittito")
            return False
        if len(tasto) == 1:
            tasto = tasto.lower()
        comando = self.comandi.get(tasto)
        if comando is None:
            dire(f"Tasto {nome_tasto(tasto)} non previsto: premi ? per l'elenco dei comandi.")
            suoni.suona("tasto_sconosciuto")
            return False
        return comando()

    def chiudi(self):
        """L'uscita ordinata: report, avvisi annullati, saluto."""
        chiesto = self.salva_report()
        if not chiesto:
            dire("Nessun dato del cronometro da salvare.")
        self.registro.chiudi()
        dire("Arrivederci.")
        print()
        suoni.suona("chiusura", sync=True)
        suoni.chiudi()


def main():
    print(f"Meditimer, l'affetta tempo, versione {VERSION} del {DATE}.")
    print(f"Autori: {AUTHOR}.")
    suoni.suona("avvio")
    if gestisci_aggiornamento(APP_NAME, VERSION, API_RELEASE):
        suoni.suona("chiusura", sync=True)
        suoni.chiudi()
        return 0
    sessione = Sessione()
    print("Premi ? per l'elenco dei comandi, q per uscire.")
    prompt_da_stampare = True
    try:
        while True:
            if prompt_da_stampare:
                print("\n" + PROMPT, end="", flush=True)
                prompt_da_stampare = False
            tasto = key()
            if tasto.lower() == "q" and not sessione.registro.in_suoneria():
                break
            prompt_da_stampare = sessione.esegui(tasto)
    except KeyboardInterrupt:
        dire("Interrotto: salvo il report ed esco.")
    except EOFError:
        dire("Nessuna console da cui leggere: esco.")
    sessione.chiudi()
    return 0


if __name__ == "__main__":
    # Senza questa chiamata i processi del banco di prova, nell'eseguibile
    # compilato con PyInstaller, riavvierebbero il programma all'infinito.
    multiprocessing.freeze_support()
    sys.exit(main())
