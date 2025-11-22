import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home.jsx'
import PaymentSuccess from './pages/PaymentSuccess.jsx'
import PaymentCancelled from './pages/PaymentCancelled.jsx'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/payment-success" element={<PaymentSuccess />} />
        <Route path="/payment-cancelled" element={<PaymentCancelled />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
