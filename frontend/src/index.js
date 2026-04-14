import React, { StrictMode, Suspense } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from "react-router-dom";
import './i18n';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { AuthProvider } from "./user/hooks/useAuth";
import { LoaderIndicator } from './common/components/LoaderIndicator';

const container = document.getElementById('root');

const root = createRoot(container);

if (!window.location.host.match("127.0.0.1")) {
  root.render(
    <StrictMode>
      <BrowserRouter> 
        <AuthProvider>   
          <Suspense fallback={<LoaderIndicator />}>
            <App />
          </Suspense>   
        </AuthProvider>
      </BrowserRouter>
    </StrictMode>      
  );
} else {
  root.render(
    <BrowserRouter> 
      <AuthProvider>   
        <Suspense fallback={<LoaderIndicator />}>
          <App />
        </Suspense>   
      </AuthProvider>
    </BrowserRouter>
  );
}

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals(console.log);
