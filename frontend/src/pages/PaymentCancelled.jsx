import React from 'react'
import { Link } from 'react-router-dom'
import '../styles/PaymentCancelled.css'

function PaymentCancelled() {
  return (
    <main className="payment-cancelled-main">
      <div className="payment-cancelled-card">
        <h1>Payment Cancelled</h1>
        <p>You cancelled the Stripe checkout. No charge was made.</p>
        <Link to="/" className="payment-cancelled-link">
          Try again
        </Link>
      </div>
    </main>
  )
}

export default PaymentCancelled
