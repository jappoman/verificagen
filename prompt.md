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
- opzionalmente `evaluation-grid/*.json` se l'utente chiede anche una griglia nuova
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
- evita alternative palesemente assurde, troppo generiche o immediatamente eliminabili;
- evita che la risposta corretta si distingua per lunghezza, precisione o stile rispetto alle altre;
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
- non modificare mai `instructions.content`: va preservato esattamente com'è;
- attivare o disattivare quiz, domande aperte ed esercizi in modo coerente con i file creati;
- non disattivare la griglia di valutazione se è già presente in `config.json`; puoi aggiornarne il file solo se l'utente chiede esplicitamente una nuova griglia;
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
