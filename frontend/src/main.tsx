import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Basic CSS reset
const globalStyles = `
  * {
    box-sizing: border-box;
  }
  
  body {
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.5;
    color: #333;
    background-color: #f8f9fa;
  }
  
  h1, h2, h3, h4, h5, h6 {
    margin-top: 0;
  }
  
  a {
    color: #007bff;
  }
  
  button:hover {
    opacity: 0.9;
  }
  
  input, select {
    box-sizing: border-box;
  }
`;

// Inject global styles
const styleElement = document.createElement('style');
styleElement.textContent = globalStyles;
document.head.appendChild(styleElement);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);