# Changelog - Meditimer

Tutti i cambiamenti e le novità introdotte nelle versioni di Meditimer.
Il changelog nasce con la versione 3.0.0. Per le versioni precedenti il resoconto sta nella cronologia dei commit e nelle release pubblicate su GitHub.

## [3.0.0] - 2026-09-11

Revisione 1 del refactoring generale del parco software. Il programma è stato riscritto in moduli, e la versione cambia di numero maggiore perché cambiano i comandi, i suoni, il banco di prova e il formato dell'archivio.

### Aggiunto
- **Un suono per ogni tasto.** Trentotto suoni nuovi nella collezione condivisa, tutti brevi e morbidi. I giri hanno un suono diverso a seconda dell'esito: più veloce o più lento del precedente, nella media, uguale, nuovo primato in un verso o nell'altro. La suoneria di timer e sveglie è l'unico suono fatto per farsi notare, e la zittisce un tasto qualsiasi.
- **Timer e sveglie sotto controllo.** Il tasto l li elenca con l'orario di scadenza e quanto manca, e permette di annullarne uno. Ogni avviso è numerato. Uscendo dal programma vengono annullati.
- **La sintassi della sveglia.** 13:02 è quell'orario; 13 sono le tredici; 5 è il minuto cinque dell'ora in corso, o della prossima se è passato; +5 è fra cinque minuti e +2:08 fra due ore e otto minuti.
- **Il banco di prova in nove fasi.** Alle tre prove del processore su tutti i core si aggiungono le stesse su un core solo, con il fattore di scala; la copia in memoria su un core e su tutti, che è la misura che vede la frequenza della RAM; e il disco, scrittura con sincronizzazione forzata e rilettura senza la cache di sistema. Si sceglie la durata fra breve, normale e lunga; ogni fase è annunciata con un suono e riassunta con il risultato; escape fra una fase e l'altra annulla.
- **La scheda della macchina** con ogni prova: processore, core fisici e processori logici, frequenza, memoria, sistema, versione di Python, alimentazione da rete o da batteria.
- **I sensori di HWiNFO.** Se HWiNFO è in esecuzione con la memoria condivisa attiva, il report dice a che potenza, temperatura e clock ha lavorato il processore durante le prove, e quali limiti sono scattati.
- **La cronologia delle prove.** L'archivio tiene tutte le prove di ogni macchina invece di una sola. Dopo ogni prova il programma dice quanto è cambiata rispetto alla precedente, se è un primato della macchina, e a che posto sta in classifica. In classifica ogni macchina compare con la sua prova migliore.
- **Quattro classifiche** invece di tre: multi core e un processore, ordinate per la media geometrica delle tre prove, memoria e disco. Con due conti sull'archivio in fondo.
- **Il manuale** con il tasto m, una pagina alla volta, e il file manuale.txt che viaggia dentro l'eseguibile.
- **Statistiche dei giri più ricche:** mediana, scarto medio in tempo e in percentuale, totale dei giri, e i pari merito detti per nome.
- **Controllo degli aggiornamenti** all'avvio del programma compilato, come negli altri programmi del parco.
- **Ctrl più C** esce in modo ordinato, salvando il report, invece di buttare via la sessione.
- **Pulizia dei report vecchi.** A ogni avvio i report di testo più vecchi di un anno, quelli delle sessioni e quelli delle prove, vengono cancellati, e il programma dice quanti; l'archivio delle prove non si tocca mai.
- **Prove automatiche** nella cartella tests, novantasette, su cronometro, formati, timer e sveglie, archivio, banco di prova, sensori e una sessione intera del programma.
- I file requirements.txt, ruff.toml, ascolta_suoni.py per sentire i suoni uno per uno, e il changelog.

### Modificato
- **I giri non contano più le pause.** Fino alla 2.9.1 la pausa finiva dentro il giro successivo, che risultava più lento di quanto fosse stato e falsava media, primati e percentuali, anche nel report salvato.
- **La percentuale del giro dice rispetto a che cosa.** Prima era la posizione del giro fra il più veloce e il più lento, e cambiava formula quando i giri precedenti erano uguali. Ora sono due variazioni, rispetto al giro precedente e rispetto alla media dei giri precedenti. A schermo il giro è una riga breve entro quaranta caratteri con le lettere come codice, per esempio g3 01:02.345 pv3,1% ml1,2% rv, e lo stesso vale per stop, pausa e tempo trascorso; nel report su file ogni giro è scritto per esteso, a parole. La legenda è nell'elenco dei comandi e nel manuale.
- **Niente più tabelle e righe di trattini.** Classifiche, confronto, statistiche e report sono frasi, una per riga, con i dati in blocchi di quaranta caratteri per il display braille. I numeri grandi si dicono a parole, milioni e miliardi, con la virgola all'italiana.
- **I risultati per processore sono riassunti:** totale, il più lento e il più veloce, media, dispersione e i processi fuori norma, invece di una riga per ognuno dei trentadue. Il dettaglio resta nel file del report e nell'archivio.
- **I file nascono accanto al programma**, non nella cartella da cui lo si è avviato, e il programma dice sempre dove li ha scritti. Se non riesce a scrivere lo dice e la sessione non si perde.
- **L'archivio delle prove si salva in sicurezza**, passando da un file temporaneo e lasciando la copia di riserva bak. Il file della 2.9.1 viene convertito al primo avvio; le voci rotte vengono scartate contandole, invece di far cadere il programma.
- **Ogni processo del banco di prova misura da sé la propria durata**, così l'avvio dei processi non diluisce più la prima fase.
- **Il tasto z dichiara quello che fa:** salva il report e azzera.
- **Le richieste di testo** usano dgt di GBUtils, la suoneria usa Acusticator invece del campanello del terminale, e il programma importa GBUtils come tutti gli altri, senza costruirsi il percorso da solo.
- Il tasto s non dice più due frasi contraddittorie, e non dice fermato se il cronometro non è mai partito; all'avvio non si sente più un azzeramento che nessuno ha chiesto; un tasto non previsto viene detto invece di essere ignorato in silenzio.
- Il timer rifiuta le durate con più di tre campi invece di scartare il primo in silenzio.
- README riscritto, con i comandi giusti e le dipendenze vere.

### Rimosso
- La cartella build di PyInstaller dal repository, e la regola che escludeva da git ogni file di testo.
- La domanda se sovrascrivere i risultati precedenti: con la cronologia non si sovrascrive più niente.
