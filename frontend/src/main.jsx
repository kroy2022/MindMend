import React, { Suspense } from 'react';
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import App from './App.jsx'
import './index.css'
import {NextUIProvider} from "@nextui-org/react";
import Login from './Login.jsx'
import Twitter from './Twitter.jsx';
import TwitterPopUp from './components/TwitterPopup.jsx';
import MessagePopUp from './components/MessagePopup.jsx';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Suspense> <App/> </Suspense>} />
        <Route path="/Login" element={<Suspense> <Login/> </Suspense>} />
        <Route path="/Twitter" element={<Suspense> <Twitter/> </Suspense>} />
        <Route path="/TwitterPopup" element={<Suspense> <TwitterPopUp/> </Suspense>} />
        <Route path="/MessagePopup" element={<Suspense> <MessagePopUp/> </Suspense>} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
);
