import os
import json
import httpx
import asyncio
from typing import List, Dict, Any

class LLMClient:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "mock").lower()
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.grok_key = os.getenv("GROK_API_KEY")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3")

    async def generate(self, prompt: str, system_instruction: str = "") -> str:
        # Check provider overrides if keys are present
        active_provider = self.provider
        if active_provider == "mock":
            if self.gemini_key:
                active_provider = "gemini"
            elif self.openai_key:
                active_provider = "openai"
            elif self.grok_key:
                active_provider = "grok"

        if active_provider == "gemini" and self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_instruction if system_instruction else None
                )
                # Run in thread executor to avoid blocking the async event loop
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, 
                    lambda: model.generate_content(prompt)
                )
                return response.text
            except Exception as e:
                return f"[Errore Gemini API: {str(e)} - Caduta su Mock]"

        elif active_provider == "openai" and self.openai_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=self.openai_key)
                messages = []
                if system_instruction:
                    messages.append({"role": "system", "content": system_instruction})
                messages.append({"role": "user", "content": prompt})
                model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        model=model_name,
                        messages=messages
                    )
                )
                return response.choices[0].message.content
            except Exception as e:
                return f"[Errore OpenAI API: {str(e)} - Caduta su Mock]"

        elif active_provider == "grok" and self.grok_key:
            try:
                headers = {
                    "Authorization": f"Bearer {self.grok_key}",
                    "Content-Type": "application/json"
                }
                messages = []
                if system_instruction:
                    messages.append({"role": "system", "content": system_instruction})
                messages.append({"role": "user", "content": prompt})
                payload = {
                    "model": os.getenv("GROK_MODEL", "grok-beta"),
                    "messages": messages
                }
                async with httpx.AsyncClient() as client:
                    response = await client.post("https://api.x.ai/v1/chat/completions", json=payload, headers=headers, timeout=60.0)
                    if response.status_code == 200:
                        return response.json()["choices"][0]["message"]["content"]
                    else:
                        return f"[Errore Grok HTTP {response.status_code}: {response.text}]"
            except Exception as e:
                return f"[Errore Grok: {str(e)}]"

        elif active_provider == "ollama":
            try:
                payload = {
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "system": system_instruction,
                    "stream": False
                }
                async with httpx.AsyncClient() as client:
                    response = await client.post(self.ollama_url, json=payload, timeout=60.0)
                    if response.status_code == 200:
                        return response.json()["response"]
                    else:
                        return f"[Errore Ollama HTTP {response.status_code}: {response.text}]"
            except Exception as e:
                return f"[Errore Ollama: {str(e)}]"

        # Default fallback: Intelligent mock simulator based on prompt analysis
        return self._generate_mock(prompt, system_instruction)

    def _generate_mock(self, prompt: str, system_instruction: str) -> str:
        # Extract keywords to make the mock responses look realistic
        is_todo = "todo" in prompt.lower() or "compiti" in prompt.lower()
        is_ticket = "ticket" in prompt.lower() or "bug" in prompt.lower() or "errore" in prompt.lower() or "segnalazione" in prompt.lower()

        if "CEO" in system_instruction:
            if is_ticket:
                return "### Decisione Strategica del CEO\n\nHo preso in carico la segnalazione dell'utente riguardante il bug. Ho istruito il Product Manager per inserirla immediatamente in cima al backlog di R&D con priorità MASSIMA. Dobbiamo risolvere questo problema per proteggere la fiducia degli utenti. Procedere all'istante."
            return "### Direttiva Strategica del CEO\n\nIniziamo lo sviluppo del nuovo prodotto: una **Todo App Collaborativa Premium**. Questo prodotto aiuterà gli utenti ad organizzare le loro attività quotidiane con un'interfaccia ad alte prestazioni. PM, procedi con la stesura del PRD focalizzandoti su usabilità e semplicità."

        elif "Product Manager" in system_instruction:
            if is_ticket:
                return "### PRD Addendum: Bug Fix - Errore di Visualizzazione\n\n**Descrizione del problema**: Gli utenti segnalano problemi quando cliccano velocemente per completare i task. \n\n**Requisiti di Fix**:\n- [REQ-BUG-01]: Impedire doppie chiamate al toggle del completamento.\n- [REQ-BUG-02]: Aggiungere feedback visivo (animazione di transizione) per lo stato di caricamento."
            return """# Product Requirement Document (PRD) - Todo App Premium

**Stato**: `Approvato`
**Versione**: 1.0

## 1. Obiettivo del Prodotto
Creare una Todo App ad alte prestazioni, con design premium, che permetta agli utenti di gestire le attività quotidiane con animazioni fluide e memorizzazione locale persistente.

## 2. Requisiti Funzionali
*   **REQ-001**: L'utente deve poter aggiungere un nuovo task specificando titolo e priorità (Alta, Media, Bassa).
*   **REQ-002**: L'utente deve poter completare un task cliccando su un checkbox circolare animato.
*   **REQ-003**: L'utente deve poter eliminare un task con un'animazione fade-out.
*   **REQ-004**: I dati devono essere salvati nel localStorage per evitare perdite di informazioni.
"""

        elif "UX Designer" in system_instruction:
            if is_ticket:
                return "### UX Audit per Bug Fix\n\n**Problema**: Mancanza di feedback nel toggle dei task.\n\n**Linee Guida di Risoluzione**:\n- Aggiungere un effetto di rimbalzo (`scale(0.95)`) al click.\n- Cambiare il colore del cerchio da grigio bordato a verde brillante (`#10b981`) con una transizione di `0.2s`."
            return """# UX Design System & Wireframes - Todo App Premium

## 1. Palette Colori (Aesthetics Premium)
*   **Background**: Deep Dark (`#0b0f19`) con gradiente radiale sfumato verso `#1e1b4b` (Indigo).
*   **Card/Container**: Vetro satinato (`rgba(17, 24, 39, 0.7)`) con bordo semi-trasparente (`rgba(255, 255, 255, 0.08)`) e sfocatura `backdrop-filter: blur(12px)`.
*   **Accent Color**: Neon Violet (`#8b5cf6`) e Emerald Green (`#10b981`) per i completamenti.

## 2. Layout & Spacing
- Layout centrale a card singola con angoli arrotondati (`border-radius: 20px`).
- Animazioni micro-interattive su hover (spostamento in alto di `2px` ed effetto bagliore).
"""

        elif "Tech Lead" in system_instruction:
            if is_ticket:
                return """# System Design Spec: Bug Fix Toggle
**Stato**: `In Corso`

## Modifiche Architetturali:
1. Introdurre uno stato `isUpdating` nel componente React dei task per disabilitare il click durante le modifiche asincrone.
2. Aggiungere una funzione helper `debounce` per prevenire click multipli."""
            return """# System Architecture Document (SAD) - Todo App Premium

## 1. Stack Tecnologico
*   **Frontend**: React (Functional Components con Hooks)
*   **Styling**: Vanilla CSS (CSS Variables per il tema scuro, Flexbox e Grid per il layout)
*   **Persistenza**: LocalStorage API integrata in un hook custom `useLocalStorage`.

## 2. Task Tecnici di Sviluppo
- [TASK-1] Creare la struttura del componente e configurare le CSS variables.
- [TASK-2] Implementare l'hook custom `useLocalStorage` per lo stato persistente.
- [TASK-3] Creare i componenti `TodoInput`, `TodoList` e `TodoItem` con relative micro-animazioni.
"""

        elif "Developer" in system_instruction:
            if is_todo:
                return """// CODE_START
// App.jsx
import React, { useState, useEffect } from 'react';
import './App.css';

export default function App() {
  const [todos, setTodos] = useState(() => {
    const saved = localStorage.getItem('xsoft_todos');
    return saved ? JSON.parse(saved) : [
      { id: 1, text: "Configurare l'ambiente di Xsoft", completed: true, priority: 'Alta' },
      { id: 2, text: "Testare la comunicazione degli agenti", completed: false, priority: 'Alta' }
    ];
  });
  const [input, setInput] = useState('');
  const [priority, setPriority] = useState('Media');

  useEffect(() => {
    localStorage.setItem('xsoft_todos', JSON.stringify(todos));
  }, [todos]);

  const addTodo = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    setTodos([...todos, { id: Date.now(), text: input, completed: false, priority }]);
    setInput('');
  };

  const toggleTodo = (id) => {
    setTodos(todos.map(t => t.id === id ? { ...t, completed: !t.completed } : t));
  };

  const deleteTodo = (id) => {
    setTodos(todos.filter(t => t.id !== id));
  };

  return (
    <div className="todo-app-container">
      <div className="glass-card">
        <h1 className="title-gradient">Xsoft Todo Premium</h1>
        <form onSubmit={addTodo} className="todo-form">
          <input 
            type="text" 
            placeholder="Qual è il prossimo task?" 
            value={input} 
            onChange={(e) => setInput(e.target.value)}
            className="todo-input"
          />
          <select value={priority} onChange={(e) => setPriority(e.target.value)} className="todo-select">
            <option value="Alta">Alta</option>
            <option value="Media">Media</option>
            <option value="Bassa">Bassa</option>
          </select>
          <button type="submit" className="todo-button">Aggiungi</button>
        </form>
        <div className="todo-list">
          {todos.map(todo => (
            <div key={todo.id} className={`todo-item ${todo.completed ? 'completed' : ''}`}>
              <div className="todo-left" onClick={() => toggleTodo(todo.id)}>
                <span className={`checkbox-circle ${todo.completed ? 'checked' : ''}`} />
                <span className="todo-text">{todo.text}</span>
              </div>
              <div className="todo-right">
                <span className={`priority-badge ${todo.priority.toLowerCase()}`}>{todo.priority}</span>
                <button onClick={() => deleteTodo(todo.id)} className="delete-btn">&times;</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
// CODE_END"""
            elif is_ticket:
                return """// CODE_START
// App.jsx (Patch Applicata per prevenire spam click e raddoppi)
import React, { useState, useEffect } from 'react';
import './App.css';

export default function App() {
  const [todos, setTodos] = useState(() => {
    const saved = localStorage.getItem('xsoft_todos');
    return saved ? JSON.parse(saved) : [];
  });
  const [input, setInput] = useState('');
  const [priority, setPriority] = useState('Media');
  const [isUpdating, setIsUpdating] = useState(false); // FIX: stato di blocco click

  useEffect(() => {
    localStorage.setItem('xsoft_todos', JSON.stringify(todos));
  }, [todos]);

  const addTodo = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    setTodos([...todos, { id: Date.now(), text: input, completed: false, priority }]);
    setInput('');
  };

  const toggleTodo = async (id) => {
    if (isUpdating) return; // FIX: previene doppio trigger veloce
    setIsUpdating(true);
    
    // Simula una breve latenza asincrona per animazione fluida
    setTodos(todos.map(t => t.id === id ? { ...t, completed: !t.completed } : t));
    await new Promise(resolve => setTimeout(resolve, 150));
    setIsUpdating(false);
  };

  const deleteTodo = (id) => {
    setTodos(todos.filter(t => t.id !== id));
  };

  return (
    <div className="todo-app-container">
      <div className="glass-card">
        <h1 className="title-gradient">Xsoft Todo Premium</h1>
        <form onSubmit={addTodo} className="todo-form">
          <input 
            type="text" 
            placeholder="Qual è il prossimo task?" 
            value={input} 
            onChange={(e) => setInput(e.target.value)}
            className="todo-input"
          />
          <select value={priority} onChange={(e) => setPriority(e.target.value)} className="todo-select">
            <option value="Alta">Alta</option>
            <option value="Media">Media</option>
            <option value="Bassa">Bassa</option>
          </select>
          <button type="submit" className="todo-button">Aggiungi</button>
        </form>
        <div className="todo-list">
          {todos.map(todo => (
            <div key={todo.id} className={`todo-item ${todo.completed ? 'completed' : ''}`}>
              <div className="todo-left" onClick={() => toggleTodo(todo.id)}>
                <span className={`checkbox-circle ${todo.completed ? 'checked' : ''}`} />
                <span className="todo-text">{todo.text}</span>
              </div>
              <div className="todo-right">
                <span className={`priority-badge ${todo.priority.toLowerCase()}`}>{todo.priority}</span>
                <button onClick={() => deleteTodo(todo.id)} className="delete-btn">&times;</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
// CODE_END"""

        elif "QA" in system_instruction:
            if is_ticket:
                return """# Test Suite Execution Report: Hotfix Validation
**Stato**: `SUPERATO`

## Test Eseguiti:
- **Test-01: Toggle Veloce**: Cliccato ripetutamente il checkbox per completare il task. **Risultato: Successo** (l'input viene ignorato durante l'animazione, nessun loop o errore nello stato).
- **Test-02: Persistenza del fix**: I dati rimangono corretti anche dopo ricaricamento. **Risultato: Successo**."""
            return """# Test Suite Execution Report - Todo App Premium
**Stato**: `SUPERATO`

## Test Funzionali:
- **Test-01: Aggiunta Task**: Inserito task 'Compilare Wiki'. **Risultato: Successo** (il task appare nella lista).
- **Test-02: Toggle Completamento**: Cliccato checkbox. **Risultato: Successo** (cambia stato visivo).
- **Test-03: Persistenza LocalStorage**: Ricaricata la pagina. **Risultato: Successo** (stato preservato).
"""

        elif "Support" in system_instruction:
            if is_ticket:
                return "### Risposta Frontline Support AI\n\nGentile utente, grazie per la segnalazione! Ho rilevato un errore nel toggle del completamento dei task. Ho inoltrato il problema direttamente al nostro Developer Agent (2° Livello - Engineering). Il fix è in corso di scrittura e verrà distribuito a breve. Riceverà una notifica automatica appena sarà online."
            return "### Messaggio Supporto Frontline\n\nBenvenuto in Xsoft! Come posso aiutarti oggi? Se hai riscontrato un bug o desideri richiedere una nuova funzionalità, inserisci pure la tua richiesta qui. Verrà inoltrata istantaneamente al reparto di competenza."

        elif "DevOps" in system_instruction:
            return """# DevOps Deployment Log
**Milestone**: `Deploy Eseguito`
**Ambiente**: `Produzione / Staging`

## Log di rilascio:
- Copia dei sorgenti `App.jsx` e `App.css` nella sandbox di produzione.
- Verifica build di Vite: `npm run build` completato in 1.4s.
- Rilascio asincrono completato con successo. L'applicazione è ora accessibile per gli utenti finali!"""

        return f"[Risposta Simulatore Agente per input: '{prompt[:40]}...']"
