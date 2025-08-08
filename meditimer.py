# Meditimer L'affetta tempo
# Data concepimento: 05/11/2015 11:51 by Gabriele Battaglia
# Porting Python 3.6: 23/11/2017.
# Inizio restyling 10/02/2022
# Restyling con ChatGPT4o il 16 luglio 2024

import time
import datetime
import sys

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

VERSIONE = "2.1.0 di luglio 2024"
MNMENU={'a':'per avviare/pausa',
		's':'Per fermare',
		'z':'Per azzerare',
		'g':'Per registrare un giro',
		'd':'Per mostrare la data',
		'o':"Per mostrare l'ora",
		'c':'Per tempo trascorso',
		'v':'Per tempo complessivo di esecuzione',
		'q':'Per uscire e salvare il report',
		'?':'Per mostrare questo aiuto'}

GIORNISETTIMANA = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
MESIANNO = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
TINIZIO = time.time()

def stringa_tempo(t):
	"""Riceve un tempo in secondi e rende una stringa formattata"""
	millis = int((t - int(t)) * 1000)
	seconds = int(t) % 60
	minutes = (int(t) // 60) % 60
	hours = (int(t) // 3600)
	return f"{hours:02}:{minutes:02}:{seconds:02}.{millis:03}"

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
        print(f"\nGiro {numero_giro} registrato: {stringa_tempo(lap_time)}", end=" ", flush=True)
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
	with open(filename, 'w') as f:
		f.write(f"Report Meditimer versione {VERSIONE}\n")
		f.write(f"Creato il {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
		if giri:
			f.write("\nGiri registrati:\n")
			for i, giro in enumerate(giri):
				giro_str = stringa_tempo(giro)
				if giro == min(giri):
					giro_str += " (Giro più veloce)"
				elif giro == max(giri):
					giro_str += " (Giro più lento)"
				f.write(f"  Giro {i+1}: {giro_str}\n")
			f.write(f"\nGiro più veloce: {stringa_tempo(min(giri))}")
			f.write(f"\nGiro più lento: {stringa_tempo(max(giri))}\n")
			f.write(f"Tempo medio: {stringa_tempo(sum(giri) / len(giri))}\n")
			f.write(f"\nTempo totale dei giri: {stringa_tempo(sum(giri))}\n")
		f.write(f"Tempo totale trascorso: {stringa_tempo(tempo_trascorso)}\n")
		f.write(f"Tempo complessivo di esecuzione: {stringa_tempo(tempo_complessivo)}\n")
	print(f"\nReport salvato in {filename}")

def mostra_aiuto():
    print("\nComandi disponibili:")
    for key, desc in MNMENU.items():
        print(f"\t'{key}': {desc}")

def main():
	print(f"Meditimer, versione {VERSIONE} by Gabriele Battaglia (IZ4APU).\n\tPremi '?' per aiuto.")
	stopwatch = Stopwatch()
	stopwatch.reset() # To print the initial message

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
				print(f"\nTempo trascorso: {stringa_tempo(stopwatch.get_elapsed_time())}",end="",flush=True)
			elif key == 'v':
				print(f"\nTempo applicazione: {stringa_tempo(tempo_complessivo_esecuzione())}",end="",flush=True)
			elif key == 'q':
				salva_report(stopwatch)
				print("\nArrivederci!")
				break
		time.sleep(0.01) # To prevent high CPU usage

if __name__ == "__main__":
	main()
