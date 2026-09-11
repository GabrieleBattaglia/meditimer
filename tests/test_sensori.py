# Meditimer, prove sui sensori: la sintesi dei campioni e il comportamento senza HWiNFO.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).

import sensori as se


def test_riassunto_estrae_le_voci_giuste():
    voci = [
        {"tipo": "potenza", "nome": "CPU Package Power", "valore": 200.0},
        {"tipo": "temp", "nome": "CPU Package", "valore": 80.0},
        {"tipo": "temp", "nome": "Core Max", "valore": 85.0},
        {"tipo": "clock", "nome": "P-core 0 Clock", "valore": 5000.0},
        {"tipo": "clock", "nome": "P-core 1 Clock", "valore": 4000.0},
        {"tipo": "clock", "nome": "E-core 0 Clock", "valore": 3600.0},
        {"tipo": "altro", "nome": "Package/Ring Thermal Throttling", "valore": 1.0},
        {"tipo": "altro", "nome": "IA: EDP Limit", "valore": 0.0},
        {"tipo": "volt", "nome": "Vcore", "valore": 1.2},
    ]
    r = se.riassunto(voci)
    assert r["potenza"] == 200.0
    assert r["temp_pkg"] == 80.0
    assert r["temp_core_max"] == 85.0
    assert r["p_clock"] == 4500.0
    assert r["e_clock"] == 3600.0
    assert r["limiti"] == ["Package/Ring Thermal Throttling"]


def test_sintesi_dei_campioni():
    assert se.sintesi([]) is None
    campioni = [
        {"potenza": 200.0, "temp_pkg": 80.0, "temp_core_max": None, "p_clock": 5000.0, "e_clock": None, "limiti": []},
        {"potenza": 240.0, "temp_pkg": 90.0, "temp_core_max": 92.0, "p_clock": 4000.0, "e_clock": 3600.0, "limiti": ["EDP Limit"]},
    ]
    s = se.sintesi(campioni)
    assert s["campioni"] == 2
    assert s["potenza_media_w"] == 220.0
    assert s["potenza_max_w"] == 240.0
    assert s["temp_pkg_max"] == 90.0
    assert s["temp_core_max"] == 92.0
    assert s["p_clock_medio_mhz"] == 4500.0
    assert s["e_clock_medio_mhz"] == 3600.0
    assert s["limiti"] == ["EDP Limit"]


def test_campionatore_senza_hwinfo(monkeypatch):
    monkeypatch.setattr(se, "letture", lambda: None)
    assert not se.disponibile()
    campionatore = se.Campionatore(intervallo=0.01)
    campionatore.avvia()
    assert campionatore.ferma() is None


def test_campionatore_con_letture_finte(monkeypatch):
    monkeypatch.setattr(se, "letture", lambda: [{"tipo": "potenza", "nome": "CPU Package Power", "valore": 100.0}])
    campionatore = se.Campionatore(intervallo=0.01)
    campionatore.avvia()
    import time

    time.sleep(0.1)
    s = campionatore.ferma()
    assert s["campioni"] >= 2
    assert s["potenza_media_w"] == 100.0
