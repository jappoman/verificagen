# Verificagen

Generatore di verifiche in PDF a partire da contenuti strutturati in JSON e da una configurazione centrale in `config.json`.

Il progetto è pensato per lavorare insieme a Codex:

- l'utente carica il materiale didattico in `teaching-materials/`;
- Codex analizza il materiale seguendo [`prompt.md`](./prompt.md);
- Codex popola i file sorgente della verifica;
- lo script [`generate_verifiche.py`](./generate_verifiche.py) produce il PDF finale.

L'output predefinito è [`output/verifiche_generate.pdf`](./output/verifiche_generate.pdf).

## Cosa fa il software

Il generatore supporta:

- più versioni della stessa verifica in un unico PDF;
- distribuzione automatica delle copie in base al numero di alunni;
- interleaving delle copie nel PDF: `V1`, `V2`, `V3`... poi di nuovo `V1`, `V2`, `V3`...;
- intestazione con banner opzionale;
- titolo costruito automaticamente come `Verifica di <subject> - <title>`;
- campi studente configurabili: nome, classe, data;
- istruzioni iniziali obbligatorie;
- griglia di valutazione obbligatoria;
- griglia di valutazione filtrata automaticamente in base alle parti attive della prova;
- quiz a risposta multipla con estrazione casuale delle domande;
- mescolamento opzionale delle domande e delle alternative;
- domande aperte selezionate tramite ID;
- esercizi selezionati tramite ID;
- sezione finale con soluzioni e correzione rapida;
- schema rapido delle risposte corrette per ogni versione dei quiz;
- validazione del punteggio totale rispetto a `max_points`;
- normalizzazione automatica di `points_wrong` per i quiz a metà del punteggio positivo, con segno negativo;
- validazione dei file JSON sorgente e messaggi di errore espliciti in caso di configurazione incoerente.

## Struttura del repository

- [`generate_verifiche.py`](./generate_verifiche.py): script principale di generazione PDF.
- [`config.json`](./config.json): configurazione centrale della verifica.
- [`prompt.md`](./prompt.md): istruzioni operative per Codex.
- [`multiple-choice-question/`](./multiple-choice-question): pool di domande a risposta multipla.
- [`open-question/`](./open-question): domande aperte, un file JSON per domanda.
- [`practical-exercises/`](./practical-exercises): esercizi, un file JSON per esercizio.
- [`evaluation-grid/`](./evaluation-grid): griglie di valutazione.
- [`teaching-materials/`](./teaching-materials): materiale didattico caricato dall'utente.
- [`banner/`](./banner): immagini usate nell'intestazione.
- `output/`: PDF generati.

## Workflow consigliato

1. Inserisci il materiale didattico in `teaching-materials/`.
2. Chiedi a Codex di generare o aggiornare la verifica seguendo [`prompt.md`](./prompt.md).
   Se trova PDF o immagini nei materiali, il prompt gli dice di preparare automaticamente una versione testuale con:

```bash
python prepare_teaching_materials.py
```

   Il comando crea file Markdown in `teaching-materials/_extracted-text/`.
   Per i PDF testuali usa `pdftotext`; per PDF scannerizzati o immagini usa Tesseract OCR, se installato.

3. Verifica che `config.json` rispecchi la composizione desiderata della prova.
4. Esegui:

```bash
python generate_verifiche.py
```

5. Apri il PDF in `output/verifiche_generate.pdf`.

## Requisiti

- Python 3
- `reportlab`
- `poppler-utils` per estrarre testo dai PDF (`pdftotext`, `pdfinfo`, `pdftoppm`)
- opzionale ma consigliato: Tesseract OCR con lingua italiana per leggere PDF scannerizzati e immagini

Se `reportlab` non è disponibile, lo script non può generare il PDF.
Se Tesseract non è disponibile, `python prepare_teaching_materials.py` riesce comunque a estrarre i PDF testuali ma segnala i PDF scannerizzati che non ha potuto leggere via OCR.

## Configurazione

Il file [`config.json`](./config.json) controlla l'intero comportamento del generatore.

Campi principali:

- `title`: titolo specifico della verifica.
- `subject`: materia.
- `output_pdf`: percorso del PDF da generare.
- `number_of_students`: numero totale di copie da produrre.
- `number_of_versions`: numero di versioni diverse.
- `max_points`: punteggio massimo consentito.
- `random_seed`: seed per rendere riproducibile la generazione casuale.

### Regole importanti di configurazione

- Se `number_of_versions` è assente o vuoto, viene calcolato automaticamente con `ceil(number_of_students / 3)`.
- `number_of_versions` non può essere maggiore di `number_of_students`.
- `instructions.content` è obbligatorio e non può essere vuoto.
- Se i quiz sono attivi, `points_correct` deve essere positivo.
- Se i quiz sono attivi, `points_wrong` viene forzato automaticamente a `-points_correct / 2`.
- Il totale delle parti attive non può superare `max_points`.
- Il titolo mostrato nel PDF non è solo `title`, ma `Verifica di <subject> - <title>`.

## Sezioni della prova

Le tre sezioni gestibili sono:

- `multiple_choice`
- `open_questions`
- `practical_exercises`

Ogni sezione può essere attivata o disattivata da `config.json`.

### Quiz a risposta multipla

Campi usati:

- `enabled`
- `part_title`
- `source_file`
- `questions_per_exam`
- `points_correct`
- `points_wrong`
- `shuffle_questions`
- `shuffle_options`

Comportamento:

