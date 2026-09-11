# Meditimer, prove sull'archivio dei banchi di prova: lettura, conversione, salvataggio, classifiche e confronto.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).

import json

import pytest

import classifiche as cl

VECCHIO = {
    "GabryBat": {
        "nome_computer": "GabryBat",
        "data_test": "2025-12-28T11:39:57.758852",
        "info_python": "3.13.2",
        "num_core": 32,
        "test": {
            "int": {"nome_test": "Calcoli su Interi", "performance_totale": 402691428.8},
            "float": {"nome_test": "Calcoli su Float", "performance_totale": 618925929.4},
            "math": {"nome_test": "Funzioni Matematiche", "performance_totale": 236513936.3},
        },
        "nota_utente": "",
    },
    "GabryMiniPC-GPD": {
        "nome_computer": "GabryMiniPC-GPD",
        "data_test": "2025-10-06T05:39:32.111677",
        "info_python": "3.11.9",
        "num_core": 8,
        "test": {
            "int": {"nome_test": "Calcoli su Interi", "performance_totale": 39197564.8},
            "float": {"nome_test": "Calcoli su Float", "performance_totale": 52030525.2},
            "math": {"nome_test": "Funzioni Matematiche", "performance_totale": 20080678.5},
        },
        "nota_utente": "Mini a batteria",
    },
    "Rotta": {"nome_computer": "Rotta", "data_test": "ieri", "test": {}},
}


def _prova(data, multi, singolo=None, memoria=None, disco=None, nota=""):
    prova = {
        "data": data,
        "versione": "3.0.0",
        "profilo": "normale",
        "python": "3.14.5",
        "scheda": {"nome_computer": "Prova", "processori_logici": 4},
        "cpu_multi": {t: {"op_s": v, "per_processo": [v / 4] * 4, "durata": 10.0} for t, v in zip(cl.PROVE_CPU, multi, strict=True)},
        "nota": nota,
    }
    if singolo:
        prova["cpu_singolo"] = dict(zip(cl.PROVE_CPU, singolo, strict=True))
    if memoria:
        prova["memoria"] = memoria
    if disco:
        prova["disco"] = disco
    return prova


def test_file_assente(tmp_path):
    dati, avviso = cl.carica(str(tmp_path / "x.json"))
    assert dati == cl.vuoto()
    assert avviso == ""


def test_file_illeggibile(tmp_path):
    percorso = tmp_path / "b.json"
    percorso.write_text("{non json", encoding="utf-8")
    dati, avviso = cl.carica(str(percorso))
    assert dati == cl.vuoto()
    assert avviso.startswith("Archivio delle prove illeggibile")
    percorso.write_text("[1, 2]", encoding="utf-8")
    assert cl.carica(str(percorso))[1].startswith("Archivio delle prove malformato")
    percorso.write_text(json.dumps({"formato": 99, "macchine": {}}), encoding="utf-8")
    assert "sconosciuto" in cl.carica(str(percorso))[1]


def test_conversione_dal_formato_della_2_9_1(tmp_path):
    percorso = tmp_path / "b.json"
    percorso.write_text(json.dumps(VECCHIO), encoding="utf-8")
    dati, avviso = cl.carica(str(percorso))
    assert avviso == "Archivio delle prove convertito dal formato della versione 2.9.1: 2 prove. Scartate 1 voci incomplete."
    assert sorted(dati["macchine"]) == ["GabryBat", "GabryMiniPC-GPD"]
    prova = cl.prove_di(dati, "GabryBat")[0]
    assert prova["cpu_multi"]["int"]["op_s"] == pytest.approx(402691428.8)
    assert prova["versione"] == "2.9.1"
    assert prova["scheda"]["processori_logici"] == 32
    assert cl.prove_di(dati, "GabryMiniPC-GPD")[0]["nota"] == "Mini a batteria"
    assert cl.valore(prova, "singolo") is None
    assert cl.valore(prova, "memoria") is None
    assert cl.valore(prova, "disco") is None
    assert cl.valore(prova, "multi") == pytest.approx(389_600_000, rel=0.01)


def test_salva_con_copia_di_riserva(tmp_path):
    percorso = str(tmp_path / "b.json")
    dati = cl.vuoto()
    cl.registra_prova(dati, "Uno", _prova("2026-09-11T10:00:00", (100.0, 200.0, 50.0)))
    cl.salva(percorso, dati)
    assert not (tmp_path / "b.json.bak").exists()
    cl.registra_prova(dati, "Uno", _prova("2026-09-12T10:00:00", (110.0, 210.0, 55.0)))
    cl.salva(percorso, dati)
    assert (tmp_path / "b.json.bak").exists()
    assert not (tmp_path / "b.json.tmp").exists()
    riletti, avviso = cl.carica(percorso)
    assert avviso == ""
    assert len(cl.prove_di(riletti, "Uno")) == 2
    assert riletti["macchine"]["Uno"]["scheda"]["nome_computer"] == "Prova"
    riserva = json.loads((tmp_path / "b.json.bak").read_text(encoding="utf-8"))
    assert len(riserva["macchine"]["Uno"]["prove"]) == 1


