# Meditimer, prova sul programma principale: una sessione intera senza console e senza suoni.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).

import os
import threading
import time

import pytest

import meditimer
import suoni


class Copione:
    """I tasti e le righe che l'utente finto digita, e i suoni che il programma ha chiesto."""

    def __init__(self, tasti, righe=()):
        self._tasti = list(tasti)
        self._righe = list(righe)
        self.suonati = []
        self.stampato = []

    def key(self, prompt="", attesa=None, alla_scadenza=""):
        if attesa == 0:
            return alla_scadenza
        if not self._tasti:
            return "q"
        tasto = self._tasti.pop(0)
        if callable(tasto):
            tasto = tasto()
        if isinstance(tasto, BaseException):
            raise tasto
        return tasto

    def dgt(self, prompt="", **parametri):
        if not self._righe:
            return parametri.get("default", "")
        riga = self._righe.pop(0)
        if parametri.get("kind") == "i":
            return int(riga) if str(riga).strip() else parametri.get("default", 0)
        return riga

    def suona(self, evento, sync=False):
        self.suonati.append(evento)
        return True

    def suona_giro(self, esito, sync=False):
        self.suonati.append(suoni.SUONI_GIRO[esito])
        return True


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Redirige file, tastiera, suoni e rete, e restituisce una fabbrica di copioni."""
    monkeypatch.setattr(meditimer, "cartella_programma", lambda: str(tmp_path))
    monkeypatch.setattr(meditimer, "percorso_dati", lambda nome: os.path.join(str(tmp_path), nome))
    monkeypatch.setattr(meditimer, "percorso_risorsa", lambda nome: os.path.join(str(tmp_path), nome))
    monkeypatch.setattr(meditimer, "gestisci_aggiornamento", lambda *a, **k: False)
    monkeypatch.setattr(meditimer, "manuale", lambda **k: True)
    monkeypatch.setattr(suoni, "chiudi", lambda: None)

    def prepara(tasti, righe=()):
        copione = Copione(tasti, righe)
        monkeypatch.setattr(meditimer, "key", copione.key)
        monkeypatch.setattr(meditimer, "dgt", copione.dgt)
        monkeypatch.setattr(suoni, "suona", copione.suona)
        monkeypatch.setattr(suoni, "suona_giro", copione.suona_giro)
        return copione

    return prepara


def _pausa(secondi):
    def attendi():
        time.sleep(secondi)
        return " "

    return attendi


def test_sessione_di_cronometraggio(banco, tmp_path, capsys):
    copione = banco(
        ["a", _pausa(0.05), _pausa(0.05), "s", "f", "c", "a", "z", "d", "o", "v", "?", "!", "up", "q"],
        ["la nota della prova", "seconda nota"],
    )
    assert meditimer.main() == 0
    uscita = capsys.readouterr().out
    assert "Cronometro avviato." in uscita
    assert "\n\rg1 00:00." in uscita
    assert "\n\rg2 00:00." in uscita and (" pv" in uscita or " pl" in uscita or " pu" in uscita)
    assert "\n\rg3 00:00." in uscita
    assert "\n\rfermato a 00:00." in uscita
    assert "Giro 1:" not in uscita
    assert "Statistiche di 3 giri." in uscita
    assert "\n\rtrascorso 00:00." in uscita and ", in pausa\r" in uscita
    assert "Riga del giro: g numero" in uscita
    assert "Cronometro ripreso." in uscita
    assert "Metti in pausa il cronometro prima di azzerarlo" in uscita
    assert "Oggi è" in uscita
    assert "Sono le" in uscita
    assert "Il programma gira da" in uscita
    assert "a: avvia il cronometro" in uscita
    assert "Tasto ! non previsto" in uscita
    assert "Tasto freccia su non previsto" in uscita
    assert "Report salvato in Meditimer-" in uscita
    assert "Arrivederci." in uscita
    report = [f for f in os.listdir(tmp_path) if f.startswith("Meditimer-")]
    assert len(report) == 1
    testo = (tmp_path / report[0]).read_text(encoding="utf-8")
    assert "Nota: la nota della prova." in testo
    assert "Giri registrati: 3." in testo
    assert "Giro 1: " in testo and "Giro 2: " in testo and "del precedente" in testo
    assert "\n\n" not in testo
    assert copione.suonati[:3] == ["avvio", "cronometro_avviato", "giro"]
    assert "tasto_sconosciuto" in copione.suonati
    assert copione.suonati[-1] == "chiusura"
    assert "-" * 3 not in uscita and "=" * 3 not in uscita


def test_azzera_salva_e_riparte(banco, tmp_path, capsys):
    banco(["a", _pausa(0.02), "s", "z", "c", "q"], ["nota di z"])
    assert meditimer.main() == 0
    uscita = capsys.readouterr().out
    assert "Cronometro azzerato." in uscita
    assert "Il cronometro non è mai partito" in uscita
    assert "Nessun dato del cronometro da salvare." in uscita
    assert len([f for f in os.listdir(tmp_path) if f.startswith("Meditimer-")]) == 1


def test_timer_che_suona_e_viene_zittito(banco, capsys):
    copione = banco(["x", _pausa(1.6), "l", "q"], ["1"])
    assert meditimer.main() == 0
    uscita = capsys.readouterr().out
    assert "Timer 1 di 1 secondo impostato, suonerà alle" in uscita
    assert "Timer 1 di 1 secondo concluso alle" in uscita
    assert "Suoneria zittita." in uscita
    assert "Nessun timer e nessuna sveglia in attesa." in uscita
    assert "allarme" in copione.suonati
    assert "allarme_zittito" in copione.suonati


def test_sveglia_elenco_e_annullamento(banco, capsys):
    copione = banco(["w", "x", "l", "l", "w", "x", "q"], ["+5", "2:30", "1", "", "ieri", "1:2:3:4"])
    assert meditimer.main() == 0
    uscita = capsys.readouterr().out
    assert "Sveglia 1 impostata alle" in uscita
    assert "Timer 2 di 2 minuti e 30 secondi impostato" in uscita
    assert "Sveglia 1, alle" in uscita and "mancano" in uscita
    assert "Sveglia 1 annullato." in uscita
    assert "Timer 2 di 2 minuti e 30 secondi, alle" in uscita
    assert "Orario non valido." in uscita
    assert "Durata non valida." in uscita
    assert copione.suonati.count("errore") == 2
    assert "annullato" in copione.suonati


def test_banco_di_prova_salva_archivio_e_report(banco, tmp_path, capsys, monkeypatch):
    prova = {
        "data": "2026-09-11T10:00:00",
        "versione": "3.0.0",
        "profilo": "breve",
        "python": "3.14.5",
        "scheda": {"nome_computer": "Finta", "processore": "Finto 9000", "processori_logici": 2},
        "cpu_multi": {
            t: {"op_s": v, "per_processo": [v / 2, v / 2], "durata": 5.0} for t, v in (("int", 100.0), ("float", 200.0), ("math", 50.0))
        },
        "cpu_singolo": {"int": 60.0, "float": 120.0, "math": 30.0},
        "memoria": {"singolo_gb_s": 10.0, "multi_gb_s": 15.0, "megabyte_singolo": 128, "megabyte_multi": 32, "processi": 2},
        "disco": {"scrittura_mb_s": 500.0, "lettura_mb_s": 900.0, "senza_cache": True, "megabyte": 128},
        "nota": "",
    }
    chiamate = []

    def esegui_finto(profilo, annuncia, segnale, annullato, cartella, versione, **k):
        chiamate.append((profilo, cartella, versione))
        annuncia("Fase 1 di 9: finta.")
        segnale("banco_fase")
        return dict(prova)

    monkeypatch.setattr(meditimer.banco_prova, "esegui", esegui_finto)
    copione = banco(["b", "b", "b", "\r", "n", "b", "\x1b", "q"], ["prima prova", "seconda prova"])
    assert meditimer.main() == 0
    uscita = capsys.readouterr().out
    assert chiamate == [("breve", str(tmp_path), "3.0.0"), ("normale", str(tmp_path), "3.0.0")]
    assert "Banco di prova, profilo breve: nove fasi, circa" in uscita
    assert "Banco di prova di Meditimer 3.0.0, profilo breve," in uscita
    assert "Macchina: Finta, Finto 9000, 2 processori logici." in uscita
    assert "Multi core: 100 op/s, prima prova di questa macchina." in uscita
    assert "Multi core: 100 op/s, come la prova precedente, il primato resta 100 op/s." in uscita
    assert "Prova salvata nell'archivio benchmark_results.json" in uscita
    assert "Report della prova salvato in benchmark-Finta-20260911-100000.txt" in uscita
    assert "Classifica multi core, una macchina" in uscita
    assert "Archivio: 2 prove di una macchina" in uscita
    assert "Banco di prova annullato." in uscita
    assert (tmp_path / "benchmark_results.json").exists()
    assert (tmp_path / "benchmark_results.json.bak").exists()
    testo = (tmp_path / "benchmark-Finta-20260911-100000.txt").read_text(encoding="utf-8")
    assert "Nota: seconda prova." in testo
    assert "Dettaglio per processo, calcoli su interi" in testo
    assert copione.suonati.count("banco_avvio") == 2
    assert copione.suonati.count("banco_concluso") == 2
    assert copione.suonati.count("banco_salvato") == 2
    assert copione.suonati.count("classifiche") == 1
    assert "primato_macchina" not in copione.suonati


def test_ctrl_c_esce_salvando(banco, tmp_path, capsys):
    banco(["a", _pausa(0.02), KeyboardInterrupt()], ["interrotta"])
    assert meditimer.main() == 0
    uscita = capsys.readouterr().out
    assert "Interrotto: salvo il report ed esco." in uscita
    assert len([f for f in os.listdir(tmp_path) if f.startswith("Meditimer-")]) == 1


def test_pulizia_dei_report_vecchi_all_avvio(banco, tmp_path, capsys):
    vecchio = tmp_path / "Meditimer-250101-120000.txt"
    vecchio.write_text("x", encoding="utf-8")
    remoto = time.time() - 400 * 86400
    os.utime(vecchio, (remoto, remoto))
    recente = tmp_path / "benchmark-X-20260901-120000.txt"
    recente.write_text("x", encoding="utf-8")
    copione = banco(["q"])
    assert meditimer.main() == 0
    uscita = capsys.readouterr().out
    assert "Cancellato un report più vecchio di un anno, Meditimer-250101-120000.txt." in uscita
    assert "\n\n" not in uscita.replace("\n\r", "\n")
    assert not vecchio.exists()
    assert recente.exists()
    assert copione.suonati[:2] == ["avvio", "pulizia"]


def test_senza_console_esce(banco, capsys):
    banco([EOFError()])
    assert meditimer.main() == 0
    assert "Nessuna console da cui leggere: esco." in capsys.readouterr().out


def test_il_manuale_e_l_aggiornamento(banco, capsys, monkeypatch):
    chiamate = []
    monkeypatch.setattr(meditimer, "manuale", lambda **k: chiamate.append(k) or True)
    banco(["m", "q"])
    assert meditimer.main() == 0
    assert chiamate[0]["nome"] == "Manuale di Meditimer"
    assert chiamate[0]["nf"].endswith("manuale.txt")
    monkeypatch.setattr(meditimer, "gestisci_aggiornamento", lambda *a, **k: True)
    copione = banco(["q"])
    assert meditimer.main() == 0
    assert copione.suonati == ["avvio", "chiusura"]


def test_la_suoneria_nel_thread_non_blocca_il_ciclo(banco, capsys):
    copione = banco(["x", _pausa(1.4), "d", "q"], ["1"])
    finito = threading.Event()

    def corri():
        meditimer.main()
        finito.set()

    threading.Thread(target=corri, daemon=True).start()
    assert finito.wait(10.0)
    uscita = capsys.readouterr().out
    assert "concluso alle" in uscita
    assert "Suoneria zittita." in uscita
    assert "Oggi è" in uscita
    assert copione.suonati.count("allarme") >= 1