- lo script legge un pool di domande;
- verifica che ogni domanda abbia esattamente 4 opzioni;
- verifica che ci sia una sola risposta corretta;
- estrae le domande per ciascuna versione;
- rietichetta le alternative come `A`, `B`, `C`, `D` dopo l'eventuale mescolamento.
- il titolo di sezione viene numerato dinamicamente nel PDF, quindi in `part_title` va messo solo il nome base, per esempio `Quiz a risposta multipla`.

### Domande aperte

Campi usati:

- `enabled`
- `part_title`
- `source_dir`
- `include_ids`

Comportamento:

- lo script legge tutti i file JSON nella cartella;
- seleziona solo gli elementi elencati in `include_ids`;
- verifica la presenza di `solution.blocks`.
- il prefisso `Parte N -` viene aggiunto automaticamente in base all'ordine reale delle sezioni attive.

### Esercizi

Campi usati:

- `enabled`
- `part_title`
- `source_dir`
- `include_ids`

Il comportamento è analogo a quello delle domande aperte.

## Griglia di valutazione

La griglia è configurata in:

- `evaluation_grid.path`

Funzionalità:

- viene letta da un file JSON esterno;
- può contenere più sezioni;
- ogni sezione può dichiarare `applies_to`;
- il generatore mostra solo le fasce coerenti con le parti attive della prova.

La griglia non è opzionale: deve essere sempre attiva e valida.

Mapping attuale:

- `multiple_choice`
- `open_questions`
- `practical_exercises`

Se, per esempio, la prova contiene solo quiz e domande aperte, la fascia degli esercizi non viene mostrata.

## Formato dei dati

### Multiple choice

File JSON con chiave radice `questions`.

Ogni domanda contiene:

- `id`
- `topic`
- `prompt`
- `difficulty`
- `source`
- `explanation`
- `options`

Ogni opzione contiene:

- `id`
- `text`
- `is_correct`

Vincoli tecnici:

- 4 opzioni esatte;
- una sola opzione corretta;
- `id` opzione valido tra `A`, `B`, `C`, `D`.

### Domande aperte

Un file JSON per domanda.

Campi:

- `id`
- `prompt`
- `points`
- `solution.source`
- `solution.blocks`

### Esercizi

Un file JSON per esercizio.

Campi:

- `id`
- `prompt`
- `points`
- `solution.source`
- `solution.blocks`

### Blocchi soluzione supportati

- `paragraph`
- `bullets`
- `preformatted`
- `image`

## Soluzioni e correzione

Il PDF finale contiene anche una sezione conclusiva con:

- tabella rapida delle risposte corrette per ogni versione dei quiz;
- testo delle domande aperte ed eventuali esercizi inclusi;
- blocchi soluzione;
- fonte della soluzione.

## Impaginazione attuale

Lo script genera PDF in formato `A4` con:

- margine sinistro: `15 mm`
- margine destro: `15 mm`
- margine superiore: `12 mm`
- margine inferiore: `12 mm`

Il banner, se attivo, viene scalato automaticamente.

## Archiviare una verifica conclusa

Il generatore resta pensato per lavorare su una verifica alla volta. Quando una generazione è conclusa e vuoi conservare materiali, sorgenti JSON e PDF prima di prepararne una nuova, usa:

```bash
python archive_generation.py
```

Il comando crea una cartella in `archives/` con:

- `config.json`;
- `prompt.md`;
- materiali didattici presenti in `teaching-materials/`;
- domande, esercizi e file sorgente presenti nelle cartelle operative;
- PDF e altri output presenti in `output/`;
- griglia di valutazione e banner referenziati dalla configurazione;
- `manifest.json` con titolo, materia, seed, numero di versioni e file copiati.

Se vuoi anche svuotare le cartelle operative dopo aver creato l'archivio, esegui:

```bash
python archive_generation.py --reset-current
```

L'opzione `--reset-current` elimina i file correnti da `teaching-materials/`, `multiple-choice-question/`, `open-question/`, `practical-exercises/` e `output/`, lasciando al loro posto i `.gitkeep`.

## Ruolo di `prompt.md`

[`prompt.md`](./prompt.md) definisce il comportamento atteso da Codex quando costruisce o aggiorna i file sorgente.

Tra i vincoli attuali più importanti:

- il materiale va letto da `teaching-materials/`;
- `subject` in `config.json` non va cambiato automaticamente;
- `title` può essere aggiornato;
- le sezioni della prova attivate nel `config.json` devono riflettersi anche nella griglia di valutazione;
- le alternative delle multiple choice devono essere plausibili e non facilmente riconoscibili;
- alla fine del workflow Codex deve eseguire `python generate_verifiche.py`.

## Errori gestiti dallo script

Lo script interrompe la generazione con un errore esplicito se trova, tra le altre cose:

- `config.json` mancante o non valido;
- griglia di valutazione assente, disattivata o senza file valido;
- istruzioni assenti o senza contenuto valido;
- numero di alunni o versioni non valido;
- più versioni che alunni;
- punteggi incoerenti;
- totale punti superiore a `max_points`;
- file sorgente mancanti;
- ID richiesti ma non presenti;
- domande multiple insufficienti rispetto a `questions_per_exam`;
- domande con numero errato di opzioni;
- domande con zero o più di una risposta corretta;
- griglia di valutazione vuota o incoerente.

## Esempio di utilizzo

```bash
python generate_verifiche.py
```

Output atteso:

- PDF completo con tutte le copie della verifica
- sezione finale di soluzioni
- riepilogo a terminale con:
  - percorso del PDF
  - numero alunni
  - numero versioni
  - distribuzione copie
  - punteggio massimo configurato
  - punteggio totale attivo
