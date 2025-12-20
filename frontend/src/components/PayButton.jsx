import React, { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import '../styles/PayButton.css'

function PayButton() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const { user, token } = useAuth()

  const handleClick = async () => {
    setLoading(true)
    setError(null)

    try {

      const res = await fetch("/api/stripe/create-checkout-session", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                user_id: user?.user_id || user?.id || 'mock-user-123',
                amount_cents: 999, // $9.99
                currency: "usd",
                payment_for: "1-Month Wavvy Premium",
              }),
            });


      const data = await res.json();

      // Redirect to Stripe Checkout
      //   console.println('Stripe checkout URL:', data.url)
      if (res.ok && data.checkout_url) {
        console.log('Redirecting to Stripe checkout:', data.checkout_url)
        window.location.assign(data.checkout_url)
      } else {
        console.error('Stripe error:', data)
        setError(data.error || `Something went wrong starting checkout. ${JSON.stringify(data)}`)
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
