import React from 'react'
import { useLocation, Link } from 'react-router-dom'
import '../styles/PaymentSuccess.css'

function PaymentSuccess() {
  const location = useLocation()
  const params = new URLSearchParams(location.search)
  const sessionId = params.get('session_id')

  return (
    <main className="payment-success-main">
      <div className="payment-success-card">
        <h1>Payment Successful</h1>
        <p>Your Stripe test payment went through.</p>

        {sessionId && (
          <p className="payment-success-session-id">
            Session ID: <code>{sessionId}</code>
          </p>
        )}

        <Link to="/" className="payment-success-link">
          Back to Home
        </Link>
      </div>
    </main>
  )
}

export default PaymentSuccess
