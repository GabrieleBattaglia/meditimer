# Meditimer, le classifiche: l'archivio dei banchi di prova, la cronologia per macchina e le graduatorie.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 11/09/2026: revisione 1. Il file cambia formato: ogni macchina tiene la
# cronologia delle sue prove invece di una voce sola sovrascritta; le voci
# della 2.9.1 si convertono al caricamento; il salvataggio passa da un file
# temporaneo e lascia una copia di riserva; le voci rotte si scartano
# contandole, invece di far cadere il programma con la sessione in corso.

"""L'archivio dei banchi di prova di Meditimer.

Il file benchmark_results.json tiene, per ogni macchina, la scheda con
processore e memoria e la cronologia delle prove. Il modulo lo legge, lo
scrive, ne ricava le classifiche fra le macchine e il confronto fra una
prova nuova e le precedenti della stessa macchina. Non stampa nulla: le
righe che restituisce sono gia' pensate per lo screen reader e per il
display braille, a blocchi di quaranta caratteri.
Ogni classifica ordina le macchine per la loro prova migliore. Le quattro
misure sono il multi core, un processore solo, la memoria e il disco: le
due del processore sono la media geometrica delle tre prove, interi,
decimali e funzioni matematiche, cosi' una macchina forte in una e debole
in un'altra non scavalca chi e' buona in tutte e tre.
"""

import json
import math
import os
from datetime import datetime

from formati import data_breve, formatta_numero_grande, numero_it, percentuale_it, riga_blocchi

FORMATO = 2
NOME_FILE = "benchmark_results.json"
PROVE_CPU = ("int", "float", "math")
SIGLE_CPU = {"int": "int", "float": "dec", "math": "mat"}
NOMI_CPU = {"int": "interi", "float": "decimali", "math": "funzioni matematiche"}
METRICHE = (("multi", "multi core"), ("singolo", "un processore"), ("memoria", "memoria"), ("disco", "disco"))
ORDINALI = ["prima", "seconda", "terza", "quarta", "quinta", "sesta", "settima", "ottava", "nona", "decima"]


def vuoto():
    return {"formato": FORMATO, "macchine": {}}


def _numero(valore):
    """Un numero finito e positivo, oppure None."""
    if isinstance(valore, bool) or not isinstance(valore, (int, float)):
        return None
    if not math.isfinite(valore) or valore <= 0:
        return None
    return float(valore)


def _data_valida(testo):
    if not isinstance(testo, str):
        return False
    try:
        datetime.fromisoformat(testo)
    except ValueError:
        return False
    return True


def _pulisci_cpu(sezione, con_dettaglio):
    """Le tre prove del processore, oppure None se ne manca una o non e' un numero."""
    if not isinstance(sezione, dict):
        return None
    pulita = {}
    for tipo in PROVE_CPU:
        voce = sezione.get(tipo)
        if con_dettaglio:
            if not isinstance(voce, dict):
                return None
            op_s = _numero(voce.get("op_s"))
            if op_s is None:
                return None
            nuova = {"op_s": op_s}
            per_processo = voce.get("per_processo")
            if isinstance(per_processo, list):
                numeri = [_numero(v) for v in per_processo]
                if all(n is not None for n in numeri):
                    nuova["per_processo"] = numeri
            durata = _numero(voce.get("durata"))
            if durata is not None:
                nuova["durata"] = durata
            pulita[tipo] = nuova
        else:
            op_s = _numero(voce)
            if op_s is None:
                return None
            pulita[tipo] = op_s
    return pulita


def _pulisci_numeri(sezione, chiavi):
    """Un dizionario con i soli numeri validi fra le chiavi date, oppure None se e' vuoto."""
    if not isinstance(sezione, dict):
        return None
    pulita = {}
    for chiave in chiavi:
        valore = _numero(sezione.get(chiave))
        if valore is not None:
            pulita[chiave] = valore
    for chiave, valore in sezione.items():
        if chiave not in chiavi and isinstance(valore, (bool, int, str)):
            pulita[chiave] = valore
    return pulita or None


