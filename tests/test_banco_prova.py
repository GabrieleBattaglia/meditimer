# Meditimer, prove sul banco di prova: i lavori, il disco, la scheda, gli aggregati e il resoconto.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).

import os

import pytest

import banco_prova as bp


class PoolFinto:
    """Esegue i lavori nel processo delle prove, uno dopo l'altro."""

    def starmap(self, funzione, argomenti):
        return [funzione(*a) for a in argomenti]

    def apply(self, funzione, argomenti):
        return funzione(*argomenti)


@pytest.mark.parametrize("tipo", ["int", "float", "math"])
def test_lavoro_cpu_conta_e_misura(tipo):
    operazioni, secondi = bp.lavoro_cpu(0.05, tipo)
    assert operazioni > 0
    assert operazioni % 1000 == 0
    assert 0.05 <= secondi < 0.5


def test_lavoro_cpu_rifiuta_prove_sconosciute():
    with pytest.raises(ValueError):
        bp.lavoro_cpu(0.01, "quantistica")


def test_lavoro_memoria_copia_qualcosa():
    byte, secondi = bp.lavoro_memoria(0.05, 1)
    assert byte > 0
    assert byte % bp.MB == 0
    assert secondi >= 0.05


def test_misura_disco_scrive_rilegge_e_cancella(tmp_path):
    risultato = bp.misura_disco(str(tmp_path), 4)
    assert risultato["scrittura_mb_s"] > 0
    assert risultato["lettura_mb_s"] > 0
    assert risultato["megabyte"] == 4
    assert risultato["senza_cache"] == (os.name == "nt")
    assert not os.path.exists(os.path.join(str(tmp_path), bp.NOME_FILE_DISCO))


def test_misura_disco_riferisce_l_errore(tmp_path):
    with pytest.raises(OSError):
        bp.misura_disco(str(tmp_path / "non_esiste"), 4)


def test_scheda_macchina_ha_il_minimo():
    scheda = bp.scheda_macchina()
    assert scheda["nome_computer"]
    assert scheda["processori_logici"] >= 1
    assert isinstance(scheda["processore"], str) and scheda["processore"]
    assert scheda["python"].count(".") >= 1
    assert scheda["sistema"]


def test_fuori_norma_elencati_o_riassunti():
    pochi = [(4, -50.0), (7, 25.0)]
    assert bp._riga_fuori_norma(pochi) == "Fuori norma: processo 4 a meno 50,0%, processo 7 a più 25,0%."
    tanti = [(i, -20.0 - i) for i in range(1, 8)] + [(9, 30.0)]
    assert (
        bp._riga_fuori_norma(tanti)
        == "Fuori norma 8 processi: 7 sotto la mediana, da meno 21,0% a meno 27,0%; 1 sopra, da più 30,0% a più 30,0%."
    )
    a = bp.aggregati([100.0] * 10 + [85.0] * 10 + [40.0])
    assert a["mediana"] == 85.0
    assert a["fuori_norma"] == [(21, pytest.approx(-52.94, abs=0.01))]


def test_aggregati():
    assert bp.aggregati([]) is None
    a = bp.aggregati([10.0, 10.0, 10.0, 5.0])
    assert a["quanti"] == 4
    assert a["minimo"] == 5.0 and a["indice_minimo"] == 4
    assert a["massimo"] == 10.0 and a["indice_massimo"] == 1
    assert a["media"] == pytest.approx(8.75)
    assert a["mediana"] == pytest.approx(10.0)
    assert a["dispersione"] == pytest.approx(24.74, abs=0.01)
    assert a["fuori_norma"] == [(4, pytest.approx(-50.0))]
    assert bp.aggregati([7.0, 7.0])["fuori_norma"] == []
    assert bp.aggregati([1.0])["dispersione"] == 0.0


def test_profili_e_stima():
    assert bp.profilo_di("normale")["cpu_multi"] == 10.0
    assert bp.profilo_di({"cpu_multi": 1})["cpu_multi"] == 1
    assert bp.secondi_stimati("normale") == 65
    assert bp.secondi_stimati("normale", con_disco=False) == 55
    assert bp.secondi_stimati("breve") < bp.secondi_stimati("lunga")


def _profilo_lampo():
    return {"cpu_multi": 0.02, "cpu_singolo": 0.02, "memoria": 0.02, "disco_mb": 4}


