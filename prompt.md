L'utente carichera' materiale didattico nella cartella `teaching-materials` sotto forma di PDF, slide, dispense, appunti o testi.
L'utente indichera' anche:

- il numero di alunni per cui generare la verifica.

Se l'utente non specifica il numero di alunni, devi usare come valore predefinito `30`.

Quando ricevi la richiesta di generare il contenuto della verifica, devi:

1. Analizzare tutto il materiale presente in `teaching-materials`.
   Se l'utente ha indicato pagine, sezioni o argomenti specifici, limita l'analisi a quel perimetro.
   Se non ha indicato nulla, usa tutto il materiale disponibile.

2. Individuare:

- i concetti teorici principali;
- i contenuti adatti a domande a risposta multipla;
- i contenuti adatti a domande aperte;
- i contenuti adatti a esercizi applicativi;
- le fonti precise delle risposte o delle soluzioni nel materiale didattico.

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

Regole:

- ogni domanda deve avere 4 opzioni;
- una sola risposta corretta;
- il testo deve essere chiaro, scolastico e non ambiguo;
- le opzioni errate devono essere plausibili;
- `source` deve indicare file + pagina/sezione da cui deriva la risposta;
- `explanation` deve contenere una spiegazione breve utile in correzione;
- `options[].is_correct` deve marcare una sola opzione vera;
- genera abbastanza domande da permettere allo script di estrarne sottoinsiemi diversi.

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

Regole:

- una domanda = un solo concetto o nucleo teorico;
- stile tipo "Spiega", "Descrivi", "Illustra";
- niente sottodomande spezzate salvo casi davvero necessari;
- `points` deve essere coerente con difficolta' e lunghezza della risposta;
- la soluzione deve essere sufficientemente completa per correggere velocemente.

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

Regole:

- l'esercizio deve richiedere applicazione concreta dei concetti;
- puo' includere punti interni solo se resta un compito unitario;
- la soluzione deve essere completa, utilizzabile in fase di correzione;
- se serve uno schema, usa un blocco `preformatted`;
- se l'utente fornisce immagini o schemi esterni da includere, puoi prevedere anche blocchi:
  `{"type": "image", "path": "percorso/relativo/file.png"}`

7. Quando generi i contenuti, devi tenere presente che lo script finale:

- puo' attivare o disattivare ciascuna sezione da `config.json`;
- mostra il punteggio di ogni domanda aperta o esercizio;
- assegna punteggio fisso alle multiple choice dal config;
- controlla che il totale dei punti attivi non superi il massimo consentito.

8. Devi anche aggiornare `config.json` nel modo piu' consono rispetto al materiale generato, lasciandolo pronto per l'esecuzione immediata dello script.
   Nel configurarlo devi:

- scegliere un titolo coerente con argomento e materiale;
- impostare `number_of_students` in base al numero di alunni indicato dall'utente;
- se il numero di alunni non e' stato indicato, impostare `number_of_students` a `30`;
- calcolare automaticamente `number_of_versions` in modo proporzionato al numero di alunni;
- usare una proporzione sensata che produca un buon numero di varianti;
- rispettare il principio pratico seguente: con 30 alunni devono esserci almeno 10 versioni diverse;
- come regola di default, usa `number_of_versions = ceil(number_of_students / 3)`, salvo casi particolari in cui il materiale disponibile non permetta una differenziazione sensata;
- in generale, il numero di versioni deve essere abbastanza alto da differenziare bene gli alunni vicini, ma non cosi' alto da rendere inutile la ripetizione delle versioni;
- attivare o disattivare quiz, domande aperte, esercizi e griglia in modo coerente con i file che hai creato;
- compilare gli `include_ids` delle domande aperte e degli esercizi con gli ID effettivamente presenti;
- impostare `questions_per_exam` a un valore compatibile con il numero di domande multiple disponibili;
- impostare i punteggi in modo realistico;
- assicurarti che il totale dei punti attivi non superi `max_points`;
- assicurarti che il numero di versioni non superi il numero di alunni;
- lasciare una configurazione che permetta allo script di generare tante copie quante sono gli alunni, distribuite il piu' equamente possibile tra le versioni;
- lasciare una configurazione che produca nel PDF un ordine interlecciato delle copie, cioe' prima un giro completo delle versioni, poi un secondo giro e cosi' via, in modo che studenti vicini ricevano versioni diverse;
- lasciare percorsi e nomi file corretti e gia' utilizzabili dallo script.

9. I contenuti devono essere progettati per una verifica realistica, svolgibile da uno studente medio nel tempo indicato o implicato dal materiale.
   Le domande devono essere:

- pertinenti;
- non ridondanti;
- distribuite tra teoria e applicazione;
- ben bilanciate per difficolta'.

10. Quando tutti i file sono stati preparati, devi eseguire anche lo script:

```bash
python generate_verifiche.py
```

Se l'esecuzione fallisce, devi correggere i file necessari e riprovare finche' la generazione non riesce oppure finche' non emerge un blocco reale non risolvibile automaticamente.

11. Al termine del lavoro non devi limitarti a dire che hai analizzato il materiale.
    Devi:

- aggiornare i file nelle cartelle corrette;
- aggiornare `config.json`;
- eseguire lo script;
- riassumere cosa hai creato;
- indicare eventuali assunzioni;
- segnalare se il numero di domande multiple generate potrebbe essere insufficiente rispetto a `config.json`;
- indicare dove e' stato salvato il PDF generato.

12. Non produrre la verifica definitiva impaginata nel messaggio.
    Il tuo compito e' popolare i file sorgente che usera' lo script `generate_verifiche.py`.