def prova_valida(prova):
    """La prova ripulita, oppure None se non ha il minimo per stare in archivio.

    Il minimo e' una data leggibile e le tre prove del multi core, che sono
    l'unica cosa che ogni versione del programma ha sempre misurato. Il
    resto, un processore, memoria, disco, sensori e scheda, si tiene se e'
    fatto bene e si lascia cadere se non lo e'.
    """
    if not isinstance(prova, dict) or not _data_valida(prova.get("data")):
        return None
    cpu_multi = _pulisci_cpu(prova.get("cpu_multi"), con_dettaglio=True)
    if cpu_multi is None:
        return None
    pulita = {
        "data": prova["data"],
        "versione": str(prova.get("versione", "")),
        "profilo": str(prova.get("profilo", "")),
        "python": str(prova.get("python", "")),
        "scheda": prova["scheda"] if isinstance(prova.get("scheda"), dict) else {},
        "cpu_multi": cpu_multi,
        "nota": str(prova.get("nota") or ""),
    }
    cpu_singolo = _pulisci_cpu(prova.get("cpu_singolo"), con_dettaglio=False)
    if cpu_singolo is not None:
        pulita["cpu_singolo"] = cpu_singolo
    memoria = _pulisci_numeri(prova.get("memoria"), ("singolo_gb_s", "multi_gb_s"))
    if memoria and ("singolo_gb_s" in memoria or "multi_gb_s" in memoria):
        pulita["memoria"] = memoria
    disco = _pulisci_numeri(prova.get("disco"), ("scrittura_mb_s", "lettura_mb_s"))
    if disco and "scrittura_mb_s" in disco and "lettura_mb_s" in disco:
        pulita["disco"] = disco
    if isinstance(prova.get("sensori"), dict):
        pulita["sensori"] = prova["sensori"]
    return pulita


def _normalizza(grezzo):
    dati = vuoto()
    scartate = 0
    macchine = grezzo.get("macchine")
    if not isinstance(macchine, dict):
        return dati, "Archivio delle prove malformato, riparto da vuoto."
    for nome, voce in macchine.items():
        if not isinstance(voce, dict) or not isinstance(voce.get("prove"), list):
            scartate += 1
            continue
        prove = []
        for prova in voce["prove"]:
            pulita = prova_valida(prova)
            if pulita is None:
                scartate += 1
            else:
                prove.append(pulita)
        if not prove:
            continue
        scheda = voce.get("scheda") if isinstance(voce.get("scheda"), dict) else {}
        dati["macchine"][str(nome)] = {"scheda": scheda, "prove": prove}
    avviso = ""
    if scartate:
        avviso = f"Scartate {scartate} voci incomplete dell'archivio delle prove."
    return dati, avviso


def _converti_formato_1(grezzo):
    """Il file della 2.9.1: una voce per macchina con le tre velocita' e basta."""
    dati = vuoto()
    convertite = scartate = 0
    for nome, voce in grezzo.items():
        if not isinstance(voce, dict) or not isinstance(voce.get("test"), dict):
            scartate += 1
            continue
        cpu_multi = {}
        for tipo in PROVE_CPU:
            op_s = _numero(voce["test"].get(tipo, {}).get("performance_totale") if isinstance(voce["test"].get(tipo), dict) else None)
            if op_s is not None:
                cpu_multi[tipo] = {"op_s": op_s}
        python = str(voce.get("info_python") or "")
        scheda = {"nome_computer": str(nome), "python": python}
        if isinstance(voce.get("num_core"), int) and not isinstance(voce.get("num_core"), bool):
            scheda["processori_logici"] = voce["num_core"]
        prova = prova_valida(
            {
                "data": voce.get("data_test"),
                "versione": "2.9.1",
                "profilo": "normale",
                "python": python,
                "scheda": scheda,
                "cpu_multi": cpu_multi,
                "nota": voce.get("nota_utente") or "",
            }
        )
        if prova is None:
            scartate += 1
            continue
        dati["macchine"][str(nome)] = {"scheda": scheda, "prove": [prova]}
        convertite += 1
    avviso = f"Archivio delle prove convertito dal formato della versione 2.9.1: {convertite} prove."
    if scartate:
        avviso += f" Scartate {scartate} voci incomplete."
    if not convertite and not scartate:
        avviso = ""
    return dati, avviso


def carica(percorso):
    """Legge l'archivio. Restituisce la coppia (dati, avviso) e non solleva mai.

    Un file assente e' un archivio vuoto senza avviso. Un file illeggibile,
    o in un formato sconosciuto, e' un archivio vuoto con l'avviso che lo
    dice: al primo salvataggio la copia di riserva conservera' comunque il
    file com'era.
    """
    if not os.path.isfile(percorso):
        return vuoto(), ""
    try:
        with open(percorso, encoding="utf-8") as f:
            grezzo = json.load(f)
    except (OSError, ValueError) as e:
        return vuoto(), f"Archivio delle prove illeggibile, riparto da vuoto: {e}."
    if not isinstance(grezzo, dict):
        return vuoto(), "Archivio delle prove malformato, riparto da vuoto."
    if "formato" not in grezzo:
        return _converti_formato_1(grezzo)
    if grezzo.get("formato") != FORMATO:
        return vuoto(), f"Archivio delle prove in un formato sconosciuto, {grezzo.get('formato')!r}: riparto da vuoto."
    return _normalizza(grezzo)


