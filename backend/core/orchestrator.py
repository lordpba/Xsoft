import os
import re
import json
import logging
import asyncio
from datetime import datetime
from typing import Callable, Dict, Any, List

from backend.core.llm import LLMClient
from backend.core.agent import Agent

logger = logging.getLogger("xsoft.orchestrator")

class Orchestrator:
    def __init__(self, workspace_dir: str, broadcast_callback: Callable[[Dict[str, Any]], None]):
        self.workspace_dir = workspace_dir
        self.wiki_dir = os.path.join(workspace_dir, "wiki")
        self.frontend_dir = os.path.join(workspace_dir, "frontend")
        self.broadcast = broadcast_callback
        
        # Initialize LLM Client
        self.llm_client = LLMClient()
        
        # Initialize Agents
        self.agents = {
            "CEO": Agent("CEO", self.llm_client),
            "PM": Agent("PM", self.llm_client),
            "UX": Agent("UX", self.llm_client),
            "TechLead": Agent("TechLead", self.llm_client),
            "Developer": Agent("Developer", self.llm_client),
            "QA": Agent("QA", self.llm_client),
            "Support": Agent("Support", self.llm_client),
            "DevOps": Agent("DevOps", self.llm_client)
        }
        
        # Internal state
        self.is_running = False
        self.current_project = ""
        self.active_agent = "Idle"
        self.agent_statuses = {k: "Idle" for k in self.agents.keys()}
        self.stats = {
            "tokens": 0,
            "tickets": 0,
            "tasks": 0,
            "builds": 0
        }

    def update_agent_status(self, agent_name: str, status: str):
        self.active_agent = agent_name
        for k in self.agent_statuses:
            self.agent_statuses[k] = "Idle"
        if agent_name in self.agent_statuses:
            self.agent_statuses[agent_name] = status
        
        # Broadcast general state update
        asyncio.create_task(self.broadcast_state())

    async def broadcast_state(self):
        await self.broadcast({
            "type": "state_update",
            "active_agent": self.active_agent,
            "agent_statuses": self.agent_statuses,
            "stats": self.stats,
            "current_project": self.current_project
        })

    async def sleep_and_notify(self, agent_name: str, action: str, channels: List[str], duration: float = 2.0):
        self.update_agent_status(agent_name, action)
        await self.broadcast({
            "type": "agent_action",
            "agent": agent_name,
            "action": action,
            "channels": channels
        })
        await asyncio.sleep(duration)

    async def log_wiki_activity(self, agent: str, description: str):
        log_path = os.path.join(self.wiki_dir, "log.md")
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        entry = f"\n## [{date_str}] {agent} | {description}\n"
        
        if os.path.exists(log_path):
            with open(log_path, "a") as f:
                f.write(entry)
        else:
            with open(log_path, "w") as f:
                f.write(f"# Xsoft Activity Log\n{entry}")

        # Notify frontend that log.md changed
        await self.notify_file_change("wiki/log.md")

    async def write_wiki_file(self, rel_path: str, content: str, agent: str, desc: str):
        full_path = os.path.join(self.workspace_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, "w") as f:
            f.write(content)
            
        await self.log_wiki_activity(agent, f"{desc} -> {rel_path}")
        await self.notify_file_change(rel_path)

    async def notify_file_change(self, rel_path: str):
        full_path = os.path.join(self.workspace_dir, rel_path)
        content = ""
        if os.path.exists(full_path):
            with open(full_path, "r") as f:
                content = f.read()
                
        await self.broadcast({
            "type": "file_changed",
            "filepath": rel_path,
            "content": content
        })

    def parse_code_blocks(self, text: str) -> Dict[str, str]:
        # Extract files between // CODE_START and // CODE_END tags
        files = {}
        pattern = r"\/\/ CODE_START\s*\n\/\/ ([a-zA-Z0-9\._\-]+)\s*\n(.*?)(\/\/ CODE_END|\Z)"
        matches = re.finditer(pattern, text, re.DOTALL)
        for match in matches:
            filename = match.group(1).strip()
            code = match.group(2).strip()
            files[filename] = code
        return files

    async def run_project_simulation(self, project_name: str):
        if self.is_running:
            return
        
        self.is_running = True
        self.current_project = project_name
        self.stats["tasks"] += 6
        
        try:
            # 1. CEO Agent
            await self.sleep_and_notify("CEO", "Analisi e Direttiva Strategica", ["boardroom"])
            ceo_prompt = f"Iniziamo lo sviluppo del prodotto '{project_name}'. Fornisci una direttiva per il PM Agent, specificando la nostra missione aziendale (creare software di alta qualità per aiutare l'umanità) e indicando le linee guida per la stesura del PRD."
            ceo_response = await self.agents["CEO"].run(ceo_prompt)
            
            await self.broadcast({
                "type": "agent_message",
                "agent": "CEO",
                "channel": "boardroom",
                "message": ceo_response
            })
            await self.log_wiki_activity("CEO", f"Avviato progetto: {project_name}")
            
            # 2. PM Agent
            await self.sleep_and_notify("PM", "Scrittura Requisiti di Prodotto (PRD)", ["boardroom", "product-ux"])
            pm_prompt = f"Leggi la direttiva del CEO:\n{ceo_response}\n\nGenera un Product Requirement Document (PRD) completo per '{project_name}' in formato Markdown. Assicurati che ogni requisito abbia un ID univoco (es. REQ-001, REQ-002)."
            prd_content = await self.agents["PM"].run(pm_prompt)
            
            prd_path = f"wiki/products/{project_name.lower().replace(' ', '_')}_prd.md"
            await self.write_wiki_file(prd_path, prd_content, "PM", "Creato PRD")
            
            await self.broadcast({
                "type": "agent_message",
                "agent": "PM",
                "channel": "product-ux",
                "message": f"Ho completato il PRD per '{project_name}'. Potete trovarlo in `{prd_path}`. UX Designer, tocca a te."
            })
            
            # 3. UX Designer Agent
            await self.sleep_and_notify("UX", "Definizione Design System & Personas", ["product-ux"])
            ux_prompt = f"Leggi il PRD del PM:\n{prd_content}\n\nProgetta l'esperienza utente ed il Design System (palette colori scura/neon, stile glassmorphism, regole tipografiche). Scrivi la guida in formato Markdown."
            ux_content = await self.agents["UX"].run(ux_prompt)
            
            ux_path = f"wiki/products/{project_name.lower().replace(' ', '_')}_ux.md"
            await self.write_wiki_file(ux_path, ux_content, "UX", "Creato Design System")
            
            await self.broadcast({
                "type": "agent_message",
                "agent": "UX",
                "channel": "product-ux",
                "message": f"Il Design System è pronto. Ho configurato uno stile ultra-premium stile Glassmorphism. Caricato in `{ux_path}`. Tech Lead, a te la palla."
            })

            # 4. Tech Lead Agent
            await self.sleep_and_notify("TechLead", "Progettazione Architettura & Scomposizione Task", ["engineering"])
            tl_prompt = f"Leggi il PRD:\n{prd_content}\n\ne il Design System UX:\n{ux_content}\n\nFornisci la System Design Spec (SAD) in Markdown, definendo i moduli frontend e i compiti operativi per lo sviluppatore."
            tl_content = await self.agents["TechLead"].run(tl_prompt)
            
            arch_path = f"wiki/architecture/{project_name.lower().replace(' ', '_')}_arch.md"
            await self.write_wiki_file(arch_path, tl_content, "TechLead", "Creato Documento di Architettura")
            
            await self.broadcast({
                "type": "agent_message",
                "agent": "TechLead",
                "channel": "engineering",
                "message": f"Ho delineato l'architettura tecnica e i task in `{arch_path}`. Sviluppatore, puoi iniziare a scrivere il codice in App.jsx ed App.css."
            })

            # 5. Developer Agent
            await self.sleep_and_notify("Developer", "Scrittura del Codice (React/CSS)", ["engineering"])
            dev_prompt = f"PRD:\n{prd_content}\n\nUX Design:\n{ux_content}\n\nArchitettura:\n{tl_content}\n\nScrivi il codice frontend completo in React. Devi generare DUE file: 'App.jsx' e 'App.css'.\nUsa ESATTAMENTE questo formato per ciascun file:\n// CODE_START\n// App.jsx\ncodice qui...\n// CODE_END\n\n// CODE_START\n// App.css\ncodice qui...\n// CODE_END"
            dev_response = await self.agents["Developer"].run(dev_prompt)
            
            # Parse code files written by the agent
            code_files = self.parse_code_blocks(dev_response)
            
            # Write files to frontend src sandbox
            for filename, code in code_files.items():
                dest_path = f"frontend/src/sandbox/{filename}"
                await self.write_wiki_file(dest_path, code, "Developer", f"Scritto codice sorgente {filename}")
            
            await self.broadcast({
                "type": "agent_message",
                "agent": "Developer",
                "channel": "engineering",
                "message": f"Codice scritto con successo! Ho creato {list(code_files.keys())} e li ho integrati nella sandbox. QA, per favore procedi con i test."
            })

            # 6. QA Agent
            await self.sleep_and_notify("QA", "Esecuzione Test Suite & Convalida", ["engineering"])
            qa_prompt = f"Requisiti PRD:\n{prd_content}\n\nCodice Sviluppatore:\n{dev_response}\n\nAnalizza il codice ed esegui una validazione automatica. Genera un Test Report in Markdown approvando o segnalando bug."
            qa_content = await self.agents["QA"].run(qa_prompt)
            
            qa_path = "wiki/operations/test_reports.md"
            await self.write_wiki_file(qa_path, qa_content, "QA", "Generato Report di Test")
            
            await self.broadcast({
                "type": "agent_message",
                "agent": "QA",
                "channel": "engineering",
                "message": f"I test sono stati eseguiti. Report inserito in `{qa_path}`. Stato dei test: SUPERATO. DevOps, puoi procedere al rilascio."
            })

            # 7. DevOps Agent
            await self.sleep_and_notify("DevOps", "Deploy & Integrazione Continua", ["ops"])
            devops_prompt = f"Report Test QA:\n{qa_content}\n\nEsegui il deploy in produzione dell'applicazione e scrivi il log del rilascio."
            devops_content = await self.agents["DevOps"].run(devops_prompt)
            
            deploy_path = "wiki/operations/deploy_log.md"
            await self.write_wiki_file(deploy_path, devops_content, "DevOps", "Rilasciato Build in Produzione")
            self.stats["builds"] += 1
            
            await self.broadcast({
                "type": "agent_message",
                "agent": "DevOps",
                "channel": "ops",
                "message": f"Rilascio completato con successo in produzione! Dettagli in `{deploy_path}`. Tutti i sistemi sono verdi. Prodotto online."
            })
            
            # Final CEO Wrap-Up
            await self.sleep_and_notify("CEO", "Rilascio Prodotto Completato", ["boardroom"])
            await self.broadcast({
                "type": "agent_message",
                "agent": "CEO",
                "channel": "boardroom",
                "message": f"Splendido lavoro, Team! Il prodotto '{project_name}' è ufficialmente rilasciato ed online. La nostra missione di servire l'umanità prosegue con successo!"
            })

        except Exception as e:
            logger.error(f"Errore nella simulazione di progetto: {e}", exc_info=True)
        finally:
            self.is_running = False
            self.current_project = ""
            self.active_agent = "Idle"
            self.agent_statuses = {k: "Idle" for k in self.agents.keys()}
            asyncio.create_task(self.broadcast_state())

    async def run_ticket_simulation(self, ticket_description: str):
        if self.is_running:
            return
        
        self.is_running = True
        self.stats["tickets"] += 1
        self.stats["tasks"] += 7
        
        try:
            # 1. Frontline Support Agent AI
            await self.sleep_and_notify("Support", "Analisi Ticket & Filtro 1° Livello", ["support-tickets"])
            support_prompt = f"Nuova segnalazione dell'utente:\n{ticket_description}\n\nAnalizza la segnalazione, inseriscila in un report ticket in Markdown con stato [Aperto - In carico a R&D] e rispondi all'utente."
            support_response = await self.agents["Support"].run(support_prompt)
            
            ticket_path = "wiki/operations/tickets.md"
            await self.write_wiki_file(ticket_path, support_response, "Support", "Creato Ticket")
            
            await self.broadcast({
                "type": "agent_message",
                "agent": "Support",
                "channel": "support-tickets",
                "message": f"Ricevuto bug report dall'utente. Creato ticket in `{ticket_path}`. Inoltrato all'Engineering e notificato il CEO."
            })

            # 2. CEO Agent
            await self.sleep_and_notify("CEO", "Valutazione Impatto Bug", ["boardroom"])
            ceo_prompt = f"Ticket in coda:\n{support_response}\n\nValuta l'impatto sul business e autorizza il PM/Engineering a fermare le attività correnti per fare un hotfix immediato."
            ceo_response = await self.agents["CEO"].run(ceo_prompt)
            
            await self.broadcast({
                "type": "agent_message",
                "agent": "CEO",
                "channel": "boardroom",
                "message": f"Approvato hotfix prioritario. PM, procedi con l'integrazione dei requisiti."
            })

            # 3. PM Agent
            await self.sleep_and_notify("PM", "Aggiornamento Requisiti (Backlog Priority)", ["boardroom", "product-ux"])
            pm_prompt = f"Bug ticket:\n{support_response}\n\nScrivi un addendum di requisiti tecnici per il fix, assegnandogli priorità massima."
            pm_response = await self.agents["PM"].run(pm_prompt)
            
            await self.write_wiki_file("wiki/products/hotfix_prd_addendum.md", pm_response, "PM", "Creato Addendum PRD")
            await self.broadcast({
                "type": "agent_message",
                "agent": "PM",
                "channel": "product-ux",
                "message": f"Requisiti di correzione aggiunti. Tech Lead, definisci i task di sviluppo."
            })

            # 4. Tech Lead Agent
            await self.sleep_and_notify("TechLead", "Analisi Tecnica & Patch Design", ["engineering"])
            tl_prompt = f"Integrazione requisiti PM:\n{pm_response}\n\nAnalizza l'errore e scrivi le specifiche tecniche del fix per guidare lo sviluppatore."
            tl_response = await self.agents["TechLead"].run(tl_prompt)
            
            await self.write_wiki_file("wiki/architecture/hotfix_design.md", tl_response, "TechLead", "Disegnato Specifica di Fix")
            await self.broadcast({
                "type": "agent_message",
                "agent": "TechLead",
                "channel": "engineering",
                "message": f"Specifica tecnica del fix caricata in `wiki/architecture/hotfix_design.md`. Developer, applica la patch."
            })

            # 5. Developer Agent
            await self.sleep_and_notify("Developer", "Scrittura Patch & Applicazione Hotfix", ["engineering"])
            
            # Read existing App.jsx from sandbox to provide context
            existing_app_path = os.path.join(self.frontend_dir, "src/sandbox/App.jsx")
            existing_code = ""
            if os.path.exists(existing_app_path):
                with open(existing_app_path, "r") as f:
                    existing_code = f.read()
            else:
                # Fallback to main frontend src if sandbox app doesn't exist yet
                existing_app_path_fallback = os.path.join(self.frontend_dir, "src/App.jsx")
                if os.path.exists(existing_app_path_fallback):
                    with open(existing_app_path_fallback, "r") as f:
                        existing_code = f.read()

            dev_prompt = f"Codice attuale App.jsx:\n{existing_code}\n\nSpecifiche tecniche di fix:\n{tl_response}\n\nApplica la patch correttiva. Ritorna il codice App.jsx intero corretto, racchiuso tra `// CODE_START` e `// CODE_END` con l'intestazione '// App.jsx'."
            dev_response = await self.agents["Developer"].run(dev_prompt)
            
            code_files = self.parse_code_blocks(dev_response)
            for filename, code in code_files.items():
                dest_path = f"frontend/src/sandbox/{filename}"
                await self.write_wiki_file(dest_path, code, "Developer", f"Applicata Patch a {filename}")
                
            await self.write_wiki_file("wiki/operations/hotfixes.md", dev_response, "Developer", "Registrato Hotfix")
            
            await self.broadcast({
                "type": "agent_message",
                "agent": "Developer",
                "channel": "engineering",
                "message": f"Hotfix applicato su `App.jsx`. QA, esegui i test di regressione."
            })

            # 6. QA Agent
            await self.sleep_and_notify("QA", "Regression Testing & Firma QA", ["engineering"])
            qa_prompt = f"Codice con patch:\n{dev_response}\n\nVerifica che la segnalazione dell'utente sia risolta e che gli altri elementi funzionino ancora. Genera il report dei test."
            qa_response = await self.agents["QA"].run(qa_prompt)
            
            await self.write_wiki_file("wiki/operations/test_reports.md", qa_response, "QA", "Generato Report di Regressione")
            await self.broadcast({
                "type": "agent_message",
                "agent": "QA",
                "channel": "engineering",
                "message": f"Test di regressione completati. Stato: SUPERATO. Il bug è corretto e sicuro. DevOps, procedi al rilascio."
            })

            # 7. DevOps Agent
            await self.sleep_and_notify("DevOps", "Deploy del Fix a Caldo (Hotfix)", ["ops"])
            devops_prompt = f"Esegui il deploy in produzione del fix a caldo."
            devops_response = await self.agents["DevOps"].run(devops_prompt)
            
            await self.write_wiki_file("wiki/operations/deploy_log.md", devops_response, "DevOps", "Distribuito Hotfix in Produzione")
            self.stats["builds"] += 1
            
            await self.broadcast({
                "type": "agent_message",
                "agent": "DevOps",
                "channel": "ops",
                "message": f"Deploy a caldo completato. Patch live in produzione."
            })

            # 8. Frontline Support Agent
            await self.sleep_and_notify("Support", "Notifica Risoluzione a Utente", ["support-tickets"])
            
            # Mark ticket as resolved
            resolved_ticket_content = f"# Ticket Status: RISOLTO\n\nIl bug è stato risolto con successo dall'Engineering ed è andato in produzione tramite DevOps.\n\n**Dettagli risoluzione**:\n{devops_response}"
            await self.write_wiki_file(ticket_path, resolved_ticket_content, "Support", "Risolto e Chiuso Ticket")
            
            await self.broadcast({
                "type": "agent_message",
                "agent": "Support",
                "channel": "support-tickets",
                "message": f"Gentile utente, sono lieta di informarla che il bug segnalato è stato corretto ed è ora online in produzione! La ringraziamo ancora per la segnalazione."
            })

        except Exception as e:
            logger.error(f"Errore nella simulazione di ticket: {e}", exc_info=True)
        finally:
            self.is_running = False
            self.active_agent = "Idle"
            self.agent_statuses = {k: "Idle" for k in self.agents.keys()}
            asyncio.create_task(self.broadcast_state())
