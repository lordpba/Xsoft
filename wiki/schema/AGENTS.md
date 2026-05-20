# Schema di Governance degli Agenti (AGENTS.md)

Questo documento definisce le regole e le convenzioni che gli agenti AI di Xsoft devono seguire per mantenere e aggiornare la Wiki aziendale.

---

## 🧭 Regole Generali di Scrittura
1.  **Nessuna Sovrascrittura Destrutturata**: Non eliminare intere sezioni scritte da altri agenti a meno che non ci sia una contraddizione o una revisione esplicita approvata.
2.  **Tracciamento nel Log**: Ogni volta che un agente crea o modifica un file, deve aggiungere un'entrata nel file `/wiki/log.md` con la data corrente e il formato:
    ```markdown
    ## [AAAA-MM-GG] nome_agente | descrizione_azione
    ```
3.  **Aggiornamento dell'Index**: Qualsiasi nuovo file deve essere referenziato e catalogato nel file `/wiki/index.md` sotto la categoria appropriata.

---

## 📂 Convenzioni per Ruolo

### 1. Product Manager Agent (PM)
*   **Destinazione**: `/wiki/products/[prodotto]_prd.md`
*   **Responsabilità**: Definire le specifiche funzionali del prodotto, le user stories e i requisiti minimi.
*   **Output obbligatorio**: Requisiti contrassegnati da ID univoci (es. `REQ-001`) per consentire il tracciamento del QA.

### 2. UX Designer Agent
*   **Destinazione**: `/wiki/products/[prodotto]_ux.md`
*   **Responsabilità**: Redigere il Design System (colori primari/secondari, font, spacing, regole di transizione) e definire i wireframe logici.
*   **Visual QA**: Scrive le sue recensioni estetiche e i feedback di usabilità sul codice frontend in `/wiki/operations/ux_reviews.md`.

### 3. Architect / Tech Lead Agent
*   **Destinazione**: `/wiki/architecture/[prodotto]_arch.md`
*   **Responsabilità**: Tradurre il PRD e il file UX in specifiche di sistema, definire il database schema, gli endpoint API e la scomposizione in task tecnici.
*   **Output obbligatorio**: Tabella dei task tecnici assegnabili al Developer con flag di completamento.

### 4. Developer Agent
*   **Destinazione**: `/wiki/operations/hotfixes.md` (in caso di bug fix istantanei)
*   **Responsabilità**: Creare il codice sorgente reale nelle cartelle del progetto.
*   **Supporto di 2° Livello**: Documenta l'analisi del bug e la patch applicata.

### 5. QA Agent (Quality Assurance)
*   **Destinazione**: `/wiki/operations/test_reports.md`
*   **Responsabilità**: Eseguire test automatici sul codice e compilare report dettagliati. Se un test fallisce, deve aprire una segnalazione nel report e notificare il Developer.

### 6. Frontline Support AI
*   **Destinazione**: `/wiki/operations/tickets.md`
*   **Responsabilità**: Tracciare lo stato dei ticket dei clienti. Gestisce i ticket come: `[Aperto]`, `[In Corso - R&D]`, `[Risolto]`.

---

## 🔍 Regole di Risoluzione dei Conflitti
*   Se due agenti rilevano una contraddizione di requisiti o architettura, l'agente che la rileva deve contrassegnarla con un avviso (es. `> [!WARNING] Contradiction Detected: ...`) nel file index.md e notificare il **CEO Agent**, il quale richiederà l'intervento umano (Board/Owner) se il conflitto è strategico.