def salva(percorso, dati):
    """Scrive l'archivio passando da un file temporaneo e lasciando la copia .bak. Solleva OSError."""
    temporaneo = percorso + ".tmp"
    with open(temporaneo, "w", encoding="utf-8") as f:
        json.dump(dati, f, indent=4, ensure_ascii=False)
    if os.path.exists(percorso):
        os.replace(percorso, percorso + ".bak")
    os.replace(temporaneo, percorso)


def registra_prova(dati, nome, prova):
    """Aggiunge una prova alla cronologia della macchina e ne aggiorna la scheda."""
    voce = dati["macchine"].setdefault(str(nome), {"scheda": {}, "prove": []})
    if isinstance(prova.get("scheda"), dict) and prova["scheda"]:
        voce["scheda"] = dict(prova["scheda"])
    voce["prove"].append(prova)


def prove_di(dati, nome):
    return list(dati["macchine"].get(str(nome), {}).get("prove", []))


def _media_geometrica(valori):
    return math.exp(sum(math.log(v) for v in valori) / len(valori))


def valore(prova, metrica):
    """Il numero con cui la prova entra nella classifica di quella misura, oppure None."""
    if metrica == "multi":
        return _media_geometrica([prova["cpu_multi"][t]["op_s"] for t in PROVE_CPU])
    if metrica == "singolo":
        singolo = prova.get("cpu_singolo")
        return _media_geometrica([singolo[t] for t in PROVE_CPU]) if singolo else None
    if metrica == "memoria":
        memoria = prova.get("memoria")
        if not memoria:
            return None
        return memoria.get("multi_gb_s") or memoria.get("singolo_gb_s")
    if metrica == "disco":
        disco = prova.get("disco")
        if not disco:
            return None
        return (disco["scrittura_mb_s"] + disco["lettura_mb_s"]) / 2
    raise ValueError(f"misura sconosciuta: {metrica}")


def formatta_valore(metrica, v):
    if metrica in ("multi", "singolo"):
        return formatta_numero_grande(v, "op/s")
    if metrica == "memoria":
        return f"{numero_it(v, 1)} GB/s"
    return f"{numero_it(v, 0)} MB/s"


def dettaglio(prova, metrica):
    """Il terzo blocco della riga di classifica: le parti da cui nasce il numero."""
    if metrica == "multi":
        return ", ".join(f"{SIGLE_CPU[t]} {formatta_numero_grande(prova['cpu_multi'][t]['op_s'], '')}" for t in PROVE_CPU)
    if metrica == "singolo":
        return ", ".join(f"{SIGLE_CPU[t]} {formatta_numero_grande(prova['cpu_singolo'][t], '')}" for t in PROVE_CPU)
    if metrica == "memoria":
        memoria = prova["memoria"]
        parti = []
        if "singolo_gb_s" in memoria:
            parti.append(f"un core {numero_it(memoria['singolo_gb_s'], 1)}")
        if "multi_gb_s" in memoria:
            parti.append(f"tutti {numero_it(memoria['multi_gb_s'], 1)}")
        return ", ".join(parti) + " GB/s"
    disco = prova["disco"]
    return f"scrittura {numero_it(disco['scrittura_mb_s'], 0)}, lettura {numero_it(disco['lettura_mb_s'], 0)} MB/s"


def migliore(prove, metrica):
    """La prova migliore in quella misura e il suo valore, oppure (None, None)."""
    scelta, massimo = None, None
    for prova in prove:
        v = valore(prova, metrica)
        if v is not None and (massimo is None or v > massimo):
            scelta, massimo = prova, v
    return massimo, scelta


def classifica(dati, metrica):
    """Le macchine ordinate dalla piu' veloce, ognuna con la sua prova migliore."""
    voci = []
    for nome, voce in dati["macchine"].items():
        v, prova = migliore(voce["prove"], metrica)
        if prova is not None:
            voci.append((nome, v, prova))
    voci.sort(key=lambda x: x[1], reverse=True)
    return voci


