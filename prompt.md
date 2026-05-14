L'utente caricherà materiale didattico nella cartella `teaching-materials` sotto forma di PDF, slide, dispense, appunti o testi.

L'utente può indicare anche:

- opzionalmente il titolo della verifica;
- opzionalmente quali parti del materiale usare, anche file per file, specificando per esempio pagine, intervalli di pagine, sezioni, capitoli o argomenti;
- opzionalmente preferenze sulla composizione della verifica, per esempio:
  - abilitare o disabilitare una o più sezioni;
  - dare più peso a quiz, domande aperte o esercizi;
  - chiedere "solo domande a risposta multipla", "nessun esercizio", "focus sulle domande aperte", "più esercizi applicativi";
  - chiedere una verifica più teorica, più pratica o bilanciata.

Se l'utente non specifica preferenze sulla composizione della verifica, devi scegliere una distribuzione equilibrata e realistica tra le sezioni disponibili, coerente con il materiale didattico e con i vincoli già definiti in `config.json`.

Quando ricevi la richiesta di generare il contenuto della verifica, devi:

0. Preparare il materiale didattico prima dell'analisi, quando serve.
   Prima controlla i file presenti in `teaching-materials`.
   Se ci sono PDF o immagini, oppure se non sei certo che i PDF contengano testo estraibile, esegui:

```bash
python prepare_teaching_materials.py
```

   Poi analizza prima di tutto i file Markdown generati in `teaching-materials/_extracted-text`.
   Questi file contengono il testo estratto dai PDF testuali e, quando disponibile, il testo OCR dei PDF scannerizzati o delle immagini.
   Se il comando segnala che `tesseract` non e' installato, oppure se alcune pagine risultano senza testo estratto, devi avvisare l'utente prima di generare la verifica: in quel caso il materiale visivo potrebbe non essere stato letto correttamente.
   Quando citi le fonti nei JSON, usa comunque il nome del file originale e la pagina/sezione, non il solo file Markdown estratto.

1. Analizzare il materiale in `teaching-materials`.
   Se l'utente ha indicato vincoli specifici, devi rispettarli file per file.
   Se per un file non ha indicato alcun vincolo, devi usare tutto quel file.
   Se non ha indicato alcun vincolo per nessun file, devi usare tutto il materiale disponibile.

2. Individuare nel materiale:
- i concetti teorici principali;
- i contenuti adatti a domande a risposta multipla;
- i contenuti adatti a domande aperte;
- i contenuti adatti a esercizi applicativi;
- le fonti precise delle risposte o delle soluzioni.

3. Popolare o aggiornare i file strutturati del progetto, senza scrivere la verifica finale in forma libera.
   Devi generare contenuti nei formati richiesti dal repository:
- `multiple-choice-question/*.json`
- `open-question/*.json`
- `practical-exercises/*.json`
- `evaluation-grid/*.json` se serve aggiornare la griglia esistente o crearne una nuova su richiesta dell'utente
- `config.json`

4. Per le domande a risposta multipla, devi produrre o aggiornare un file JSON nel formato seguente:

```json
{
  "questions": [
    {
      "id": "mc_argomento_01",
      "topic": "argomento",
      "prompt": "Testo della domanda.",
      "difficulty": "facile",
      "source": "Nome file, pagina o sezione da cui deriva la risposta corretta",
      "explanation": "Breve spiegazione utile per la correzione",
      "options": [
        {
          "id": "A",
          "text": "Prima alternativa",
          "is_correct": false
        },
        {
          "id": "B",
          "text": "Seconda alternativa",
          "is_correct": true
        },
        {
          "id": "C",
          "text": "Terza alternativa",
          "is_correct": false
        },
        {
          "id": "D",
          "text": "Quarta alternativa",
          "is_correct": false
        }
      ]
    }
  ]
}
```

Regole per le multiple choice:

- ogni domanda deve avere 4 opzioni;
- una sola risposta corretta;
- il testo deve essere chiaro, scolastico e non ambiguo;
- la domanda deve essere autosufficiente e naturale, senza riferimenti metatestuali come "nel materiale", "nella slide", "nel PDF";
- le opzioni errate devono essere plausibili, vicine al contenuto corretto e costruite su errori realistici;
- le opzioni errate non devono essere "segnalatori" della risposta giusta: non devono risultare palesemente assurde, caricaturali, troppo estreme, fuori contesto o banalmente false;
- i distrattori devono assomigliare davvero alla risposta corretta per categoria, registro linguistico, livello di precisione, lunghezza e struttura sintattica;
- quando possibile, costruisci i distrattori partendo da:
  - un dettaglio quasi corretto ma leggermente sbagliato;
  - una regola vera applicata nel contesto sbagliato;
  - un termine tecnico vicino ma non esatto;
  - una procedura simile ma con un passaggio scorretto;
  - un'inversione realistica di causa/effetto, funzione/strumento, vantaggio/limite;
