// src/App.jsx
import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home.jsx";
import PaymentSuccess from "./pages/PaymentSuccess.jsx";
import PaymentCancelled from "./pages/PaymentCancelled.jsx";
import "./styles/App.css"; // ⬅️ new

function App() {
  return (
    <BrowserRouter>
      <div className="app-root">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/payment-success" element={<PaymentSuccess />} />
          <Route path="/payment-cancelled" element={<PaymentCancelled />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
