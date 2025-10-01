# Meditimer L'affetta tempo
# Data concepimento: 05/11/2015 11:51 by Gabriele Battaglia
# Porting Python 3.6: 23/11/2017.
# Inizio restyling 10/02/2022
# Restyling con ChatGPT4o il 16 luglio 2024
# Aggiunta Classifiche Benchmark by Partner di Programmazione il 01/10/2025

import time, datetime, sys, os, socket, math, multiprocessing, json, threading

try:
    # Windows
    import msvcrt
    def kbhit():
        return msvcrt.kbhit()
    def getch():
        ch = msvcrt.getch()
        # Se il byte è un prefisso per tasti speciali (es. frecce, F1-F12),
        # leggiamo anche il secondo byte per pulire il buffer di input
        # e restituiamo una stringa vuota per ignorare l'input.
        if ch in (b'\x00', b'\xe0'):
            msvcrt.getch()
            return ''
        try:
            # Altrimenti, proviamo a decodificare il byte come un carattere normale.
            return ch.decode('utf-8').lower()
        except UnicodeDecodeError:
            # Se la decodifica fallisce per qualsiasi altro motivo, ignoriamo l'input.
            return ''
except ImportError:
    # Unix-like (nessuna modifica necessaria qui, ma il codice resta per compatibilità)
    import termios
    import tty
    import select
    def kbhit():
        return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])
    def getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch.lower()
VERSIONE = "2.5.2 di ottobre 2025"
MNMENU={'a':'per avviare/pausa',
  's':'Per fermare',
  'z':'Per azzerare',
  'g':'Per registrare un giro',
  'd':'Per mostrare la data',
  'o':"Per mostrare l'ora",
  'x':'Per impostare un timer',
  'w':'Per impostare una sveglia',
  'c':'Per tempo trascorso',
  'v':'Per tempo complessivo di esecuzione',
  'b':'Per eseguire un test di velocità della macchina',
  'n':'Per mostrare le classifiche dei benchmark',
  'q':'Per uscire e salvare il report',
  '?':'Per mostrare questo aiuto'}
GIORNISETTIMANA = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
MESIANNO = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
TINIZIO = time.time()
NOME_FILE_JSON = "benchmark_results.json" # Nome del file per i risultati del benchmark

