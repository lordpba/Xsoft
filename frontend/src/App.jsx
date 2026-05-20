import React, { useState, useEffect, useRef } from 'react';
import './App.css';

// Import dynamic sandbox preview component
import SandboxApp from './sandbox/App.jsx';

const AGENT_COLORS = {
  CEO: '#a855f7',
  PM: '#6366f1',
  UX: '#ec4899',
  TechLead: '#3b82f6',
  Developer: '#10b981',
  QA: '#f59e0b',
  Support: '#0ea5e9',
  DevOps: '#ef4444',
  Idle: '#64748b'
};

const AGENT_SYSTEM_PROMPTS = {
  CEO: "CEO Agent: Guida la visione strategica aziendale. Il suo focus primario è dirigere lo sviluppo del prodotto verso una redditività sostenibile ed efficiente, coordinando il team per creare software che aiuti l'umanità ad evolversi.",
  PM: "Product Manager Agent: Definisce i requisiti di business e stila il PRD (Product Requirement Document). Definisce i singoli blocchi funzionali legandoli a ID di tracciamento univoci.",
  UX: "UX Designer Agent: Ricerca l'esperienza ottimale degli utenti e progetta il visual design system (palette scure/neon, stili vetrosi). Effettua controlli di usabilità e visual QA.",
  TechLead: "Tech Lead Agent: Traduce i requisiti in specifiche di architettura (System Design Spec). Suddivide le milestones tecniche in singoli compiti di programmazione per lo sviluppatore.",
  Developer: "Developer Agent: Scrive codice sorgente pulito e funzionante in React e CSS, isolandolo in un ambiente di sandbox per la revisione da parte del team.",
  QA: "QA Agent: Convalida la stabilità del software eseguendo test funzionali e test di regressione, assicurando che non ci siano anomalie visive o logiche.",
  Support: "Frontline Support Agent: Agente di front-desk che risponde in tempo reale alle problematiche dell'utente. Se rileva bug complessi, li inserisce direttamente nel backlog di engineering bypassando i filtri tradizionali.",
  DevOps: "DevOps Agent: Gestisce la pipeline di integrazione continua (CI/CD) e automatizza la messa online in produzione dei build approvati dal QA."
};

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [activeChannel, setActiveChannel] = useState('boardroom');
  const [activeFile, setActiveFile] = useState('wiki/index.md');
  const [selectedAgentInfo, setSelectedAgentInfo] = useState(null);
  
  // Real-time states synchronized with backend
  const [wsConnected, setWsConnected] = useState(false);
  const [currentProject, setCurrentProject] = useState('');
  const [activeAgent, setActiveAgent] = useState('Idle');
  const [agentStatuses, setAgentStatuses] = useState({
    CEO: 'Idle', PM: 'Idle', UX: 'Idle', TechLead: 'Idle',
    Developer: 'Idle', QA: 'Idle', Support: 'Idle', DevOps: 'Idle'
  });
  const [stats, setStats] = useState({ tokens: 0, tickets: 0, tasks: 0, builds: 0 });
  const [messages, setMessages] = useState([
    {
      agent: 'CEO',
      channel: 'boardroom',
      message: 'Benvenuti nel pannello di controllo di Xsoft. Pronti a creare il futuro dello sviluppo software autonomo. Iniziamo definendo il nostro progetto.',
      time: new Date().toLocaleTimeString()
    }
  ]);
  const [files, setFiles] = useState({
    'wiki/index.md': '# Xsoft Knowledge Index\nCaricamento wiki in corso...'
  });

  // Inputs
  const [projectNameInput, setProjectNameInput] = useState('');
  const [ticketInput, setTicketInput] = useState('');
  
  const wsRef = useRef(null);
  const chatEndRef = useRef(null);

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeChannel]);

  // Establish WebSocket connection
  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const connectWebSocket = () => {
    console.log("Connessione al WebSocket del server...");
    const socket = new WebSocket('ws://127.0.0.1:8000/ws');
    
    socket.onopen = () => {
      console.log("WebSocket connesso con successo.");
      setWsConnected(true);
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("Evento ricevuto:", data);

      if (data.type === 'state_update') {
        setActiveAgent(data.active_agent);
        setAgentStatuses(data.agent_statuses);
        setStats(data.stats);
        setCurrentProject(data.current_project);
      } 
      else if (data.type === 'agent_action') {
        // Log action as a system notification in the chat
        const time = new Date().toLocaleTimeString();
        setMessages(prev => [...prev, {
          agent: data.agent,
          channel: data.channels[0] || 'boardroom',
          message: `[ATTIVITÀ]: ${data.action}`,
          time,
          isSystem: true
        }]);
      }
      else if (data.type === 'agent_message') {
        const time = new Date().toLocaleTimeString();
        setMessages(prev => [...prev, {
          agent: data.agent,
          channel: data.channel,
          message: data.message,
          time
        }]);
      }
      else if (data.type === 'all_files') {
        setFiles(data.files);
      }
      else if (data.type === 'file_changed') {
        setFiles(prev => ({
          ...prev,
          [data.filepath]: data.content
        }));
        // Auto-select changed file if in workspace to show live changes
        setActiveFile(data.filepath);
      }
    };

    socket.onclose = () => {
      console.log("WebSocket disconnesso. Tentativo di riconnessione tra 3 secondi...");
      setWsConnected(false);
      setTimeout(connectWebSocket, 3000);
    };

    socket.onerror = (err) => {
      console.error("Errore WebSocket:", err);
      socket.close();
    };

    wsRef.current = socket;
  };

  const startProject = (e) => {
    e.preventDefault();
    if (!projectNameInput.trim() || !wsConnected) return;
    
    // Clear old chat logs for fresh feel
    setMessages([]);
    
    wsRef.current.send(JSON.stringify({
      action: 'start_project',
      project_name: projectNameInput
    }));
    setProjectNameInput('');
  };

  const submitTicket = (e) => {
    e.preventDefault();
    if (!ticketInput.trim() || !wsConnected) return;

    wsRef.current.send(JSON.stringify({
      action: 'submit_ticket',
      ticket_desc: ticketInput
    }));
    setTicketInput('');
    // Switch to support/chat tab to monitor progress
    setActiveTab('chat');
    setActiveChannel('support-tickets');
  };

  // Custom Markdown converter to render clean rich templates
  const renderMarkdown = (text) => {
    if (!text) return <p className="md-p">Seleziona un file per visualizzarne il contenuto.</p>;
    
    return text.split('\n').map((line, index) => {
      if (line.startsWith('# ')) {
        return <h1 key={index} className="md-h1">{line.slice(2)}</h1>;
      }
      if (line.startsWith('## ')) {
        return <h2 key={index} className="md-h2">{line.slice(3)}</h2>;
      }
      if (line.startsWith('### ')) {
        return <h3 key={index} className="md-h3">{line.slice(4)}</h3>;
      }
      if (line.startsWith('* ') || line.startsWith('- ')) {
        const item = line.slice(2);
        if (item.startsWith('[ ] ')) {
          return <li key={index} className="md-li" style={{ listStyle: 'none' }}>☐ {item.slice(4)}</li>;
        }
        if (item.startsWith('[x] ') || item.startsWith('[X] ')) {
          return <li key={index} className="md-li" style={{ listStyle: 'none', color: '#10b981' }}>☑ {item.slice(4)}</li>;
        }
        return <li key={index} className="md-li">{item}</li>;
      }
      if (line.startsWith('> ')) {
        return <div key={index} className="md-block">{line.slice(2)}</div>;
      }
      if (line.trim() === '') {
        return <div key={index} style={{ height: '8px' }} />;
      }
      return <p key={index} className="md-p">{line}</p>;
    });
  };

  const activeChannelMessages = messages.filter(m => m.channel === activeChannel);
  const isSimulationRunning = activeAgent !== 'Idle';

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <div className="sidebar">
        <div className="logo-container">
          <div className="logo-icon">X</div>
          <span className="logo-text">Xsoft Corp</span>
        </div>
        
        <div className="nav-menu">
          <div className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>
            <span className="nav-icon">📊</span> Sede Centrale
          </div>
          <div className={`nav-item ${activeTab === 'chat' ? 'active' : ''}`} onClick={() => setActiveTab('chat')}>
            <span className="nav-icon">💬</span> Canali Chat
          </div>
          <div className={`nav-item ${activeTab === 'workspace' ? 'active' : ''}`} onClick={() => setActiveTab('workspace')}>
            <span className="nav-icon">📁</span> Workspace
          </div>
          <div className={`nav-item ${activeTab === 'preview' ? 'active' : ''}`} onClick={() => setActiveTab('preview')}>
            <span className="nav-icon">💻</span> App Sandbox
          </div>
          <div className={`nav-item ${activeTab === 'support' ? 'active' : ''}`} onClick={() => setActiveTab('support')}>
            <span className="nav-icon">🛠️</span> Support & R&D
          </div>
        </div>

        <div className="sidebar-footer">
          <div className="connection-status">
            <span className={`status-dot ${wsConnected ? 'connected' : ''}`} />
            {wsConnected ? 'Backend Connesso' : 'Disconnesso (Riconnessione...)'}
          </div>
        </div>
      </div>

      {/* Main Workspace Frame */}
      <div className="main-content">
        {/* Top Navbar */}
        <div className="topbar">
          <div className="topbar-left">
            <h2>{activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}</h2>
            {currentProject && (
              <span className="project-badge">Progetto: {currentProject}</span>
            )}
            {isSimulationRunning && (
              <span className="project-badge" style={{ background: 'rgba(16, 185, 129, 0.15)', borderColor: '#10b981', color: '#10b981' }}>
                Agente Attivo: {activeAgent}
              </span>
            )}
          </div>
          
          <div className="topbar-right">
            <div className="stat-widget">
              <span className="stat-label">Tasks</span>
              <span className="stat-value">{stats.tasks}</span>
            </div>
            <div className="stat-widget">
              <span className="stat-label">Builds</span>
              <span className="stat-value">{stats.builds}</span>
            </div>
            <div className="stat-widget">
              <span className="stat-label">Ticket Risolti</span>
              <span className="stat-value">{stats.tickets}</span>
            </div>
          </div>
        </div>

        {/* Tab Switch Viewports */}
        <div className="panel-container">
          
          {/* TAB 1: DASHBOARD (Overview & Controls) */}
          {activeTab === 'dashboard' && (
            <div className="dashboard-grid">
              {/* Agent Org Chart Map */}
              <div className="glass-card">
                <div className="card-title">
                  <span>Mappa degli Agenti AI</span>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Clicca per info di ruolo</span>
                </div>
                
                <div className="org-chart-container">
                  {/* Row 1: Board Strategic Level */}
                  <div className="org-row">
                    <div 
                      className={`org-node ${activeAgent === 'CEO' ? 'active' : ''}`}
                      style={{ borderBottom: `3px solid ${AGENT_COLORS.CEO}` }}
                      onClick={() => setSelectedAgentInfo('CEO')}
                    >
                      <div className="node-role" style={{ color: AGENT_COLORS.CEO }}>CEO</div>
                      <div className="node-status">{agentStatuses.CEO}</div>
                    </div>
                  </div>
                  
                  {/* Row 2: Product & UX Design */}
                  <div className="org-row">
                    <div 
                      className={`org-node ${activeAgent === 'PM' ? 'active' : ''}`}
                      style={{ borderBottom: `3px solid ${AGENT_COLORS.PM}` }}
                      onClick={() => setSelectedAgentInfo('PM')}
                    >
                      <div className="node-role" style={{ color: AGENT_COLORS.PM }}>Product Manager</div>
                      <div className="node-status">{agentStatuses.PM}</div>
                    </div>
                    <div 
                      className={`org-node ${activeAgent === 'UX' ? 'active' : ''}`}
                      style={{ borderBottom: `3px solid ${AGENT_COLORS.UX}` }}
                      onClick={() => setSelectedAgentInfo('UX')}
                    >
                      <div className="node-role" style={{ color: AGENT_COLORS.UX }}>UX Designer</div>
                      <div className="node-status">{agentStatuses.UX}</div>
                    </div>
                  </div>

                  {/* Row 3: Tech Lead & Developer */}
                  <div className="org-row">
                    <div 
                      className={`org-node ${activeAgent === 'TechLead' ? 'active' : ''}`}
                      style={{ borderBottom: `3px solid ${AGENT_COLORS.TechLead}` }}
                      onClick={() => setSelectedAgentInfo('TechLead')}
                    >
                      <div className="node-role" style={{ color: AGENT_COLORS.TechLead }}>Tech Lead</div>
                      <div className="node-status">{agentStatuses.TechLead}</div>
                    </div>
                    <div 
                      className={`org-node ${activeAgent === 'Developer' ? 'active' : ''}`}
                      style={{ borderBottom: `3px solid ${AGENT_COLORS.Developer}` }}
                      onClick={() => setSelectedAgentInfo('Developer')}
                    >
                      <div className="node-role" style={{ color: AGENT_COLORS.Developer }}>Developer</div>
                      <div className="node-status">{agentStatuses.Developer}</div>
                    </div>
                  </div>

                  {/* Row 4: Quality & DevOps & Support */}
                  <div className="org-row">
                    <div 
                      className={`org-node ${activeAgent === 'QA' ? 'active' : ''}`}
                      style={{ borderBottom: `3px solid ${AGENT_COLORS.QA}` }}
                      onClick={() => setSelectedAgentInfo('QA')}
                    >
                      <div className="node-role" style={{ color: AGENT_COLORS.QA }}>QA Engineer</div>
                      <div className="node-status">{agentStatuses.QA}</div>
                    </div>
                    <div 
                      className={`org-node ${activeAgent === 'Support' ? 'active' : ''}`}
                      style={{ borderBottom: `3px solid ${AGENT_COLORS.Support}` }}
                      onClick={() => setSelectedAgentInfo('Support')}
                    >
                      <div className="node-role" style={{ color: AGENT_COLORS.Support }}>Support AI</div>
                      <div className="node-status">{agentStatuses.Support}</div>
                    </div>
                    <div 
                      className={`org-node ${activeAgent === 'DevOps' ? 'active' : ''}`}
                      style={{ borderBottom: `3px solid ${AGENT_COLORS.DevOps}` }}
                      onClick={() => setSelectedAgentInfo('DevOps')}
                    >
                      <div className="node-role" style={{ color: AGENT_COLORS.DevOps }}>DevOps</div>
                      <div className="node-status">{agentStatuses.DevOps}</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Controls Column */}
              <div className="glass-card" style={{ justifyContent: 'center' }}>
                <div className="card-title">Avvia Progetto Autonomo</div>
                <form onSubmit={startProject} className="control-panel">
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '8px', lineHeight: '1.5' }}>
                    Inserisci il nome del software che desideri venga sviluppato. Il team di agenti farà brainstorming, scriverà i requisiti, configurerà l'architettura, programmerà l'interfaccia ed eseguirà i test.
                  </p>
                  <input 
                    type="text" 
                    placeholder="Esempio: Todo App, Weather Dashboard..." 
                    value={projectNameInput}
                    onChange={(e) => setProjectNameInput(e.target.value)}
                    className="control-input"
                    disabled={isSimulationRunning}
                  />
                  <button 
                    type="submit" 
                    className="btn-primary" 
                    disabled={isSimulationRunning || !projectNameInput.trim() || !wsConnected}
                  >
                    {isSimulationRunning ? 'Simulazione in corso...' : 'Avvia Produzione Agentica'}
                  </button>
                </form>
              </div>
            </div>
          )}

          {/* TAB 2: CHANNELS CHAT (Slack style) */}
          {activeTab === 'chat' && (
            <div className="chat-layout">
              {/* Channel List */}
              <div className="channels-list">
                <button className={`channel-btn ${activeChannel === 'boardroom' ? 'active' : ''}`} onClick={() => setActiveChannel('boardroom')}>
                  # boardroom
                </button>
                <button className={`channel-btn ${activeChannel === 'product-ux' ? 'active' : ''}`} onClick={() => setActiveChannel('product-ux')}>
                  # product-ux
                </button>
                <button className={`channel-btn ${activeChannel === 'engineering' ? 'active' : ''}`} onClick={() => setActiveChannel('engineering')}>
                  # engineering
                </button>
                <button className={`channel-btn ${activeChannel === 'support-tickets' ? 'active' : ''}`} onClick={() => setActiveChannel('support-tickets')}>
                  # support-tickets
                </button>
                <button className={`channel-btn ${activeChannel === 'ops' ? 'active' : ''}`} onClick={() => setActiveChannel('ops')}>
                  # ops
                </button>
              </div>

              {/* Chat Messages Feed */}
              <div className="chat-feed-container">
                <div className="chat-feed">
                  {activeChannelMessages.length === 0 ? (
                    <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '40px 0' }}>
                      Nessun messaggio in questo canale al momento.
                    </div>
                  ) : (
                    activeChannelMessages.map((msg, i) => (
                      <div key={i} className="chat-message">
                        <div className="message-header">
                          <div 
                            className="message-avatar"
                            style={{ backgroundColor: AGENT_COLORS[msg.agent] || '#555' }}
                          >
                            {msg.agent.slice(0, 2)}
                          </div>
                          <span className="message-author" style={{ color: AGENT_COLORS[msg.agent] || '#fff' }}>
                            {msg.agent}
                          </span>
                          <span className="message-time">{msg.time}</span>
                        </div>
                        <div 
                          className="message-content"
                          style={msg.isSystem ? { borderLeft: `3px solid ${AGENT_COLORS[msg.agent]}`, fontStyle: 'italic', background: 'rgba(255,255,255,0.01)' } : {}}
                        >
                          {msg.message}
                        </div>
                      </div>
                    ))
                  )}
                  <div ref={chatEndRef} />
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: WORKSPACE & FILE EXPLORER */}
          {activeTab === 'workspace' && (
            <div className="explorer-layout">
              {/* Left File Tree */}
              <div className="file-tree">
                <h4 style={{ color: 'var(--text-muted)', fontSize: '0.8rem', paddingLeft: '12px', marginBottom: '8px' }}>ARCHIVI WIKI & CODICE</h4>
                {Object.keys(files).sort().map((filepath) => (
                  <div 
                    key={filepath}
                    className={`tree-item ${activeFile === filepath ? 'active' : ''}`}
                    onClick={() => setActiveFile(filepath)}
                  >
                    📄 {filepath.split('/').pop()}
                  </div>
                ))}
              </div>

              {/* Right File Viewer */}
              <div className="viewer-pane">
                <div className="viewer-header">
                  Visualizzatore: {activeFile}
                </div>
                <div className="viewer-content">
                  {activeFile.endsWith('.md') ? (
                    renderMarkdown(files[activeFile])
                  ) : (
                    <pre><code>{files[activeFile] || 'Nessun codice caricato.'}</code></pre>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: APP LIVE SANDBOX PREVIEW */}
          {activeTab === 'preview' && (
            <div className="preview-layout">
              <div className="preview-bar">
                <div style={{ display: 'flex', gap: '6px' }}>
                  <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ff5f56' }} />
                  <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ffbd2e' }} />
                  <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#27c93f' }} />
                </div>
                <div className="preview-address">http://xsoft-sandbox.local/production</div>
                <div style={{ width: '32px' }} />
              </div>
              <div className="preview-frame">
                <SandboxApp />
              </div>
            </div>
          )}

          {/* TAB 5: UNIFIED SUPPORT & R&D INBOX */}
          {activeTab === 'support' && (
            <div className="support-layout">
              {/* Form to submit tickets */}
              <div className="glass-card">
                <div className="card-title">Segnala Bug o Invia Feedback (Loop R&D Unificato)</div>
                <form onSubmit={submitTicket} className="control-panel">
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '8px', lineHeight: '1.5' }}>
                    Segnala una problematica riscontrata nel software di produzione (es. "Il toggle dei compiti della Todo App fa cilecca se cliccato molto rapidamente"). 
                    L'agente di supporto di 1° livello prenderà in carico la segnalazione e scriverà automaticamente al Developer e PM per rilasciare una patch correttiva in pochi minuti.
                  </p>
                  <textarea 
                    placeholder="Descrivi dettagliatamente il problema o la modifica richiesta..." 
                    value={ticketInput}
                    onChange={(e) => setTicketInput(e.target.value)}
                    className="control-input"
                    style={{ minHeight: '120px', resize: 'vertical' }}
                    disabled={isSimulationRunning}
                  />
                  <button 
                    type="submit" 
                    className="btn-primary"
                    style={{ background: 'linear-gradient(135deg, var(--color-blue), var(--color-indigo))' }}
                    disabled={isSimulationRunning || !ticketInput.trim() || !wsConnected}
                  >
                    {isSimulationRunning ? 'Loop R&D in esecuzione...' : 'Invia Segnalazione a R&D'}
                  </button>
                </form>
              </div>

              {/* Description of R&D Loop */}
              <div className="glass-card">
                <div className="card-title">Come funziona la nostra fusione Supporto & R&D?</div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: '1.6' }}>
                  <p style={{ marginBottom: '14px' }}>
                    Nelle aziende vecchio stampo, i ticket di supporto si perdono in vari livelli di burocrazia. 
                    Qui in <strong>Xsoft</strong>, l'Agente di Supporto è integrato direttamente nel team di engineering:
                  </p>
                  <ul style={{ paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <li><strong>1. Ingestione Automatica</strong>: Il ticket del cliente viene analizzato dall'AI di supporto e registrato nella Wiki operazionale (`wiki/operations/tickets.md`).</li>
                    <li><strong>2. Hotfix Prioritario</strong>: Se l'errore è bloccante, il CEO mette in pausa gli altri task e assegna al PM e Developer il fix immediato.</li>
                    <li><strong>3. Deploy & Chiusura Loop</strong>: Il Developer scrive la patch, il QA valida l'hotfix, DevOps lo distribuisce e il Supporto AI chiude il ticket avvisando l'utente.</li>
                  </ul>
                </div>
              </div>
            </div>
          )}

        </div>
      </div>

      {/* Info Modal on Node Click */}
      {selectedAgentInfo && (
        <div className="modal-backdrop" onClick={() => setSelectedAgentInfo(null)} style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0, 0, 0, 0.75)', backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100
        }}>
          <div className="glass-card" onClick={e => e.stopPropagation()} style={{
            maxWidth: '500px', width: '90%', padding: '32px', gap: '16px'
          }}>
            <h3 style={{ color: AGENT_COLORS[selectedAgentInfo], fontSize: '1.4rem' }}>{selectedAgentInfo} Agent</h3>
            <p style={{ color: '#fff', fontSize: '0.95rem', lineHeight: '1.6' }}>{AGENT_SYSTEM_PROMPTS[selectedAgentInfo]}</p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px' }}>
              <button className="btn-primary" style={{ padding: '8px 20px', fontSize: '0.85rem' }} onClick={() => setSelectedAgentInfo(null)}>
                Chiudi
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
