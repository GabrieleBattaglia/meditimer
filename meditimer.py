# Meditimer L'affetta tempo
# Data concepimento: 05/11/2015 11:51 by Gabriele Battaglia
# Porting Python 3.6: 23/11/2017.
# Inizio restyling 10/02/2022
# Restyling con ChatGPT4o il 16 luglio 2024

import time, datetime, sys, os, socket, math, multiprocessing

# Cross-platform getch and kbhit
try:
    # Windows
    import msvcrt
    def kbhit():
        return msvcrt.kbhit()
    def getch():
        return msvcrt.getch().decode('utf-8').lower()
except ImportError:
    # Unix-like
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

VERSIONE = "2.2.4 di settembre 2025"
MNMENU={'a':'per avviare/pausa',
  's':'Per fermare',
  'z':'Per azzerare',
  'g':'Per registrare un giro',
  'd':'Per mostrare la data',
  'o':"Per mostrare l'ora",
  'c':'Per tempo trascorso',
  'v':'Per tempo complessivo di esecuzione',
  'b':'Per eseguire un test di velocità della macchina',
  'q':'Per uscire e salvare il report',
  '?':'Per mostrare questo aiuto'}
GIORNISETTIMANA = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
MESIANNO = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
TINIZIO = time.time()

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

    # Unisce le parti con virgole e una "e" finale
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
            # Starting or resuming
            self._running = True
            if self._start_time == 0.0: # First start
                self._start_time = time.time()
                self._last_lap_time = self._start_time
                print("\nCronometro avviato!", end="", flush=True)
            else: # Resuming
                pause_duration = time.time() - self._pause_time
                self._total_pause_time += pause_duration
                print("\nCronometro ripreso!", end="", flush=True)
        else:
            # Pausing
            self._running = False
            self._pause_time = time.time()
            print("\nCronometro in pausa!", end="", flush=True)

    def stop(self):
        if self._running:
            self.start_pause() # Just pause it
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
    f.write(f"\nTempo totale dei giri: {stringa_tempo_descrittiva(sum(giri))}\n") # <-- MODIFICA QUI
  if tempo_trascorso > 0:
   f.write(f"Tempo totale trascorso: {stringa_tempo_descrittiva(tempo_trascorso)}\n") # <-- MODIFICA QUI
  if tempo_complessivo > 0:
   f.write(f"Tempo complessivo di esecuzione: {stringa_tempo_descrittiva(tempo_complessivo)}\n") # <-- MODIFICA QUI
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
            # Usiamo 'g' per un formato più compatto e togliamo .0 inutili
            return f"{float(f'{n:.3g}'):g} {unita}{suffisso}".replace(",", ".")
        n /= 1000.0
    return f"{n:,.2f} P{suffisso}".replace(",", ".")
def benchmark_worker(durata, tipo_test):
    """
    Esegue calcoli intensivi per un singolo processo.
    Ora esegue solo UN tipo di test in base all'argomento 'tipo_test'.
    """
    operazioni = 0
    start_time = time.perf_counter()
    
    # Esegue un ciclo ottimizzato per il tipo di test specifico
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

def esegui_benchmark_multicore():
    """
    Esegue 3 test di performance separati (Interi, Float, Math),
    sfruttando tutti i core della CPU per ogni test.
    """
    print("\n\n-- Inizio Test di Velocità Multi-Core (3 Fasi) --")
    
    DURATA_PER_TEST = 10.0 # Durata di ciascun test in secondi
    num_core = os.cpu_count() or 1

    print(f"Rilevati {num_core} core. Verranno eseguiti 3 test da {DURATA_PER_TEST} secondi ciascuno.")
    print("Non usare il computer durante l'analisi per risultati più accurati.")

    # Raccogli informazioni sul sistema
    nome_computer = socket.gethostname()
    info_python = sys.version
    
    # Inizializza il report
    report = [f"--- Report Test di Velocità Multi-Core (3 Fasi) ---"]
    report.append(f"Nome Computer: {nome_computer}")
    report.append(f"Data e Ora: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Versione Python: {info_python.splitlines()[0]}")
    
    tipi_di_test = [
        ('Calcoli su Interi', 'int'),
        ('Calcoli su Float', 'float'),
        ('Funzioni Matematiche', 'math')
    ]

    with multiprocessing.Pool(processes=num_core) as pool:
        for i, (nome_test, tipo) in enumerate(tipi_di_test):
            print(f"\n-- Fase {i+1}/3: {nome_test}... --")
            
            start_time = time.perf_counter()
            # Usiamo starmap per passare argomenti multipli (durata, tipo) al worker
            args = [(DURATA_PER_TEST, tipo)] * num_core
            risultati_per_core = pool.starmap(benchmark_worker, args)
            end_time = time.perf_counter()
            
            tempo_effettivo = end_time - start_time
            
            # Analizza e aggiungi al report i risultati della fase corrente
            report.append("-" * 40)
            report.append(f"RISULTATI FASE: {nome_test}")
            report.append(f"Durata effettiva: {tempo_effettivo:.4f} secondi")

            totale_operazioni = sum(risultati_per_core)
            performance_totale = totale_operazioni / tempo_effettivo
            
            report.append(f"  Performance Totale: {formatta_numero_grande(performance_totale, 'op/s')} ({performance_totale:,.0f} op/s)")
            report.append("  Performance per Core:")
            
            for core_idx, res_core in enumerate(risultati_per_core):
                perf_core = res_core / tempo_effettivo
                report.append(f"    Core {core_idx+1:<2}: {formatta_numero_grande(perf_core, 'op/s')} ({perf_core:,.0f} op/s)")

    report.append("-" * 40)
    report.append("Nota: RAM e GPU non possono essere misurate con precisione usando solo librerie standard di Python.")
    
    report_completo = "\n".join(report)
    print("\n" + report_completo)

    # Chiedi una nota all'utente e salva il file
    print("\nPuoi aggiungere una nota personale al report.")
    nota_utente = input("Inserisci la nota e premi Invio (lascia vuoto per nessuna nota): ")
    if nota_utente:
        report.append("\n--- Nota dell'Utente ---")
        report.append(nota_utente)

    try:
        filename = f"benchmark-multicore-{nome_computer}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(report))
        print(f"\nReport di benchmark salvato con successo nel file: {filename}")
    except IOError as e:
        print(f"\nErrore: Impossibile salvare il file di report. Dettagli: {e}")

    print("\nPremi un tasto per tornare al menu principale.")

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
   elif key == 'v':
    tempo_esec = tempo_complessivo_esecuzione()
    if tempo_esec > 0:
     print(f"\nTempo applicazione: {stringa_tempo_descrittiva(tempo_esec)}",end="",flush=True)
   elif key == 'q':
    salva_report(stopwatch)
    print("\nArrivederci!")
    break
  time.sleep(0.01) # To prevent high CPU usage

if __name__ == "__main__":
 main()