def test_esegui_tutte_le_fasi_con_il_pool_finto(tmp_path):
    detto, suonato = [], []
    prova = bp.esegui(
        _profilo_lampo(),
        detto.append,
        suonato.append,
        lambda: False,
        str(tmp_path),
        "3.0.0",
        con_sensori=False,
        pool=PoolFinto(),
    )
    assert prova is not None
    assert prova["versione"] == "3.0.0"
    assert prova["profilo"] == "personalizzato"
    assert set(prova["cpu_multi"]) == {"int", "float", "math"}
    n = prova["scheda"]["processori_logici"]
    assert len(prova["cpu_multi"]["int"]["per_processo"]) == n
    assert prova["cpu_multi"]["int"]["op_s"] == pytest.approx(sum(prova["cpu_multi"]["int"]["per_processo"]))
    assert set(prova["cpu_singolo"]) == {"int", "float", "math"}
    assert prova["memoria"]["singolo_gb_s"] > 0
    assert prova["memoria"]["multi_gb_s"] > 0
    assert prova["memoria"]["processi"] == n
    assert prova["disco"]["megabyte"] == 4
    assert "sensori" not in prova
    assert detto[0] == f"Fase 1 di 9: calcoli su interi su {n} processori, 0 secondi."
    assert detto[1].startswith("Tutti i processori, calcoli su interi:")
    assert sum(1 for d in detto if d.startswith("Fase ")) == 9
    assert suonato.count("banco_fase") == 9
    assert suonato.count("banco_fase_conclusa") == 9
    assert "banco_annullato" not in suonato
    righe = bp.righe_riepilogo(prova)
    assert righe[0].startswith("Banco di prova di Meditimer 3.0.0, profilo personalizzato,")
    assert righe[1].startswith("Macchina: ")
    assert any(r.startswith("Interi, tutti i processori:") and r[40:].endswith("%") for r in righe)
    assert any(r.startswith("Interi, un processore:") and "fattore di scala" in r[80:] for r in righe)
    assert any(r.startswith("Copia in memoria su un core:") for r in righe)
    assert any(r.startswith("Copia in memoria su tutti i processori:") for r in righe)
    assert any(r.startswith("Disco: scrittura") for r in righe)
    assert "" not in righe
    dettaglio = bp.righe_dettaglio(prova)
    assert len(dettaglio) == 3
    assert dettaglio[0].startswith("Dettaglio per processo, calcoli su interi, in milioni di op/s: ")


def test_esegui_si_ferma_quando_si_annulla(tmp_path):
    detto, suonato = [], []
    risposte = iter([False, True])
    prova = bp.esegui(
        _profilo_lampo(),
        detto.append,
        suonato.append,
        lambda: next(risposte),
        str(tmp_path),
        "3.0.0",
        con_disco=False,
        con_sensori=False,
        pool=PoolFinto(),
    )
    assert prova is None
    assert detto[-1] == "Banco di prova annullato: niente viene salvato."
    assert suonato[-1] == "banco_annullato"
    assert sum(1 for d in detto if d.startswith("Fase ")) == 2
    assert detto[0].endswith(" di 8: calcoli su interi su " + str(os.cpu_count() or 1) + " processori, 0 secondi.")


def test_riepilogo_di_una_prova_vecchia_senza_dettagli():
    prova = {
        "data": "2025-12-28T11:39:57",
        "versione": "2.9.1",
        "profilo": "normale",
        "python": "3.13.2",
        "scheda": {"nome_computer": "GabryBat", "processori_logici": 32},
        "cpu_multi": {"int": {"op_s": 402691428.8}, "float": {"op_s": 618925929.4}, "math": {"op_s": 236513936.3}},
        "nota": "prima del BIOS",
    }
    righe = bp.righe_riepilogo(prova)
    assert righe[1] == "Macchina: GabryBat, processore sconosciuto, 32 processori logici."
    assert righe[2] == "Sistema: sconosciuto, Python 3.13.2."
    assert righe[3][40:] == "403 milioni op/s"
    assert righe[-1] == "Nota: prima del BIOS."
    assert bp.righe_dettaglio(prova) == []
    assert bp.righe_sensori(None) == []


def test_righe_sensori():
    s = {
        "campioni": 5,
        "potenza_media_w": 210.4,
        "potenza_max_w": 253.0,
        "temp_pkg_max": 87.2,
        "temp_core_max": 91.0,
        "p_clock_medio_mhz": 4500.0,
        "e_clock_medio_mhz": 3600.0,
        "limiti": ["Package/Ring Thermal Throttling"],
    }
    righe = bp.righe_sensori(s)
    assert righe[0] == (
        "Sensori di HWiNFO durante le prove del processore, 5 letture: potenza media 210 W, massima 253 W, "
        "temperatura massima del pacchetto 87 gradi, del core più caldo 91 gradi, clock medio dei P-core 4.500 MHz, degli E-core 3.600 MHz."
    )
    assert righe[1] == "Limiti scattati: Package/Ring Thermal Throttling."
