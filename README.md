# Meditimer

Un cronometro semplice, potente e accessibile da riga di comando (CLI). Progettato per essere leggero e funzionale, Meditimer permette di cronometrare tempi, registrare giri e salvare report dettagliati. Include anche una potente funzione di **benchmark** per testare le prestazioni della CPU, un **timer** per conti alla rovescia e una **sveglia** programmabile.

L'interfaccia testuale lo rende perfettamente compatibile con gli screen reader, garantendo la piena accessibilità.

**by Gabriele Battaglia (IZ4APU)**

## Funzionalità

  * **Cronometro completo:** Avvio, pausa, stop e azzeramento.
  * **Registrazione Giri:** Registra tempi parziali (giri) con la pressione di un tasto.
  * **Analisi Giri:** Calcola e mostra automaticamente il giro più veloce e quello più lento.
  * **Timer e Sveglia:** Imposta timer multipli per conti alla rovescia o sveglie per orari specifici. I thread in background garantiscono che queste funzioni non interferiscano con il cronometro.
  * **Benchmark CPU:** Esegue un test di performance multi-core per misurare la potenza di calcolo del tuo sistema.
  * **Classifiche Benchmark:** Confronta i risultati dei tuoi test con quelli di altre macchine grazie a classifiche ordinate salvate localmente.
  * **Informazioni Rapide:** Visualizza data, ora e tempo trascorso in qualsiasi momento.
  * **Report Automatico:** Salva un report di testo dettagliato per il cronometro e i risultati dei benchmark.

## Requisiti

  * **Python 3** (versione 3.8 o successiva consigliata).
  * **Nessuna dipendenza esterna.** Il programma utilizza solo librerie standard di Python, quindi non è richiesta l'installazione di pacchetti aggiuntivi.

## Installazione e Avvio

Puoi scaricare l'eseguibile da github dal link [www.github.com/GabrieleBattaglia/meditimer.git](https://www.google.com/search?q=https://www.github.com/GabrieleBattaglia/meditimer.git)
Oppure segui questa procedura per lanciarlo da sorgente Python.

1.  Assicurati di avere Python installato sul tuo computer.
2.  Salva il file `meditimer.py` in una cartella a tua scelta.
3.  Apri un terminale (Prompt dei comandi su Windows, Terminale su macOS/Linux).
4.  Naviga fino alla cartella dove hai salvato il file usando il comando `cd NOME_CARTELLA`.
5.  Esegui il programma con il comando:
    ```
    python meditimer.py
    ```

## Comandi (Tasti Rapidi)

All'avvio del programma, puoi usare i seguenti tasti per controllarlo. Non è necessario premere Invio.

| Tasto | Azione | Descrizione |
|:---:|---|---|
| **`a`** | Avvia / Pausa | Avvia il cronometro se è fermo, lo mette in pausa se è in esecuzione, o lo riprende se è in pausa. |
| **`s`** | Ferma (Stop) | Interrompe il cronometro. Equivale a metterlo in pausa. |
| **`z`** | Azzera | Resetta il cronometro e tutti i giri registrati. Funziona solo se il cronometro è fermo. |
| **`g`** | Registra Giro | Salva il tempo parziale dall'ultimo giro (o dall'inizio) senza fermare il cronometro. |
| **`c`** | Tempo Trascorso | Mostra il tempo totale misurato dal cronometro. |
| **`d`** | Mostra Data | Visualizza la data corrente. |
| **`o`** | Mostra Ora | Visualizza l'ora corrente. |
| **`v`** | Tempo Esecuzione | Mostra da quanto tempo è in esecuzione il programma Meditimer. |
| **`b`** | **Benchmark CPU** | Avvia il test di velocità del computer (vedi sezione dedicata). |
| **`n`** | **Classifiche** | Mostra le classifiche dei risultati dei benchmark salvati. |
| **`x`** | **Imposta Timer** | Avvia un conto alla rovescia. Al termine, emette un segnale acustico. |
| **`w`** | **Imposta Sveglia** | Imposta una sveglia per un orario specifico. Al termine, emette un segnale acustico. |
| **`q`** | Esci e Salva | Chiude il programma e salva il report del cronometro (se utilizzato) in un file di testo. |
| **`?`** | Aiuto | Mostra la lista dei comandi disponibili direttamente nel terminale. |