def stringa_tempo_descrittiva(t):
    """
    Riceve un tempo in secondi e rende una stringa descrittiva
    mostrando solo le parti non nulle (es. "1 minuto, 15 secondi e 321 millisecondi").
    """
    millis = int((t - int(t)) * 1000)
    seconds = int(t) % 60
    minutes = (int(t) // 60) % 60
    hours = (int(t) // 3600)

    parti = []
    if hours > 0:
        parti.append(f"{hours} {'ora' if hours == 1 else 'ore'}")
    if minutes > 0:
        parti.append(f"{minutes} {'minuto' if minutes == 1 else 'minuti'}")
    if seconds > 0:
        parti.append(f"{seconds} {'secondo' if seconds == 1 else 'secondi'}")
    if millis > 0:
        parti.append(f"{millis} {'millisecondo' if millis == 1 else 'millisecondi'}")
    
    if not parti:
        return "0 secondi"

    if len(parti) > 1:
        return ", ".join(parti[:-1]) + " e " + parti[-1]
    else:
        return parti[0]

class Stopwatch:
    def __init__(self):
        self.reset()

    def reset(self):
        self._start_time = 0.0
        self._pause_time = 0.0
        self._total_pause_time = 0.0
        self._running = False
        self._laps = []
        self._last_lap_time = 0.0
        print("\nCronometro azzerato!", end="", flush=True)

    def start_pause(self):
        if not self._running:
            self._running = True
            if self._start_time == 0.0:
                self._start_time = time.time()
                self._last_lap_time = self._start_time
                print("\nCronometro avviato!", end="", flush=True)
            else:
                pause_duration = time.time() - self._pause_time
                self._total_pause_time += pause_duration
                print("\nCronometro ripreso!", end="", flush=True)
        else:
            self._running = False
            self._pause_time = time.time()
            print("\nCronometro in pausa!", end="", flush=True)

    def stop(self):
        if self._running:
            self.start_pause()
        print("\nCronometro fermato!", end="", flush=True)

    def record_lap(self):
        if not self._running:
            return
        now = time.time()
        lap_time = now - self._last_lap_time
        self._last_lap_time = now
        self._laps.append(lap_time)
        numero_giro = len(self._laps)
        print(f"\nGiro {numero_giro} registrato: {stringa_tempo_descrittiva(lap_time)}", end=" ", flush=True)
        if len(self._laps) > 1:
            if lap_time == min(self._laps):
                print("(giro più veloce)", end="", flush=True)
            elif lap_time == max(self._laps):
                print("(giro più lento)", end="", flush=True)

    def get_elapsed_time(self):
        if self._start_time == 0.0:
            return 0.0
        if not self._running:
            return self._pause_time - self._start_time - self._total_pause_time
        return time.time() - self._start_time - self._total_pause_time

    @property
    def laps(self):
        return self._laps

    @property
    def is_running(self):
        return self._running

def mostra_data_attuale():
    now = datetime.datetime.now()
    giorno_settimana = GIORNISETTIMANA[now.weekday()]
    giorno = now.day
    mese = MESIANNO[now.month - 1]
    anno = now.year
    giorno_dell_anno = now.timetuple().tm_yday
    print(f"\nData: {giorno_settimana}, {giorno} {mese} {anno}, giorno {giorno_dell_anno} dell'anno",end="",flush=True)

def mostra_ora_attuale():
    print(f"\nOre: {datetime.datetime.now().strftime('%H:%M:%S')}",end="",flush=True)

def tempo_complessivo_esecuzione():
    return time.time() - TINIZIO

def salva_report(stopwatch):
    giri = stopwatch.laps
    tempo_trascorso = stopwatch.get_elapsed_time()
    if not giri and tempo_trascorso == 0:
        print("\nNessun dato del cronometro da salvare. Uscita senza report.")
        return  # Esce immediatamente dalla funzione
    tempo_complessivo = tempo_complessivo_esecuzione()
    filename = f"Meditimer-{datetime.datetime.now().strftime('%y%m%d-%H%M')}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"Report Meditimer versione {VERSIONE}\n")
        f.write(f"Creato il {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        if giri:
            f.write("\nGiri registrati:\n")
            for i, giro in enumerate(giri):
                giro_str = stringa_tempo_descrittiva(giro)
                if giro == min(giri):
                    giro_str += " (Giro più veloce)"
                elif giro == max(giri):
                    giro_str += " (Giro più lento)"
                f.write(f"  Giro {i+1}: {giro_str}\n")
            f.write(f"\nGiro più veloce: {stringa_tempo_descrittiva(min(giri))}\n")
            f.write(f"Giro più lento: {stringa_tempo_descrittiva(max(giri))}\n")
            f.write(f"Tempo medio: {stringa_tempo_descrittiva(sum(giri) / len(giri))}\n")
            if sum(giri) > 0:
                f.write(f"\nTempo totale dei giri: {stringa_tempo_descrittiva(sum(giri))}\n")
        if tempo_trascorso > 0:
            f.write(f"Tempo totale trascorso: {stringa_tempo_descrittiva(tempo_trascorso)}\n")
        if tempo_complessivo > 0:
            f.write(f"Tempo complessivo di esecuzione: {stringa_tempo_descrittiva(tempo_complessivo)}\n")
    print(f"\nReport salvato in {filename}")

def mostra_aiuto():
    print("\nComandi disponibili:")
    for key, desc in MNMENU.items():
        print(f"\t'{key}': {desc}")

def formatta_numero_grande(n, suffisso='op/s'):
    """Formatta un numero grande con prefissi metrici (K, M, G, T)."""
    if n == 0:
        return f"0 {suffisso}"
    for unita in ['', 'K', 'M', 'G', 'T']:
        if abs(n) < 1000.0:
            return f"{float(f'{n:.3g}'):g} {unita}{suffisso}".replace(",", ".")
        n /= 1000.0
    return f"{n:,.2f} P{suffisso}".replace(",", ".")

def benchmark_worker(durata, tipo_test):
    operazioni = 0
    start_time = time.perf_counter()
    if tipo_test == 'int':
        while (time.perf_counter() - start_time) < durata:
            for i in range(1000):
                risultato = (i * i * 2 + 15) // 3
            operazioni += 1000
    elif tipo_test == 'float':
        while (time.perf_counter() - start_time) < durata:
            for i in range(1000):
                risultato_float = (float(i) * 3.14159) / 2.71828
            operazioni += 1000
    elif tipo_test == 'math':
        while (time.perf_counter() - start_time) < durata:
            for i in range(1, 1001):
                risultato_mat = math.sqrt(i) + math.sin(i/100.0)
            operazioni += 1000
    return operazioni

def salva_risultati_benchmark(risultati):
    """
    Salva i risultati del benchmark in un file JSON.
    Se il file esiste, aggiorna i dati; altrimenti, ne crea uno nuovo.
    """
    try:
        try:
            with open(NOME_FILE_JSON, 'r', encoding='utf-8') as f:
                dati = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            dati = {} # Se il file non esiste o è vuoto, crea un dizionario vuoto

        # Aggiorna o aggiunge il risultato del computer corrente
        dati[risultati['nome_computer']] = risultati

        with open(NOME_FILE_JSON, 'w', encoding='utf-8') as f:
            json.dump(dati, f, indent=4)
        print(f"\nRisultati del benchmark salvati in {NOME_FILE_JSON}")

    except IOError as e:
        print(f"\nErrore durante il salvataggio del file JSON: {e}")

def esegui_benchmark_multicore():
    print("\n\n-- Inizio Test di Velocità Multi-Core (3 Fasi) --")
    
    DURATA_PER_TEST = 10.0
    num_core = os.cpu_count() or 1

    print(f"Rilevati {num_core} core. Verranno eseguiti 3 test da {DURATA_PER_TEST} secondi ciascuno.")
    print("Non usare il computer durante l'analisi per risultati più accurati.")

    nome_computer = socket.gethostname()
    data_e_ora = datetime.datetime.now()
    info_python = sys.version

    report_testo = [f"--- Report Test di Velocità Multi-Core (3 Fasi) ---"]
    report_testo.append(f"Nome Computer: {nome_computer}")
    report_testo.append(f"Data e Ora: {data_e_ora.strftime('%Y-%m-%d %H:%M:%S')}")
    report_testo.append(f"Versione Python: {info_python.splitlines()[0]}")

    # Dizionario per salvare i dati strutturati per il JSON
    risultati_json = {
        "nome_computer": nome_computer,
        "data_test": data_e_ora.isoformat(),
        "info_python": info_python.splitlines()[0],
        "num_core": num_core,
        "test": {}
    }

    tipi_di_test = [
        ('Calcoli su Interi', 'int'),
        ('Calcoli su Float', 'float'),
        ('Funzioni Matematiche', 'math')
    ]

    with multiprocessing.Pool(processes=num_core) as pool:
        for i, (nome_test, tipo) in enumerate(tipi_di_test):
            print(f"\n-- Fase {i+1}/3: {nome_test}... --")
            
            start_time = time.perf_counter()
            args = [(DURATA_PER_TEST, tipo)] * num_core
            risultati_per_core = pool.starmap(benchmark_worker, args)
            end_time = time.perf_counter()
            
            tempo_effettivo = end_time - start_time
            
            report_testo.append("-" * 40)
            report_testo.append(f"RISULTATI FASE: {nome_test}")
            report_testo.append(f"Durata effettiva: {tempo_effettivo:.4f} secondi")

            totale_operazioni = sum(risultati_per_core)
            performance_totale = totale_operazioni / tempo_effettivo
            
            # Aggiungi i risultati al report di testo
            report_testo.append(f"  Performance Totale: {formatta_numero_grande(performance_totale, 'op/s')} ({performance_totale:,.0f} op/s)")
            report_testo.append("  Performance per Core:")
            
            for core_idx, res_core in enumerate(risultati_per_core):
                perf_core = res_core / tempo_effettivo
                report_testo.append(f"    Core {core_idx+1:<2}: {formatta_numero_grande(perf_core, 'op/s')} ({perf_core:,.0f} op/s)")

            # Aggiungi i risultati al dizionario per il JSON
            risultati_json["test"][tipo] = {
                "nome_test": nome_test,
                "performance_totale": performance_totale
            }

    report_testo.append("-" * 40)
    report_testo.append("Nota: RAM e GPU non possono essere misurate con precisione usando solo librerie standard di Python.")
    
    report_completo = "\n".join(report_testo)
    print("\n" + report_completo)

    print("\nPuoi aggiungere una nota personale al report.")
    nota_utente = input("Inserisci la nota e premi Invio (lascia vuoto per nessuna nota): ")
    if nota_utente:
        report_testo.append("\n--- Nota dell'Utente ---")
        report_testo.append(nota_utente)
        risultati_json["nota_utente"] = nota_utente # Aggiungi la nota al JSON
    else:
        risultati_json["nota_utente"] = ""

    # Salva il report di testo
    try:
        filename = f"benchmark-multicore-{nome_computer}-{data_e_ora.strftime('%Y%m%d-%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_testo))
        print(f"\nReport di benchmark salvato con successo nel file: {filename}")
    except IOError as e:
        print(f"\nErrore: Impossibile salvare il file di report. Dettagli: {e}")

    # Salva i risultati nel file JSON
    salva_risultati_benchmark(risultati_json)

    print("\nPremi un tasto per tornare al menu principale.")

def mostra_classifiche():
    """
    Legge i dati dal file JSON e mostra le classifiche per ogni tipo di test.
    """
    try:
        with open(NOME_FILE_JSON, 'r', encoding='utf-8') as f:
            dati = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("\nNessun dato di benchmark trovato. Esegui prima un test con 'b'.")
        return

    print("\n--- Classifiche Benchmark ---")
    
    tipi_di_test = ['int', 'float', 'math']
    nomi_test = {
        'int': 'Calcoli su Interi',
        'float': 'Calcoli su Float',
        'math': 'Funzioni Matematiche'
    }

    for tipo in tipi_di_test:
        print(f"\n--- Classifica: {nomi_test[tipo]} ---")
        
        # Crea una lista di computer che hanno eseguito questo test
        classifica = []
        for nome_computer, risultati in dati.items():
            if 'test' in risultati and tipo in risultati['test']:
                classifica.append({
                    "nome_computer": nome_computer,
                    "velocita": risultati['test'][tipo]['performance_totale'],
                    "data": risultati['data_test'],
                    "nota": risultati.get('nota_utente', '')
                })
        
        # Ordina la classifica dalla velocità più alta alla più bassa
        classifica_ordinata = sorted(classifica, key=lambda x: x['velocita'], reverse=True)

        # Mostra i risultati
        if not classifica_ordinata:
            print("Nessun dato disponibile per questo tipo di test.")
            continue
        
        print(f"{'Pos.':<5} {'Nome Computer':<25} {'Velocità (op/s)':<20} {'Data Test':<20} {'Nota':<30}")
        print("-" * 100)

        for i, entry in enumerate(classifica_ordinata[:30]): # Mostra solo i primi 30
            pos = f"{i+1}."
            nome = entry['nome_computer'][:23]
            velocita_str = formatta_numero_grande(entry['velocita'], 'op/s')
            data_str = datetime.datetime.fromisoformat(entry['data']).strftime('%d/%m/%Y %H:%M')
            nota_str = entry['nota'][:28]
            
            print(f"{pos:<5} {nome:<25} {velocita_str:<20} {data_str:<20} {nota_str:<30}")

    print("\nPremi un tasto per tornare al menu principale.")

def parse_time_input(input_str):
    """
    Interpreta una stringa come "h:m:s", "m:s" o "s" e la converte in secondi totali.
    Restituisce il numero di secondi o None se l'input non è valido.
    """
    try:
        parts = [int(p) for p in input_str.strip().split(':')]
        parts.reverse()  # Lavoriamo da secondi a ore
        
        seconds = parts[0] if len(parts) > 0 else 0
        minutes = parts[1] if len(parts) > 1 else 0
        hours = parts[2] if len(parts) > 2 else 0
        
        if seconds < 0 or minutes < 0 or hours < 0:
            return None

        return hours * 3600 + minutes * 60 + seconds
    except (ValueError, IndexError):
        # Se la conversione a int fallisce o il formato non è corretto
        return None

def suona_allarme():
    """
    Mostra un messaggio di conclusione con data/ora ed esegue la sequenza di beep.
    """
    now = datetime.datetime.now()
    giorno_settimana = GIORNISETTIMANA[now.weekday()]
    data_str = now.strftime('%d/%m/%Y')
    ora_str = now.strftime('%H:%M:%S')

    # Messaggio di conclusione che include data e ora
    print(f"\n\n-- SVEGLIA/TIMER CONCLUSO --")
    print(f"Alle ore {ora_str} di {giorno_settimana} {data_str}", flush=True)

    # Sequenza di beep
    pausa_tra_beep = 2.5
    pausa_tra_serie = 5.0

    for _ in range(3):
        for _ in range(5):
            print('\a', end='', flush=True)
            time.sleep(pausa_tra_beep)
        time.sleep(pausa_tra_serie)
def timer_worker(durata_secondi):
    """
    Questa è la funzione che viene eseguita in un thread separato.
    Attende per la durata specificata e poi suona l'allarme.
    """
    orario_fine = datetime.datetime.now() + datetime.timedelta(seconds=durata_secondi)
    print(f"\nTimer impostato per {stringa_tempo_descrittiva(durata_secondi)}. L'allarme suonerà alle {orario_fine.strftime('%H:%M:%S')}.", end="", flush=True)
    
    # Il thread semplicemente "dorme" per il numero di secondi richiesto.
    # Questo è molto efficiente e non consuma CPU.
    time.sleep(durata_secondi)
    
    # Una volta terminata l'attesa, suona l'allarme.
    suona_allarme()

def imposta_timer():
    """
    Chiede all'utente la durata del timer, interpreta l'input
    e avvia il thread del timer in background.
    """
    input_str = input("\nImposta durata (formati: ore:min:sec, min:sec, oppure solo sec): ")
    if not input_str:
        print("\nOperazione annullata.", end="", flush=True)
        return

    secondi_totali = parse_time_input(input_str)

    if secondi_totali is None or secondi_totali <= 0:
        print("\nFormato non valido o durata nulla. Riprova.", end="", flush=True)
        return

    # Creiamo il thread.
    # 'target' è la funzione da eseguire (il nostro worker).
    # 'args' sono gli argomenti da passare a quella funzione.
    # 'daemon=True' è la magia: assicura che il thread si chiuda con il programma.
    timer_thread = threading.Thread(target=timer_worker, args=(secondi_totali,), daemon=True)
    
    # Avviamo il thread, che inizierà a eseguire timer_worker in background.
    timer_thread.start()
# --- NUOVE FUNZIONI PER LA SVEGLIA ---

def parse_time_alarm(input_str):
    """
    Interpreta un orario come "H:M:S" o "M:S" e calcola i secondi
    mancanti da ora fino a quell'orario (per oggi o domani).
    """
    try:
        parts = [int(p) for p in input_str.strip().split(':')]
        now = datetime.datetime.now()

        # Imposta i valori di default per l'orario di oggi
        hour, minute, second = now.hour, now.minute, now.second

        # Aggiorna in base all'input dell'utente
        if len(parts) == 1: # Formato M
             minute, second = parts[0], 0
        elif len(parts) == 2: # Formato M:S
            minute, second = parts[0], parts[1]
        elif len(parts) == 3: # Formato H:M:S
            hour, minute, second = parts[0], parts[1], parts[2]
        else:
            return None, None
            
        # Crea l'oggetto datetime per l'orario della sveglia di oggi
        target_time = now.replace(hour=hour, minute=minute, second=second, microsecond=0)

        # Se l'orario è già passato oggi, imposta la sveglia per domani
        if target_time < now:
            target_time += datetime.timedelta(days=1)
            
        # Calcola i secondi totali di attesa
        wait_seconds = (target_time - now).total_seconds()
        
        return wait_seconds, target_time

    except (ValueError, IndexError):
        return None, None

def alarm_worker(durata_secondi):
    """
    Funzione eseguita dal thread della sveglia. Attende e suona.
    È quasi identica a timer_worker, ma la teniamo separata per chiarezza.
    """
    time.sleep(durata_secondi)
    suona_allarme()

def imposta_sveglia():
    """
    Chiede all'utente l'orario della sveglia e avvia il thread.
    """
    input_str = input("\nImposta orario sveglia (formati: H:M:S, M:S o M): ")
    if not input_str:
        print("\nOperazione annullata.", end="", flush=True)
        return

    secondi_attesa, orario_sveglia = parse_time_alarm(input_str)

    if secondi_attesa is None or secondi_attesa <= 0:
        print("\nFormato non valido. Riprova.", end="", flush=True)
        return

    print(f"\nSveglia impostata per le {orario_sveglia.strftime('%H:%M:%S del %d/%m/%Y')}.", end="", flush=True)
    
    # Creiamo e avviamo il thread della sveglia, esattamente come per il timer
    alarm_thread = threading.Thread(target=alarm_worker, args=(secondi_attesa,), daemon=True)
    alarm_thread.start()

def main():
    print(f"Meditimer - (L'AFFETTA TEMPO), versione {VERSIONE} by Gabriele Battaglia (IZ4APU).\n\tPremi '?' per aiuto.")
    stopwatch = Stopwatch()
    while True:
        if kbhit():
            key = getch()
            if key == 'a':
                stopwatch.start_pause()
            elif key == '?':
                mostra_aiuto()
            
            elif key == 'w':
                imposta_sveglia()
            elif key == 'x':
                imposta_timer()
            elif key == 's':
                stopwatch.stop()
            elif key == 'z':
                if not stopwatch.is_running:
                    stopwatch.reset()
                else:
                    print("\nIl cronometro deve essere in pausa per azzerare.",end="",flush=True)
            elif key == 'g':
                stopwatch.record_lap()
            elif key == 'd':
                mostra_data_attuale()
            elif key == 'o':
                mostra_ora_attuale()
            elif key == 'c':
                tempo_trascorso = stopwatch.get_elapsed_time()
                if tempo_trascorso > 0:
                    print(f"\nTempo trascorso: {stringa_tempo_descrittiva(tempo_trascorso)}", end="", flush=True)
            elif key == 'b':
                esegui_benchmark_multicore()
            elif key == 'n': # Nuovo comando per le classifiche
                mostra_classifiche()
            elif key == 'v':
                tempo_esec = tempo_complessivo_esecuzione()
                if tempo_esec > 0:
                    print(f"\nTempo applicazione: {stringa_tempo_descrittiva(tempo_esec)}",end="",flush=True)
            elif key == 'q':
                salva_report(stopwatch)
                print("\nArrivederci!")
                break
        time.sleep(0.01)

if __name__ == "__main__":
    # Assicurati che il programma non si blocchi quando eseguito come eseguibile compilato
    multiprocessing.freeze_support() 
    main()