# Meditimer, prove su timer e sveglie: la sintassi degli orari e il registro.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).

import threading
from datetime import datetime, timedelta

import pytest

import sveglie as sv

ADESSO = datetime(2026, 9, 11, 8, 33, 20)


@pytest.mark.parametrize(
    ("testo", "atteso"),
    [
        ("35", 35),
        ("2:35", 155),
        ("3:3:35", 11015),
        (" 90 ", 90),
        ("0:90", 90),
        ("1:2:3:4", None),
        ("", None),
        ("-5", None),
        ("0", None),
        ("a", None),
        ("1:", None),
        ("2.5", None),
    ],
)
def test_interpreta_durata(testo, atteso):
    assert sv.interpreta_durata(testo) == atteso


@pytest.mark.parametrize(
    ("testo", "atteso"),
    [
        ("+5", ADESSO + timedelta(minutes=5)),
        ("+2:08", ADESSO + timedelta(hours=2, minutes=8)),
        ("+0:0:30", ADESSO + timedelta(seconds=30)),
        ("+90", ADESSO + timedelta(minutes=90)),
        ("+0", None),
        ("+", None),
        ("+1:2:3:4", None),
        ("5", datetime(2026, 9, 11, 9, 5, 0)),
        ("34", datetime(2026, 9, 11, 8, 34, 0)),
        ("33", datetime(2026, 9, 11, 9, 33, 0)),
        ("25", datetime(2026, 9, 11, 9, 25, 0)),
        ("13", datetime(2026, 9, 11, 13, 0, 0)),
        ("08", datetime(2026, 9, 12, 8, 0, 0)),
        ("05", datetime(2026, 9, 12, 5, 0, 0)),
        ("00", datetime(2026, 9, 12, 0, 0, 0)),
        ("0", datetime(2026, 9, 11, 9, 0, 0)),
        ("60", None),
        ("13:02", datetime(2026, 9, 11, 13, 2, 0)),
        ("8:10", datetime(2026, 9, 12, 8, 10, 0)),
        ("13:02:30", datetime(2026, 9, 11, 13, 2, 30)),
        ("8:33:20", datetime(2026, 9, 12, 8, 33, 20)),
        ("13:02:30:1", None),
        ("24:00", None),
        ("12:60", None),
        ("abc", None),
        ("", None),
        ("-5", None),
    ],
)
def test_interpreta_orario(testo, atteso):
    assert sv.interpreta_orario(testo, ADESSO) == atteso


def test_descrizioni_degli_avvisi():
    timer = sv.Avviso(1, "timer", ADESSO + timedelta(minutes=5), ADESSO)
    assert timer.descrizione(ADESSO) == "Timer 1 di 5 minuti, alle 08:38:20, mancano 5 minuti."
    assert timer.annuncio(ADESSO) == "Timer 1 di 5 minuti impostato, suonerà alle 08:38:20."
    assert timer.conclusione(ADESSO + timedelta(minutes=5)) == "Timer 1 di 5 minuti concluso alle 08:38:20."
    sveglia = sv.Avviso(2, "sveglia", datetime(2026, 9, 12, 7, 0, 0), ADESSO)
    assert sveglia.descrizione(ADESSO) == "Sveglia 2, alle 07:00:00 di 12/09/2026, mancano 22 ore, 26 minuti e 40 secondi."
    assert sveglia.annuncio(ADESSO).startswith("Sveglia 2 impostata alle 07:00:00 di 12/09/2026, fra 22 ore")
    assert sveglia.conclusione(datetime(2026, 9, 12, 7, 0, 1)) == "Sveglia 2 delle 07:00:00: sono le 07:00:01."


class Suoneria:
    """Raccoglie le chiamate del registro e finge di suonare finche' non viene zittita."""

    def __init__(self):
        self.suonati = []
        self.pronta = threading.Event()
        self.zittita = threading.Event()

    def __call__(self, avviso, silenzio):
        self.suonati.append(avviso.numero)
        self.pronta.set()
        if silenzio.wait(5.0):
            self.zittita.set()


def test_il_timer_suona_e_si_zittisce():
    suoneria = Suoneria()
    registro = sv.Registro(suoneria)
    avviso = registro.aggiungi_timer(0.2)
    assert avviso.tipo == "timer"
    assert [a.numero for a in registro.attivi()] == [1]
    assert suoneria.pronta.wait(3.0)
    assert suoneria.suonati == [1]
    assert registro.in_suoneria() is avviso
    assert registro.attivi() == []
    assert registro.zittisci()
    assert suoneria.zittita.wait(3.0)
    for _ in range(50):
        if registro.in_suoneria() is None:
            break
        threading.Event().wait(0.02)
    assert registro.in_suoneria() is None
    assert not registro.zittisci()


def test_annullare_evita_la_suoneria():
    suoneria = Suoneria()
    registro = sv.Registro(suoneria)
    registro.aggiungi_timer(0.3)
    sveglia = registro.aggiungi_sveglia(datetime.now() + timedelta(hours=1))
    assert [a.numero for a in registro.attivi()] == [1, 2]
    assert registro.annulla(1).numero == 1
    assert registro.annulla(1) is None
    assert registro.annulla(9) is None
    assert [a.numero for a in registro.attivi()] == [2]
    assert not suoneria.pronta.wait(0.8)
    assert suoneria.suonati == []
    registro.chiudi()
    assert registro.attivi() == []
    assert sveglia.annulla.is_set()


def test_gli_avvisi_sono_ordinati_per_scadenza():
    registro = sv.Registro(lambda *a: None)
    tardi = registro.aggiungi_sveglia(datetime.now() + timedelta(hours=2))
    presto = registro.aggiungi_sveglia(datetime.now() + timedelta(hours=1))
    assert [a.numero for a in registro.attivi()] == [presto.numero, tardi.numero]
    registro.chiudi()
