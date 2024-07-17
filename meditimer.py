# Meditimer L'affetta tempo
# Data concepimento: 05/11/2015 11:51 by Gabriele Battaglia
# Porting Python 3.6: 23/11/2017.
# Inizio restyling 10/02/2022
# Restyling con ChatGPT4o il 16 luglio 2024

import time
import datetime
import msvcrt
import sys
from GBUtils import menu

VERSIONE = "2.0.5 di luglio 2024"
MNMENU={'a':'per avviare/pausa',
		's':'Per fermare',
		'z':'Per azzerare',
		'g':'Per registrare un giro',
		'd':'Per mostrare la data',
		'o':"Per mostrare l'ora",
		'x':'Per tempo in cui il cronometro era in moto',
		'c':'Per tempo trascorso globalmente',
		'v':'Per tempo complessivo di esecuzione',
		'q':'Per uscire e salvare il report',
		'?':'Per mostrare questo aiuto'}
go = False
stop = True
crono = 0.0
tpausa = 0.0
giri = []
start_time = None
pause_time = None
last_giro_time = None  # New variable to store the last lap time
TINIZIO = time.time()
TCRONOINIZIO = None  # New variable to store the start time of the first start of the cronometro
TEMPO_PAUSE = 0.0  # Total pause time accumulated

GIORNISETTIMANA = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
MESIANNO = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]

def stringa_tempo(t):
	"""Riceve un tempo in secondi e rende una stringa formattata"""
	millis = int((t - int(t)) * 1000)
	seconds = int(t) % 60
	minutes = (int(t) // 60) % 60
	hours = (int(t) // 3600)
	return f"{hours:02}:{minutes:02}:{seconds:02}.{millis:03}"

def avvia_pausa_cronometro():
	global go, stop, start_time, pause_time, tpausa, crono, last_giro_time, TCRONOINIZIO, TEMPO_PAUSE
	if not go:
		go = True
		stop = False
		if TCRONOINIZIO is None:
			TCRONOINIZIO = time.time()
		if start_time is None:
			start_time = time.time()
		else:
			TEMPO_PAUSE += time.time() - pause_time
			start_time = time.time() - crono
		last_giro_time = start_time  # Initialize last_giro_time when starting the cronometro
		print("\nCronometro avviato!",end="",flush=True)
	elif not stop:
		stop = True
		pause_time = time.time()
		crono = pause_time - start_time
		print("\nCronometro in pausa!",end="",flush=True)
	else:
		stop = False
		TEMPO_PAUSE += time.time() - pause_time
		start_time = time.time() - crono
		print("\nCronometro ripreso!",end="",flush=True)

def ferma_cronometro():
	global go, stop, crono, pause_time
	if not stop:
		stop = True
		pause_time = time.time()
		crono = pause_time - start_time
		print("\nCronometro fermato!",end="",flush=True)
		go = False

def azzera_cronometro():
	global go, stop, crono, tpausa, giri, last_giro_time, TCRONOINIZIO, TEMPO_PAUSE
	if stop:
		go = False
		stop = True
		crono = 0.0
		tpausa = 0.0
		giri = []
		last_giro_time = None
		TCRONOINIZIO = None
		TEMPO_PAUSE = 0.0
		print("\nCronometro azzerato!",end="",flush=True)
	else:
		print("\nIl cronometro deve essere in pausa per azzerare.",end="",flush=True)

def registra_giro():
	global crono, start_time, giri, tpausa, last_giro_time
	if not stop:
		now = time.time()
		if last_giro_time is None:
			last_giro_time = now
		giro = now - last_giro_time
		last_giro_time = now
		giri.append(giro)
		numero_giro = len(giri)
		print(f"\nGiro {numero_giro} registrato: {stringa_tempo(giro)}",end=" ",flush=True)
		if giro == min(giri):
			print("max",end="",flush=True)
		elif giro == max(giri):
			print("min",end="",flush=True)

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

def tempo_trascorso_globale():
	global TCRONOINIZIO, TEMPO_PAUSE, go, stop, pause_time
	if TCRONOINIZIO is None:
		tempo_trascorso = 0.0
	elif go:
		tempo_trascorso = time.time() - TCRONOINIZIO - TEMPO_PAUSE
	else:
		tempo_trascorso = pause_time - TCRONOINIZIO - TEMPO_PAUSE
	print(f"\nTempo cronometro attivo): {stringa_tempo(tempo_trascorso)}",end="",flush=True)
	return tempo_trascorso

def tempo_cronometro_in_moto():
	global crono, start_time, tpausa
	if not stop:
		tempo_in_moto = time.time() - start_time - tpausa
	else:
		tempo_in_moto = crono
	print(f"\nTempo cronometro in moto: {stringa_tempo(tempo_in_moto)}",end="",flush=True)
	return tempo_in_moto

def tempo_complessivo_esecuzione():
	global TINIZIO
	tempo_complessivo = time.time() - TINIZIO
	print(f"\nTempo applicazione: {stringa_tempo(tempo_complessivo)}",end="",flush=True)
	return tempo_complessivo

def salva_report():
	global giri, crono
	tempo_in_moto = tempo_cronometro_in_moto()
	tempo_globale = tempo_trascorso_globale()
	tempo_complessivo = tempo_complessivo_esecuzione()
	filename = f"Meditimer-{datetime.datetime.now().strftime('%y%m%d-%H%M')}.txt"
	with open(filename, 'w') as f:
		f.write(f"Report Meditimer versione {VERSIONE}\n")
		f.write(f"Creato il {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
		f.write("Giri registrati:\n")
		for i, giro in enumerate(giri):
			giro_str = stringa_tempo(giro)
			if giro == min(giri):
				giro_str += " Giro più veloce"
			elif giro == max(giri):
				giro_str += " Giro più lento"
			f.write(f"Giro {i+1}: {giro_str}\n")
		if giri:
			f.write(f"\nGiro più veloce: {stringa_tempo(min(giri))}")
			f.write(f"Giro più lento: {stringa_tempo(max(giri))}\n")
			f.write(f"Tempo medio: {stringa_tempo(sum(giri) / len(giri))}\n")
		f.write(f"\nTempo totale: {stringa_tempo(sum(giri))}")
		f.write(f"Tempo trascorso globalmente: {stringa_tempo(tempo_globale)}\n")
		f.write(f"Tempo del cronometro in moto: {stringa_tempo(tempo_in_moto)}\n")
		f.write(f"Tempo complessivo di esecuzione: {stringa_tempo(tempo_complessivo)}\n")
	print(f"Report salvato in {filename}")

def main():
	print(f"Meditimer, versione {VERSIONE} by Gabriele Battaglia (IZ4APU).\n\tPremi '?' per aiuto.")
	while True:
		if msvcrt.kbhit():
			key = msvcrt.getch().decode('utf-8').lower()
			if key == 'a':
				avvia_pausa_cronometro()
			elif key == '?': menu(d=MNMENU,show_only=True)
			elif key == 's':
				ferma_cronometro()
			elif key == 'z':
				azzera_cronometro()
			elif key == 'g':
				registra_giro()
			elif key == 'd':
				mostra_data_attuale()
			elif key == 'o':
				mostra_ora_attuale()
			elif key == 'c':
				tempo_trascorso_globale()
			elif key == 'x':
				tempo_cronometro_in_moto()
			elif key == 'v':
				tempo_complessivo_esecuzione()
			elif key == 'q':
				salva_report()
				print("Arrivederci!")
				break

if __name__ == "__main__":
	main()
