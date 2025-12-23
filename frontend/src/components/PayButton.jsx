import React, { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import '../styles/PayButton.css'

function PayButton() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const { user, token } = useAuth()
  const navigate = useNavigate()

  const handleClick = async () => {
    setLoading(true)
    setError(null)

    try {
      const res = await fetch("/api/stripe/create-checkout-session", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          amount_cents: 999, // $9.99
          currency: "usd",
          payment_for: "1-Month Wavvy Premium",
        }),
      });

      const data = await res.json();

      // Check if user needs to connect Stripe account
      if (!res.ok) {
        if (data.error_code === 'STRIPE_NOT_CONNECTED') {
          setError(
            <span>
              {data.error}{' '}
              <button 
                onClick={() => navigate('/settings')} 
                className="link-button"
              >
                Go to Settings
              </button>
            </span>
          )
        } else {
          setError(data.error || `Something went wrong starting checkout.`)
        }
        setLoading(false)
        return
      }

      // Redirect to Stripe Checkout
      if (data.checkout_url) {
        console.log('Redirecting to Stripe checkout:', data.checkout_url)
        window.location.assign(data.checkout_url)
      } else {
        console.error('Stripe error:', data)
        setError('No checkout URL received from server')
        setLoading(false)
      }
    } catch (err) {
      console.error('Network error:', err)
      setError('Network error. Is the backend running on :5000?')
      setLoading(false)
    }
  }

  return (
    <>
      <button
        className="pay-button"
        onClick={handleClick}
        disabled={loading}
      >
        {/* If loading, show redirecting text */}
        {loading ? 'Redirecting to Stripe…' : 'Get Premium!'}
      </button>
      {error && <p className="pay-button-error">{error}</p>}
    </>
  )
}

export default PayButton
