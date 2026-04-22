# Verificagen

Generatore di verifiche in PDF a partire da file strutturati e da una configurazione centrale in `config.json`.

Per il workflow con Codex, il numero di versioni puo' essere calcolato automaticamente a partire dal numero di alunni. La regola consigliata e' `ceil(numero_alunni / 3)`.

## Workflow

1. Metti il materiale didattico in `teaching-materials/`.
2. Chiedi a Codex di analizzare il materiale seguendo il file [`prompt`](./prompt).
3. Codex popola:
   - `multiple-choice-question/*.json`
   - `open-question/*.json`
   - `practical-exercises/*.json`
   - opzionalmente `evaluation-grid/*.json`
4. Configura cosa attivare in [`config.json`](./config.json).
5. Genera il PDF con:

```bash
python generate_verifiche.py
```

L'output finisce in `output/verifiche_generate.pdf`.

## Cosa gestisce lo script

- banner nell'intestazione;
- campi alunno, classe e data;
- istruzioni iniziali configurabili;
- griglia di valutazione opzionale;
- quiz a risposta multipla con domande e risposte scrambolate;
- domande aperte ed esercizi da JSON;
- controllo del punteggio massimo configurato;
- piu' versioni della verifica in un unico PDF;
- tante copie quante sono gli alunni configurati, distribuite nel modo piu' equo possibile tra le versioni;
- copie ordinate in modo interlecciato nel PDF, cioe' un primo giro di versioni, poi un secondo giro, e cosi' via;
- sezione finale con soluzioni, fonti e chiavi rapide di correzione per ogni ID verifica.

## Formati dati

### Multiple choice

JSON con chiave `questions`, dove ogni domanda contiene:

- `id`
- `topic`
- `prompt`
- `difficulty`
- `source`
- `explanation`
- `options` con 4 elementi, ciascuno con `id`, `text`, `is_correct`

### Domande aperte ed esercizi

Un file JSON per elemento, con:

- `id`
- `prompt`
- `points`
- `answer_space_lines`
- `solution.source`
- `solution.blocks`

Blocchi soluzione supportati:

- `paragraph`
- `bullets`
- `preformatted`
- `image`
