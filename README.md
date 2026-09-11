# Meditimer, l'affetta tempo

Un cronometro da riga di comando, pensato per chi usa uno screen reader e un display braille. Registra i giri e li confronta fra loro, tiene timer e sveglie, misura quanto è veloce il computer su cui gira e conserva i risultati per mettere in classifica le tue macchine. Ogni comando è un tasto solo, senza invio, e ogni tasto ha il suo suono.

Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode). Versione 3.0.0 del 11 settembre 2026. Il manuale completo è il file `manuale.txt`, che si legge anche dentro il programma con il tasto m; le novità di ogni versione stanno in `CHANGELOG.md`.

## Che cosa fa

- Cronometro con giri: ogni giro viene detto a parole, con la variazione in percentuale rispetto al giro precedente e alla media, e con un suono diverso a seconda che sia più veloce, più lento, nella media o un nuovo primato. Le pause non entrano nei giri.
- Statistiche dei giri: il più veloce e il più lento, la differenza, la media, la mediana, lo scarto medio, il totale.
- Report di ogni sessione in un file di testo, una frase per riga.
- Timer e sveglie quanti ne vuoi, con elenco, annullamento e una suoneria che si zittisce con un tasto qualsiasi. La sveglia si scrive come 13:02, oppure 13 per le tredici, 5 per il minuto cinque, +5 per fra cinque minuti.
- Banco di prova della macchina in nove fasi: interi, decimali e funzioni matematiche su tutti i processori e su uno solo, copia in memoria su un core e su tutti, scrittura e lettura del disco. Con la scheda della macchina e, se HWiNFO è in esecuzione, potenza, temperature e clock del processore durante la prova.
- Archivio delle prove con la cronologia di ogni macchina, confronto con le prove precedenti, primati, e quattro classifiche fra le macchine.

## Scaricare e avviare

L'eseguibile per Windows è nell'ultima release su GitHub: https://github.com/GabrieleBattaglia/meditimer/releases/latest. Si scarica l'archivio, si estrae dove si vuole e si avvia `meditimer.exe`. Non serve installare niente. Al primo avvio Windows può mostrare l'avviso di SmartScreen, perché l'eseguibile non è firmato: è normale. All'avvio il programma controlla se c'è una versione nuova e propone di installarla.

Dal codice sorgente:

1. Serve Python 3.10 o successivo.
2. Serve GBUtils, la libreria condivisa di IZ4APU, con la sua collezione dei suoni: `git clone https://github.com/GabrieleBattaglia/GBUtils.git` e poi la sua cartella in PYTHONPATH, oppure `GBUtils.py` e `Acu_Collection.json` copiati accanto a `meditimer.py`.
3. `pip install -r requirements.txt` per numpy, scipy, sounddevice, requests e, facoltativo, psutil.
4. `python meditimer.py`.

## I comandi

- a: avvia il cronometro, lo mette in pausa, lo riprende.
- spazio: registra un giro.
- s: registra l'ultimo giro e ferma il cronometro.
- f: statistiche dei giri.
- c: tempo trascorso.
- z: salva il report e azzera, a cronometro fermo.
- x: imposta un timer, per esempio 90, 2:30 oppure 1:15:00.
- w: imposta una sveglia, per esempio 13:02, 13, 5 oppure +5.
- l: elenca timer e sveglie, e ne annulla uno.
- d: la data di oggi.
- o: l'ora.
- v: da quanto tempo gira il programma.
- b: banco di prova della macchina.
- n: classifiche dei banchi di prova.
- m: il manuale.
- ?: l'elenco dei comandi.
- q: salva il report ed esce. Anche Ctrl più C.

## I file

Tutto nasce nella cartella del programma, accanto all'eseguibile: i report delle sessioni, `Meditimer` seguito da data e ora; i report delle prove, `benchmark` seguito dal nome del computer e dalla data; l'archivio `benchmark_results.json`, con la copia di riserva `.bak`. Per confrontare macchine diverse basta portare l'archivio da una all'altra e fare la prova anche lì.

## Accessibilità

Output lineare, senza tabelle, righe di trattini o animazioni. Ogni messaggio va a capo prima e non dopo, così il display braille resta sull'ultima riga scritta. Le righe con più dati sono in blocchi di quaranta caratteri. Tutto ciò che si vede si sente anche, e tutto ciò che si sente è scritto.

## Sviluppo

I moduli: `meditimer.py` è il ciclo dei tasti, `cronometro.py` il cronometro, `sveglie.py` timer e sveglie, `banco_prova.py` le misure, `sensori.py` la lettura di HWiNFO, `classifiche.py` l'archivio, `suoni.py` la mappa dei suoni, `formati.py` i formati, `percorsi.py` i percorsi, `version.py` la versione. Le prove automatiche stanno in `tests`, si eseguono con `python -m pytest tests -q`, e il codice passa `ruff check` con la configurazione di `ruff.toml`. `ascolta_suoni.py` fa sentire i suoni uno per uno. `meditimer.spec` compila con PyInstaller un eseguibile in un file unico, e `zip_maker.py` prepara l'archivio della release.

Licenza: GPL 3, vedi `LICENSE`.
