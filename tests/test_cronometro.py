# Meditimer, prove sul cronometro: pause, giri, esiti, statistiche e report.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).

from datetime import datetime

import pytest

import cronometro as cr


class Orologio:
    """Un orologio finto che avanza solo quando glielo si chiede."""

    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t

    def avanza(self, secondi):
        self.t += secondi


@pytest.fixture
def orologio():
    return Orologio()


@pytest.fixture
def crono(orologio):
    return cr.Cronometro(orologio=orologio)


def test_i_giri_non_contano_le_pause(crono, orologio):
    assert crono.avvia_pausa() == "avviato"
    orologio.avanza(0.2)
    crono.giro()
    assert crono.avvia_pausa() == "pausa"
    orologio.avanza(1.0)
    assert crono.avvia_pausa() == "ripreso"
    orologio.avanza(0.2)
    crono.giro()
    giri = crono.giri
    assert giri == pytest.approx([0.2, 0.2])
    assert crono.tempo_trascorso() == pytest.approx(0.4)
    assert sum(giri) == pytest.approx(crono.tempo_trascorso())


def test_tempo_fermo_in_pausa_e_dopo_l_azzeramento(crono, orologio):
    assert crono.tempo_trascorso() == 0.0
    crono.avvia_pausa()
    orologio.avanza(2.0)
    crono.avvia_pausa()
    orologio.avanza(5.0)
    assert crono.tempo_trascorso() == pytest.approx(2.0)
    assert not crono.in_corsa
    assert crono.avviato
    crono.azzera()
    assert crono.tempo_trascorso() == 0.0
    assert not crono.avviato
    assert crono.giri == []


def test_ferma_solo_se_sta_andando(crono, orologio):
    assert crono.ferma() is None
    assert crono.giro() is None
    crono.avvia_pausa()
    orologio.avanza(1.0)
    assert crono.ferma() == "fermato"
    assert crono.ferma() is None
    assert crono.tempo_trascorso() == pytest.approx(1.0)


def _registra(crono, orologio, durate):
    crono.avvia_pausa()
    esiti = []
    for d in durate:
        orologio.avanza(d)
        esiti.append(crono.giro().esito)
    return esiti


def test_esiti_dei_giri(crono, orologio):
    esiti = _registra(crono, orologio, [1.0, 1.1, 0.9, 1.0, 1.5, 1.2, 1.2])
    assert esiti == ["primo", "piu_lento", "record_veloce", "nella_media", "record_lento", "piu_veloce", "uguale"]


def test_il_primato_vale_da_tre_giri(crono, orologio):
    esiti = _registra(crono, orologio, [1.0, 0.5])
    assert esiti == ["primo", "piu_veloce"]


def test_descrizione_del_giro_dice_rispetto_a_che_cosa(crono, orologio):
    _registra(crono, orologio, [1.0, 1.1, 0.9])
    registro = crono.registro
    assert registro[0].descrizione() == "Giro 1: 1 secondo."
    assert registro[1].descrizione() == "Giro 2: 1 secondo e 100 millisecondi, 10,0% più lento del precedente."
    assert registro[2].descrizione() == (
        "Giro 3: 900 millisecondi, 18,2% più veloce del precedente, 14,3% più veloce della media. Nuovo giro più veloce!"
    )
    assert registro[2].delta_precedente == pytest.approx(-18.18, abs=0.01)
    assert registro[2].delta_media == pytest.approx(-14.29, abs=0.01)


def test_riga_compatta_del_giro(crono, orologio):
    _registra(crono, orologio, [1.0, 1.1, 0.9, 0.9, 5.0])
    compatti = [g.compatto() for g in crono.registro]
    assert compatti[0] == "g1 00:01.000"
    assert compatti[1] == "g2 00:01.100 pl10,0%"
    assert compatti[2] == "g3 00:00.900 pv18,2% mv14,3% rv"
    assert compatti[3] == "g4 00:00.900 pu mv10,0%"
    assert compatti[4] == "g5 00:05.000 pl455,6% ml412,8% rl"
    assert all(len(c) <= 40 for c in compatti)
    estremo = cr.Giro(999, 35999.999, 999.9, -999.9, "record_lento")
    assert estremo.compatto() == "g999 9:59:59.999 pl999,9% mv999,9% rl"
    assert len(estremo.compatto()) <= 40


def test_giro_uguale_e_pari_alla_media(crono, orologio):
    _registra(crono, orologio, [1.0, 1.0, 1.0])
    ultimo = crono.registro[-1]
    assert ultimo.esito == "nella_media"
    assert ultimo.descrizione() == "Giro 3: 1 secondo, uguale al precedente, pari alla media."


def test_statistiche_con_pari_merito(crono, orologio):
    assert crono.statistiche() is None
    assert crono.righe_statistiche() == ["Servono almeno due giri registrati per le statistiche."]
    _registra(crono, orologio, [2.0, 1.0, 1.0, 2.0])
    s = crono.statistiche()
    assert s["numeri_veloce"] == [2, 3]
    assert s["numeri_lento"] == [1, 4]
    assert s["media"] == pytest.approx(1.5)
    assert s["mediana"] == pytest.approx(1.5)
    assert s["differenza"] == pytest.approx(1.0)
    assert s["scarto_medio"] == pytest.approx(0.5)
    assert s["scarto_percentuale"] == pytest.approx(33.33, abs=0.01)
    righe = crono.righe_statistiche()
    assert righe[0] == "Statistiche di 4 giri."
    assert righe[1] == "Giro più veloce: 1 secondo, giri 2 e 3 a pari merito."
    assert righe[2] == "Giro più lento: 2 secondi, giri 1 e 4 a pari merito."
    assert "33,3%" in righe[6]
    assert not any("-" * 3 in r for r in righe)


def test_report_della_sessione(crono, orologio):
    _registra(crono, orologio, [1.0, 2.0])
    righe = cr.righe_report(crono, "3.0.0", "prova", 12.5, datetime(2026, 9, 11, 8, 33, 12))
    assert righe[0] == "Report di Meditimer versione 3.0.0."
    assert righe[1] == "Creato venerdì 11 settembre 2026 alle 08:33:12."
    assert righe[2] == "Giri registrati: 2."
    assert righe[3] == "Giro 1: 1 secondo."
    assert righe[-1] == "Nota: prova."
    assert any(r.startswith("Tempo totale trascorso: 3 secondi") for r in righe)
    assert any(r.startswith("Tempo complessivo di esecuzione") for r in righe)
    assert "" not in righe


def test_report_senza_nota(crono, orologio):
    crono.avvia_pausa()
    orologio.avanza(1.0)
    righe = cr.righe_report(crono, "3.0.0", "", 0, datetime(2026, 9, 11))
    assert righe[-1] == "Nota: nessuna."
    assert not any(r.startswith("Giri registrati") for r in righe)
