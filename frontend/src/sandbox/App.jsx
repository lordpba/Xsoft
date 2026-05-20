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