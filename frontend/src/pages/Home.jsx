import React from 'react'
import PayButton from '../components/PayButton.jsx'
import '../styles/Home.css'

function Home() {
  return (
    <main className="home-main">
      <div className="home-card">
        <h1>Wavvy Premium (Test Mode)</h1>
        <p>
          This is a fake checkout for wavvy.
          Use Stripe test cards only – no real money happens here.
        </p>
        <PayButton />
      </div>
    </main>
  )
}

export default Home