- almeno uno o due distrattori dovrebbero essere abbastanza credibili da poter trarre in inganno uno studente che ha studiato in modo superficiale;
- se la risposta corretta è molto specifica, anche le alternative sbagliate devono essere specifiche e credibili: evita di affiancarle a risposte generiche, vaghe o evidentemente "buttate lì";
- se la risposta corretta usa una formulazione breve, anche i distrattori dovrebbero avere una brevità comparabile; se è una frase completa, anche i distrattori dovrebbero esserlo;
- evita set di opzioni in cui una sola alternativa appartiene davvero alla stessa categoria logica delle altre tre;
- evita il pattern "1 risposta seria + 3 risposte sciocche": tutte e quattro devono sembrare inizialmente possibili a una lettura rapida;
- se una domanda usa parole come "sempre", "solo", "mai", "automaticamente", "obbligatoriamente", usale con molta prudenza nelle opzioni, perché spesso rendono i distrattori troppo facili da scartare;
- evita alternative palesemente assurde, troppo generiche o immediatamente eliminabili;
- evita che la risposta corretta si distingua per lunghezza, precisione o stile rispetto alle altre;
- prima di salvare una domanda, fai un controllo qualitativo sulle alternative e riscrivile se la risposta corretta si riconosce troppo facilmente al primo colpo;
- in particolare, scarta e riscrivi una batteria di opzioni se succede una di queste cose:
  - una risposta è nettamente più precisa, tecnica o ben scritta delle altre;
  - una o più alternative sono chiaramente fuori argomento;
  - una o più alternative sono troppo corte o troppo lunghe rispetto alle altre;
  - basta il buon senso, senza conoscere il contenuto, per eliminare subito due o tre opzioni;
  - i distrattori non rappresentano errori realistici che uno studente potrebbe davvero fare;
- il livello di qualità desiderato è questo: leggendo le quattro opzioni, uno studente preparato deve dover ragionare per scegliere; uno studente poco preparato non deve poter individuare la risposta giusta solo "a naso";
- `source` deve indicare file più pagina o sezione;
- `explanation` deve essere breve ma utile alla correzione;
- `options[].is_correct` deve marcare una sola opzione vera;
- anche se l'utente specifica un numero preciso di domande a risposta multipla per ogni verifica, non devi limitarti a generare solo quel numero di domande nel file sorgente;
- devi generare un pool più ampio di domande multiple rispetto a `questions_per_exam`, così lo script può costruire versioni realmente differenti e non solo con ordine o opzioni mescolati;
- se l'utente specifica un numero preciso di domande, quel numero va interpretato come numero di quiz da includere in ciascuna verifica, non come limite massimo del pool totale da generare;
- se l'utente non specifica un numero preciso, genera comunque un pool di domande sufficientemente ampio rispetto al bilanciamento scelto e al numero di versioni previsto in `config.json`;
- evita quindi configurazioni in cui il pool totale delle domande multiple coincide con `questions_per_exam`, salvo richiesta esplicita dell'utente o impossibilità reale dovuta al materiale disponibile;
- se, nonostante questo criterio, il materiale consente solo un pool limitato, devi segnalarlo chiaramente nel riepilogo finale.

5. Per le domande aperte, devi creare un file JSON per domanda dentro `open-question`.
   Formato richiesto:

```json
{
  "id": "open_nome_progressivo",
  "prompt": "Domanda aperta chiara e singola.",
  "points": 2,
  "solution": {
    "source": "Nome file, pagina o sezione",
    "blocks": [
      {
        "type": "paragraph",
        "content": "Soluzione discorsiva."
      },
      {
        "type": "bullets",
        "items": ["Punto chiave 1", "Punto chiave 2"]
      }
    ]
  }
}
```

Regole per le domande aperte:

- una domanda deve coprire un solo concetto o nucleo teorico;
- usa formulazioni come "Spiega", "Descrivi", "Illustra";
- evita sottodomande spezzate salvo casi davvero necessari;
- `points` deve essere coerente con difficoltà e lunghezza della risposta;
- la soluzione deve essere abbastanza completa da permettere una correzione veloce.

6. Per gli esercizi, devi creare un file JSON per esercizio dentro `practical-exercises`.
   Formato richiesto:

```json
{
  "id": "exercise_nome_progressivo",
  "prompt": "Testo dell'esercizio.",
  "points": 2.5,
  "solution": {
    "source": "Nome file, pagina o sezione",
    "blocks": [
      {
        "type": "paragraph",
        "content": "Spiegazione della soluzione."
      },
      {
        "type": "preformatted",
        "content": "Schema o struttura testuale utile alla correzione"
      }
    ]
  }
}
```

Regole per gli esercizi:

- l'esercizio deve richiedere applicazione concreta dei concetti;
- può includere punti interni solo se resta un compito unitario;
- la soluzione deve essere completa e utilizzabile in correzione;
- se serve uno schema, usa un blocco `preformatted`;
- se l'utente fornisce immagini o schemi esterni da includere, puoi prevedere anche blocchi come `{"type": "image", "path": "percorso/relativo/file.png"}`.