## Funzioni Avanzate

#### Funzione di Benchmark

Premendo il tasto **`b`**, avvierai un test di performance che misura la potenza di calcolo della tua CPU.

  * **Multipiattaforma e Multi-Core:** Il test è progettato per sfruttare tutti i core del tuo processore.
  * **Tre Fasi Separate:** Esegue tre test distinti e sequenziali da 10 secondi ciascuno per misurare diverse aree di performance:
    1.  **Calcoli su Interi:** Operazioni aritmetiche base.
    2.  **Calcoli su Float:** Operazioni con numeri decimali.
    3.  **Funzioni Matematiche:** Calcoli complessi (`sqrt`, `sin`).
  * **Salvataggio Automatico:** Al termine, i risultati vengono mostrati a schermo, salvati in un file `.txt` e aggiunti al file `benchmark_results.json` per alimentare le classifiche.

#### Classifiche Benchmark

Premendo il tasto **`n`**, puoi visualizzare le classifiche di tutti i benchmark eseguiti e salvati.

  * **Tre Classifiche:** Viene mostrata una classifica per ognuna delle tre tipologie di test (Interi, Float, Matematiche).
  * **Ordinamento:** Le macchine sono ordinate dalla più veloce alla più lenta in base alle "operazioni al secondo" (op/s).
  * **Dettagli:** Ogni riga della classifica riporta posizione, nome del computer, velocità, data del test e note dell'utente.

#### Timer e Sveglia

I comandi **`x`** (timer) e **`w`** (sveglia) ti permettono di impostare avvisi acustici in background.

  * **Input Intelligente:** Puoi specificare la durata o l'orario in formati flessibili:
      * `35` = 35 secondi (solo per il timer).
      * `2:35` = 2 minuti e 35 secondi.
      * `3:3:35` = 3 ore, 3 minuti e 35 secondi.
  * **Esecuzione in Background:** Grazie al multithreading, puoi impostare timer e sveglie multiple senza interrompere il cronometro principale.
  * **Avviso Acustico:** Al termine, il programma emetterà una sequenza di beep di sistema.

## Report e Dati

Meditimer genera automaticamente tre tipi di file nella sua cartella:

1.  **Report Cronometro (`.txt`):** Creato quando si esce con `q` (solo se il cronometro è stato usato). Contiene il riepilogo dei giri, i tempi totali e le statistiche.
2.  **Report Benchmark (`.txt`):** Creato dopo ogni test con `b`. Contiene i dettagli del sistema e i risultati del test di performance.
3.  **Database Classifiche (`.json`):** Il file `benchmark_results.json` contiene i dati strutturati di tutti i benchmark eseguiti. Viene letto dal programma per generare le classifiche e aggiornato ogni volta che si esegue un nuovo test.
Per mettere in classifica e confrontare le tue diverse macchine ad esempio, o quelle dei tuoi amici, o quelle su cui stai facendo dei test, sposta il file .json generato da meditimer su una diversa copia del programma, su un diverso computer, poi esegui meditimer e fagli eseguire il test velocità premendo la b. Al termine osserva le classifiche premendo la n.

## Compatibilità e Accessibilità

  * **Multipiattaforma (Cross-Platform)**: Il codice è pienamente compatibile con **Windows** e sistemi **Unix-like (Linux, macOS)**.
  * **Accessibilità**: Essendo un'applicazione a riga di comando con output testuale pulito, Meditimer è pienamente utilizzabile con gli screen reader (come JAWS, NVDA o VoiceOver) per garantire un'esperienza utente ottimale anche per le persone non vedenti.