def posizione(dati, metrica, nome):
    """La posizione della macchina in quella classifica e quante macchine ci sono."""
    voci = classifica(dati, metrica)
    for i, (n, _, _) in enumerate(voci, 1):
        if n == nome:
            return i, len(voci)
    return None, len(voci)


def _data(prova):
    return datetime.fromisoformat(prova["data"])


def righe_classifica(dati, metrica, etichetta, massimo=30):
    voci = classifica(dati, metrica)
    if not voci:
        return [f"Classifica {etichetta}: nessuna prova in archivio."]
    quante = "una macchina" if len(voci) == 1 else f"{len(voci)} macchine"
    righe = [f"Classifica {etichetta}, {quante}, ordinate per la prova migliore di ciascuna."]
    for i, (nome, v, prova) in enumerate(voci[:massimo], 1):
        righe.append(riga_blocchi(f"{i}. {nome}, {data_breve(_data(prova))}", formatta_valore(metrica, v), dettaglio(prova, metrica)))
    return righe


def righe_archivio(dati):
    """Due conti sull'archivio, per chi ama le statistiche."""
    macchine = dati["macchine"]
    prove = [p for voce in macchine.values() for p in voce["prove"]]
    if not prove:
        return ["Archivio delle prove vuoto: premi b per fare la prima."]
    date = sorted(_data(p) for p in prove)
    quante_prove = "una prova" if len(prove) == 1 else f"{len(prove)} prove"
    quante_macchine = "una macchina" if len(macchine) == 1 else f"{len(macchine)} macchine"
    righe = [f"Archivio: {quante_prove} di {quante_macchine}, dalla prima del {data_breve(date[0])} all'ultima del {data_breve(date[-1])}."]
    voci = classifica(dati, "multi")
    if len(voci) >= 2:
        prima, ultima = voci[0], voci[-1]
        rapporto = prima[1] / ultima[1]
        righe.append(
            f"Nel multi core {prima[0]} fa {formatta_numero_grande(prima[1])}, {ultima[0]} ne fa {formatta_numero_grande(ultima[1])}: "
            f"un rapporto di {numero_it(rapporto, 1)} a 1."
        )
    nome_top, voce_top = max(macchine.items(), key=lambda kv: len(kv[1]["prove"]))
    if len(voce_top["prove"]) >= 2:
        righe.append(f"La macchina con più prove è {nome_top}, con {len(voce_top['prove'])}.")
    return righe


def righe_classifiche(dati):
    """Tutte le classifiche, una dopo l'altra, e i conti sull'archivio."""
    righe = []
    for metrica, etichetta in METRICHE:
        righe.extend(righe_classifica(dati, metrica, etichetta))
    righe.extend(righe_archivio(dati))
    return righe


def righe_confronto(dati, nome, prova):
    """Il confronto della prova con le precedenti della stessa macchina.

    Restituisce le righe e un vero se la prova e' un primato della macchina
    in almeno una misura, avendo almeno una prova precedente con cui
    confrontarsi: la prima prova di una macchina non e' un primato.
    """
    altre = [p for p in prove_di(dati, nome) if p is not prova]
    precedente = max(altre, key=_data) if altre else None
    righe = []
    primato = False
    for metrica, etichetta in METRICHE:
        v = valore(prova, metrica)
        if v is None:
            continue
        testo = f"{etichetta[0].upper()}{etichetta[1:]}: {formatta_valore(metrica, v)}"
        v_prec = valore(precedente, metrica) if precedente is not None else None
        v_migliore, _ = migliore(altre, metrica)
        if v_prec is not None:
            delta = (v - v_prec) / v_prec * 100.0
            if abs(delta) < 0.05:
                testo += ", come la prova precedente"
            else:
                testo += f", {percentuale_it(abs(delta))} {'più' if delta > 0 else 'meno'} della prova precedente"
        if v_migliore is None:
            testo += ", prima prova di questa macchina"
        elif v > v_migliore:
            testo += ", nuovo primato di questa macchina"
            primato = True
        else:
            testo += f", il primato resta {formatta_valore(metrica, v_migliore)}"
        righe.append(testo + ".")
    for metrica, etichetta in METRICHE:
        pos, totale = posizione(dati, metrica, nome)
        if pos is None or totale < 2:
            continue
        ordinale = ORDINALI[pos - 1] if pos <= len(ORDINALI) else f"numero {pos}"
        righe.append(f"In classifica {etichetta} questa macchina è {ordinale} su {totale}.")
    return righe, primato