def test_le_voci_rotte_si_scartano_contandole(tmp_path):
    percorso = tmp_path / "b.json"
    buona = _prova("2026-09-11T10:00:00", (100.0, 200.0, 50.0))
    senza_data = dict(buona, data="mai")
    senza_multi = {k: v for k, v in buona.items() if k != "cpu_multi"}
    zero = _prova("2026-09-11T10:00:00", (0.0, 200.0, 50.0))
    strana = dict(buona, cpu_singolo={"int": "molto"}, memoria={"singolo_gb_s": -1}, disco={"scrittura_mb_s": 10})
    percorso.write_text(
        json.dumps(
            {
                "formato": 2,
                "macchine": {
                    "Uno": {"scheda": {}, "prove": [buona, senza_data, senza_multi, zero, strana]},
                    "Due": {"scheda": {}, "prove": [senza_data]},
                    "Tre": "niente",
                },
            }
        ),
        encoding="utf-8",
    )
    dati, avviso = cl.carica(str(percorso))
    assert avviso == "Scartate 5 voci incomplete dell'archivio delle prove."
    assert sorted(dati["macchine"]) == ["Uno"]
    prove = cl.prove_di(dati, "Uno")
    assert len(prove) == 2
    assert "cpu_singolo" not in prove[1]
    assert "memoria" not in prove[1]
    assert "disco" not in prove[1]


def _archivio():
    dati = cl.vuoto()
    cl.registra_prova(dati, "Lenta", _prova("2026-01-01T10:00:00", (10.0, 20.0, 5.0), singolo=(2.0, 4.0, 1.0)))
    cl.registra_prova(
        dati,
        "Veloce",
        _prova(
            "2026-02-01T10:00:00",
            (100.0, 200.0, 50.0),
            singolo=(20.0, 40.0, 10.0),
            memoria={"singolo_gb_s": 18.3, "multi_gb_s": 45.2},
            disco={"scrittura_mb_s": 2450.0, "lettura_mb_s": 3100.0, "senza_cache": True},
        ),
    )
    cl.registra_prova(dati, "Veloce", _prova("2026-03-01T10:00:00", (90.0, 180.0, 45.0)))
    return dati


def test_classifica_ordina_per_la_prova_migliore():
    dati = _archivio()
    voci = cl.classifica(dati, "multi")
    assert [v[0] for v in voci] == ["Veloce", "Lenta"]
    assert voci[0][2]["data"] == "2026-02-01T10:00:00"
    assert cl.posizione(dati, "multi", "Lenta") == (2, 2)
    assert cl.posizione(dati, "memoria", "Lenta") == (None, 1)
    assert [v[0] for v in cl.classifica(dati, "disco")] == ["Veloce"]


def test_righe_delle_classifiche_a_blocchi():
    dati = _archivio()
    righe = cl.righe_classifiche(dati)
    assert righe[0] == "Classifica multi core, 2 macchine, ordinate per la prova migliore di ciascuna."
    assert righe[1].startswith("1. Veloce, 01/02/2026")
    assert righe[1][40:].startswith("100 op/s")
    assert righe[1][80:] == "int 100, dec 200, mat 50"
    assert righe[2].startswith("2. Lenta, 01/01/2026")
    assert righe[3] == "Classifica un processore, 2 macchine, ordinate per la prova migliore di ciascuna."
    assert "Classifica memoria, una macchina, ordinate per la prova migliore di ciascuna." in righe
    memoria = next(r for r in righe if r.startswith("1. Veloce") and "GB/s" in r)
    assert memoria[40:].startswith("45,2 GB/s")
    assert memoria[80:] == "un core 18,3, tutti 45,2 GB/s"
    disco = next(r for r in righe if "MB/s" in r and r.startswith("1."))
    assert disco[40:].startswith("2.775 MB/s")
    assert disco[80:] == "scrittura 2.450, lettura 3.100 MB/s"
    assert righe[-3] == "Archivio: 3 prove di 2 macchine, dalla prima del 01/01/2026 all'ultima del 01/03/2026."
    assert righe[-2].endswith("un rapporto di 10,0 a 1.")
    assert righe[-1] == "La macchina con più prove è Veloce, con 2."
    assert "" not in righe


def test_archivio_vuoto_lo_dice():
    righe = cl.righe_classifiche(cl.vuoto())
    assert righe[0] == "Classifica multi core: nessuna prova in archivio."
    assert righe[-1] == "Archivio delle prove vuoto: premi b per fare la prima."


def test_confronto_con_le_prove_precedenti():
    dati = _archivio()
    nuova = _prova("2026-04-01T10:00:00", (110.0, 220.0, 55.0), singolo=(19.0, 38.0, 9.5), memoria={"multi_gb_s": 50.0})
    cl.registra_prova(dati, "Veloce", nuova)
    righe, primato = cl.righe_confronto(dati, "Veloce", nuova)
    assert primato
    assert righe[0] == "Multi core: 110 op/s, 22,2% più della prova precedente, nuovo primato di questa macchina."
    assert righe[1] == "Un processore: 19 op/s, il primato resta 20 op/s."
    assert righe[2] == "Memoria: 50,0 GB/s, nuovo primato di questa macchina."
    assert righe[3] == "In classifica multi core questa macchina è prima su 2."
    assert righe[4] == "In classifica un processore questa macchina è prima su 2."
    assert len(righe) == 5


def test_la_prima_prova_non_e_un_primato():
    dati = cl.vuoto()
    prova = _prova("2026-04-01T10:00:00", (110.0, 220.0, 55.0))
    cl.registra_prova(dati, "Nuova", prova)
    righe, primato = cl.righe_confronto(dati, "Nuova", prova)
    assert not primato
    assert righe == ["Multi core: 110 op/s, prima prova di questa macchina."]
    uguale = _prova("2026-04-02T10:00:00", (110.0, 220.0, 55.0))
    cl.registra_prova(dati, "Nuova", uguale)
    righe, primato = cl.righe_confronto(dati, "Nuova", uguale)
    assert not primato
    assert righe[0] == "Multi core: 110 op/s, come la prova precedente, il primato resta 110 op/s."
