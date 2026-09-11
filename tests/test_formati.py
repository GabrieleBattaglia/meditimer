# Meditimer, prove sui formati: tempi a parole, numeri all'italiana, blocchi braille.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).

from datetime import datetime

import formati as f


def test_tempo_a_parole_con_tutte_le_parti():
    assert f.stringa_tempo_descrittiva(75.321) == "1 minuto, 15 secondi e 321 millisecondi"


def test_tempo_a_parole_salta_le_parti_nulle():
    assert f.stringa_tempo_descrittiva(3600) == "1 ora"
    assert f.stringa_tempo_descrittiva(7322) == "2 ore, 2 minuti e 2 secondi"
    assert f.stringa_tempo_descrittiva(0) == "0 secondi"
    assert f.stringa_tempo_descrittiva(-3) == "0 secondi"
    assert f.stringa_tempo_descrittiva(0.001) == "1 millisecondo"


def test_tempo_a_parole_arrotonda_i_millisecondi_con_riporto():
    assert f.stringa_tempo_descrittiva(59.9996) == "1 minuto"
    assert f.stringa_tempo_descrittiva(1.9995) == "2 secondi"


def test_numeri_all_italiana():
    assert f.numero_it(1234.5) == "1.234,5"
    assert f.numero_it(1234567, 0) == "1.234.567"
    assert f.numero_it(0.25, 2) == "0,25"
    assert f.percentuale_it(3.14) == "3,1%"
    assert f.percentuale_it(-3.14) == "3,1%"
    assert f.percentuale_it(3.14, segno=True) == "+3,1%"
    assert f.percentuale_it(-3.14, segno=True) == "-3,1%"


def test_numeri_grandi_a_parole():
    assert f.formatta_numero_grande(402691428.8) == "403 milioni op/s"
    assert f.formatta_numero_grande(56385611) == "56,4 milioni op/s"
    assert f.formatta_numero_grande(1234567) == "1,23 milioni op/s"
    assert f.formatta_numero_grande(999400) == "999.400 op/s"
    assert f.formatta_numero_grande(999600) == "1 milione op/s"
    assert f.formatta_numero_grande(999600000) == "1 miliardo op/s"
    assert f.formatta_numero_grande(1000000) == "1 milione op/s"
    assert f.formatta_numero_grande(0) == "0 op/s"
    assert f.formatta_numero_grande(2.5e12, "byte") == "2,5 bilioni byte"


def test_riga_a_blocchi_parte_dal_quarantunesimo():
    riga = f.riga_blocchi("1. GabryBat, 28/12/2025", "interi 403 milioni op/s")
    assert riga[40:] == "interi 403 milioni op/s"
    assert riga[:23] == "1. GabryBat, 28/12/2025"
    lunga = f.riga_blocchi("x" * 45, "coda")
    assert lunga[80:] == "coda"
    assert f.riga_blocchi("solo") == "solo"
    assert f.riga_blocchi("", "") == ""


def test_date():
    quando = datetime(2026, 9, 11, 8, 33, 12)
    assert f.data_italiana(quando) == "venerdì 11 settembre 2026"
    assert f.data_breve(quando) == "11/09/2026"
    assert f.ora_breve(quando) == "08:33:12"
