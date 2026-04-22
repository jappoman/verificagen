L'utente carichera' materiale didattico nella cartella `teaching-materials` sotto forma di PDF, slide, dispense, appunti o testi.
L'utente indichera' anche:

- il numero di alunni per cui generare la verifica.
- opzionalmente preferenze sulla composizione della verifica, per esempio:
  - abilitare o disabilitare una o piu' sezioni;
  - dare piu' peso a quiz, domande aperte o esercizi;
  - chiedere "solo domande a risposta multipla", "nessun esercizio", "focus sulle domande aperte", "piu' esercizi applicativi", ecc.
  - chiedere una verifica piu' teorica, piu' pratica o bilanciata.

Se l'utente non specifica il numero di alunni, devi usare come valore predefinito `30`.

Se l'utente non specifica preferenze sulla composizione della verifica, devi scegliere una distribuzione equilibrata e realistica tra le sezioni disponibili, coerente con il materiale didattico e con il tetto massimo di `9` punti.

Quando ricevi la richiesta di generare il contenuto della verifica, devi:

1. Analizzare tutto il materiale presente in `teaching-materials`.
   Se l'utente ha indicato pagine, sezioni o argomenti specifici, limita l'analisi a quel perimetro.
   Se non ha indicato nulla, usa tutto il materiale disponibile.

   Se l'utente ha espresso preferenze sulla composizione della verifica, devi tenerne conto fin dall'analisi e dalla selezione dei contenuti, privilegiando i materiali piu' adatti alle sezioni richieste.

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
- le opzioni errate devono essere davvero plausibili, cioe' credibili per uno studente che ha studiato in modo parziale o confuso;
- le opzioni errate non devono essere palesemente assurde, caricaturali, tecnicamente impossibili o immediatamente eliminabili senza ragionare;
- i distrattori devono essere vicini al contenuto corretto: devono appartenere allo stesso argomento, allo stesso contesto e allo stesso livello lessicale della risposta giusta;
- evita alternative sbagliate troppo lontane dal materiale, troppo generiche o costruite in modo tale da sembrare ovviamente false;
- evita anche il caso opposto: la risposta corretta non deve essere l'unica molto piu' precisa, lunga o specifica delle altre; il livello di dettaglio delle quattro opzioni deve essere il piu' possibile omogeneo;
- quando possibile, costruisci i distrattori a partire da errori realistici, confusioni frequenti, regole vicine, casi limite o inversioni plausibili dei concetti spiegati nel materiale;
- prima di considerare valida una domanda, verifica che uno studente medio non possa individuare la risposta corretta solo per contrasto di stile, lunghezza, tono o assurdita' delle alternative sbagliate;
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
- considera `9` come tetto massimo fisso dei punti distribuibili nella verifica.
- quindi il mix tra quiz, domande aperte ed esercizi deve essere gestito soprattutto tramite `config.json`, sia abilitando/disabilitando le sezioni sia variando quantita' e punteggi in modo coerente con la richiesta dell'utente.

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
- se l'utente chiede una composizione specifica della verifica, rifletterla esplicitamente in `config.json`;
- questo significa, a seconda dei casi:
- abilitare o disabilitare `multiple_choice`, `open_questions`, `practical_exercises`, `evaluation_grid`;
- aumentare o ridurre `questions_per_exam` per dare piu' o meno peso ai quiz;
- includere piu' o meno ID nelle domande aperte e negli esercizi;
- redistribuire i punti tra le sezioni attive, restando sempre entro `max_points = 9`;
- se l'utente chiede una verifica solo quiz, solo aperte, solo esercizi, oppure esclude esplicitamente una sezione, configurare il file in modo coerente senza lasciare sezioni attive inutilmente;
- se l'utente chiede "piu' peso" a una sezione, non limitarti ad aggiungere file: fai in modo che il peso emerga davvero nella configurazione finale attraverso quantita', attivazione e punteggi;
- compilare gli `include_ids` delle domande aperte e degli esercizi con gli ID effettivamente presenti;
- impostare `questions_per_exam` a un valore compatibile con il numero di domande multiple disponibili;
- impostare i punteggi in modo realistico;
- impostare sempre `max_points` a `9`;
- assicurarti che il totale dei punti attivi non superi mai `9`;
- distribuire i punti delle sezioni attive in modo realistico restando sempre entro il totale massimo di `9`;
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
- indicare come hai interpretato e applicato le preferenze dell'utente sulla composizione della verifica;
- segnalare se il numero di domande multiple generate potrebbe essere insufficiente rispetto a `config.json`;
- indicare dove e' stato salvato il PDF generato.

12. Non produrre la verifica definitiva impaginata nel messaggio.
    Il tuo compito e' popolare i file sorgente che usera' lo script `generate_verifiche.py`.
