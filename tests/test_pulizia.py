# Meditimer, prove sulla pulizia: solo i report, solo quelli vecchi, mai l'archivio.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).

import os

import pulizia as pu

GIORNO = 86400


def _scrivi(cartella, nome, eta_giorni, adesso):
    percorso = cartella / nome
    percorso.write_text("x", encoding="utf-8")
    quando = adesso - eta_giorni * GIORNO
    os.utime(percorso, (quando, quando))
    return percorso


def test_riconosce_i_report():
    assert pu.e_report("Meditimer-260911-094614.txt")
    assert pu.e_report("meditimer-260911-094614.TXT")
    assert pu.e_report("benchmark-GabryBat-20260911-094457.txt")
    assert pu.e_report("benchmark-multicore-GabryBat-20251003-174352.txt")
    assert not pu.e_report("benchmark_results.json")
    assert not pu.e_report("benchmark_results.json.bak")
    assert not pu.e_report("manuale.txt")
    assert not pu.e_report("collaudo.txt")
    assert not pu.e_report("Meditimer-260911.log")
    assert not pu.e_report("banco_prova_disco.tmp")


def test_cancella_solo_i_report_vecchi(tmp_path):
    adesso = 1_800_000_000.0
    vecchio = _scrivi(tmp_path, "Meditimer-250101-120000.txt", 400, adesso)
    vecchia_prova = _scrivi(tmp_path, "benchmark-GabryBat-20250101-120000.txt", 366, adesso)
    recente = _scrivi(tmp_path, "Meditimer-260901-120000.txt", 10, adesso)
    al_limite = _scrivi(tmp_path, "benchmark-X-20250912-120000.txt", 364, adesso)
    archivio = _scrivi(tmp_path, "benchmark_results.json", 900, adesso)
    riserva = _scrivi(tmp_path, "benchmark_results.json.bak", 900, adesso)
    altro = _scrivi(tmp_path, "appunti.txt", 900, adesso)
    sotto = tmp_path / "sotto"
    sotto.mkdir()
    annidato = _scrivi(sotto, "Meditimer-240101-120000.txt", 900, adesso)
    assert pu.report_vecchi(str(tmp_path), adesso) == [str(vecchio), str(vecchia_prova)]
    cancellati, errori = pu.rimuovi_report_vecchi(str(tmp_path), adesso)
    assert cancellati == ["Meditimer-250101-120000.txt", "benchmark-GabryBat-20250101-120000.txt"]
    assert errori == []
    assert not vecchio.exists() and not vecchia_prova.exists()
    for intatto in (recente, al_limite, archivio, riserva, altro, annidato):
        assert intatto.exists()
    assert pu.rimuovi_report_vecchi(str(tmp_path), adesso) == ([], [])


def test_cartella_assente_o_illeggibile(tmp_path):
    assert pu.report_vecchi(str(tmp_path / "non_esiste")) == []
    assert pu.rimuovi_report_vecchi(str(tmp_path / "non_esiste")) == ([], [])


def test_errore_di_cancellazione_riferito(tmp_path, monkeypatch):
    adesso = 1_800_000_000.0
    _scrivi(tmp_path, "Meditimer-250101-120000.txt", 400, adesso)

    def rifiuta(percorso):
        raise PermissionError("negato")

    monkeypatch.setattr(pu.os, "remove", rifiuta)
    cancellati, errori = pu.rimuovi_report_vecchi(str(tmp_path), adesso)
    assert cancellati == []
    assert errori == ["Non riesco a cancellare Meditimer-250101-120000.txt: negato."]
