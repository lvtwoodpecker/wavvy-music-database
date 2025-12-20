import React, { useEffect, useRef } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { subscriptionService } from '../services/subscriptionService'
import '../styles/PaymentSuccess.css'

function PaymentSuccess() {
  const location = useLocation()
  const navigate = useNavigate()
  const params = new URLSearchParams(location.search)
  const { markPremium, token, setPremiumExpiry } = useAuth()
  const hasActivatedRef = useRef(false)

  useEffect(() => {
    if (hasActivatedRef.current) return
    hasActivatedRef.current = true

    const activate = async () => {
      try {
        // Grant premium locally
        markPremium('Premium')
        // Persist subscription history
        if (token) {
          const sub = await subscriptionService.activate(token, { plan_name: 'Premium Monthly' })
          if (sub?.expires_at) setPremiumExpiry(sub.expires_at)
        }
      } catch (err) {
        console.error('Failed to persist subscription:', err)
      } finally {
        navigate('/app', { replace: true })
      }
    }
    activate()
  }, [markPremium, setPremiumExpiry, token, navigate])

  return null
}

export default PaymentSuccess
