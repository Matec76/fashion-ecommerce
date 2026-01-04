import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {/* Bọc BrowserRouter ở ngoài cùng để dùng được tính năng chuyển trang */}
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);