7. Quando generi i contenuti, devi tenere presente che lo script finale:

- può attivare o disattivare ciascuna sezione da `config.json`;
- mostra il punteggio di ogni domanda aperta o esercizio;
- assegna il punteggio delle multiple choice da `config.json`;
- richiede sempre `points_wrong` negativo e pari a metà di `points_correct` per le multiple choice;
- usa `max_points` in `config.json` come limite complessivo della verifica.

8. Devi aggiornare `config.json` in modo coerente con il materiale generato, lasciandolo pronto per l'esecuzione dello script.
   Nel configurarlo devi:

- usare il titolo fornito dall'utente se presente; altrimenti ricavarlo dal materiale e dalla richiesta;
- non modificare il campo `subject` di `config.json`: la materia va sempre preservata così com'è già configurata;
- puoi aggiornare il titolo della verifica (`title`), ma non la materia (`subject`), salvo richiesta esplicita e separata dell'utente;
- le istruzioni della prova sono obbligatorie: in `config.json` deve sempre essere presente una sezione `instructions` valida con `instructions.content` non vuoto;
- non modificare mai `instructions.content`: va preservato esattamente com'è, salvo richiesta esplicita dell'utente;
- attivare o disattivare quiz, domande aperte ed esercizi in modo coerente con i file creati;
- nei `part_title` delle sezioni non inserire numerazioni fisse come "Parte 1", "Parte 2", "Parte 3": il prefisso numerico viene aggiunto automaticamente dal generatore in base alle sezioni effettivamente attive;
- la griglia di valutazione è obbligatoria: in `config.json` deve sempre essere presente una sezione `evaluation_grid` valida con un file referenziato da `evaluation_grid.path`;
- puoi aggiornarne il file solo se l'utente chiede esplicitamente una nuova griglia o se serve adeguare quella esistente alla composizione della prova;
- quando abiliti o disabiliti sezioni della prova in `config.json`, devi fare in modo che nella griglia di valutazione restino visibili solo le fasce corrispondenti alle sezioni attive;
- quindi: quiz attivi => fascia quiz visibile; domande aperte attive => fascia domande aperte visibile; esercizi attivi => fascia esercizi visibile; le altre fasce devono essere escluse dalla griglia finale;
- riflettere in `config.json` eventuali preferenze esplicite dell'utente sulla composizione della verifica;
- regolare quantità, ID inclusi e punteggi in modo realistico e coerente con `max_points`;
- impostare `questions_per_exam` in modo compatibile con il numero di domande multiple disponibili;
- impostare sempre `points_wrong` a metà in valore assoluto di `points_correct`, con segno negativo;
- non modificare i valori strutturali di `config.json` che definiscono la numerosità della generazione, come `number_of_students` e `number_of_versions`, salvo esplicita richiesta dell'utente;
- lasciare percorsi, nomi file e configurazione finale già utilizzabili dallo script.

9. I contenuti devono essere progettati per una verifica realistica, svolgibile da uno studente medio nel tempo indicato o implicato dal materiale.
   Le domande devono essere:

- pertinenti;
- non ridondanti;
- distribuite tra teoria e applicazione;
- ben bilanciate per difficoltà;
- scritte in un italiano corretto anche dal punto di vista ortografico e tipografico.

10. Quando scrivi domande, opzioni, soluzioni, spiegazioni e testi di configurazione, devi prestare particolare attenzione alle lettere accentate italiane.

Regole:

- usa correttamente le vocali accentate come `è`, `à`, `ì`, `ò`, `ù` quando richieste;
- non sostituire gli accenti con apostrofi: evita forme scorrette come `e'`, `poiche'`, `cosi'`, `piu'`;
- controlla sempre il testo finale prima di salvare i file JSON o Markdown;
- mantieni questa attenzione in tutti i file generati o aggiornati nel repository.

11. Quando tutti i file sono stati preparati, devi eseguire anche lo script:

```bash
python generate_verifiche.py
```

Se l'esecuzione fallisce, devi correggere i file necessari e riprovare finché la generazione non riesce oppure finché non emerge un blocco reale non risolvibile automaticamente.

12. Al termine del lavoro non devi limitarti a dire che hai analizzato il materiale.
    Devi:

- aggiornare i file nelle cartelle corrette;
- aggiornare `config.json`;
- eseguire lo script;
- riassumere cosa hai creato;
- indicare eventuali assunzioni;
- indicare come hai interpretato e applicato le preferenze dell'utente sulla composizione della verifica;
- segnalare se il numero di domande multiple generate potrebbe essere insufficiente rispetto a `config.json`;
- indicare dove è stato salvato il PDF generato.

13. Non produrre la verifica definitiva impaginata nel messaggio.
    Il tuo compito è popolare i file sorgente che userà lo script `generate_verifiche.py`.
