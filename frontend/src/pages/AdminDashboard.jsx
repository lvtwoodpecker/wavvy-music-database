// src/pages/AdminDashboard.jsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import '../styles/AdminDashboard.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5173';

function AdminDashboard() {
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState('pricing');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // State for different sections
  const [pricingTrends, setPricingTrends] = useState([]);
  const [competitors, setCompetitors] = useState([]);
  const [musicAnalytics, setMusicAnalytics] = useState(null);
  const [mlAnalysis, setMlAnalysis] = useState([]);
  const [users, setUsers] = useState([]);
  const [usersPagination, setUsersPagination] = useState({ page: 1, per_page: 20 });
  
  // Fetch data based on active tab
  useEffect(() => {
    fetchTabData();
  }, [activeTab, usersPagination.page]);

  const fetchTabData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      switch (activeTab) {
        case 'pricing':
          await fetchPricingTrends();
          break;
        case 'competitors':
          await fetchCompetitors();
          break;
        case 'music':
          await fetchMusicAnalytics();
          break;
        case 'ml-analysis':
          await fetchMLAnalysis();
          break;
        case 'users':
          await fetchUsers();
          break;
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchPricingTrends = async () => {
    const response = await fetch(`${API_BASE_URL}/api/admin/pricing-trends`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error('Failed to fetch pricing trends');
    const data = await response.json();
    setPricingTrends(data.pricing_trends || []);
  };

  const fetchCompetitors = async () => {
    const response = await fetch(`${API_BASE_URL}/api/admin/competitor-data`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error('Failed to fetch competitor data');
    const data = await response.json();
    setCompetitors(data.competitors || []);
  };

  const fetchMusicAnalytics = async () => {
    const response = await fetch(`${API_BASE_URL}/api/admin/music-analytics`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error('Failed to fetch music analytics');
    const data = await response.json();
    setMusicAnalytics(data.analytics);
  };

  const fetchMLAnalysis = async () => {
    const response = await fetch(`${API_BASE_URL}/api/admin/ml-price-analysis`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error('Failed to fetch ML analysis');
    const data = await response.json();
    setMlAnalysis(data.recommendations || []);
  };

  const fetchUsers = async () => {
    const response = await fetch(
      `${API_BASE_URL}/api/admin/users?page=${usersPagination.page}&per_page=${usersPagination.per_page}`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    if (!response.ok) throw new Error('Failed to fetch users');
    const data = await response.json();
    setUsers(data.users || []);
    setUsersPagination({ ...usersPagination, ...data.pagination });
  };

  const updatePrice = async (planId, newPrice) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/admin/update-price`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ plan_id: planId, new_price: parseFloat(newPrice) })
      });
      
      if (!response.ok) throw new Error('Failed to update price');
      
      alert('Price updated successfully');
      await fetchPricingTrends();
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  const updateUserStatus = async (userId, status) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/admin/update-user-status`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ user_id: userId, status })
      });
      
      if (!response.ok) throw new Error('Failed to update user status');
      
      alert('User status updated successfully');
      await fetchUsers();
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  const updateUserRole = async (userId, role) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/admin/update-user-role`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ user_id: userId, role })
      });
      
      if (!response.ok) throw new Error('Failed to update user role');
      
      alert('User role updated successfully');
      await fetchUsers();
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  const renderPricingSection = () => (
    <div className="admin-section">
      <h2>Subscription Pricing Trends</h2>
      {pricingTrends.map(plan => {
        const [newPrice, setNewPrice] = React.useState('');
        
        return (
          <div key={plan.plan_id} className="pricing-card">
            <h3>{plan.plan_name}</h3>
            <div className="current-price">
              <span>Current Price:</span>
              <strong>${plan.current_price}</strong>
            </div>
            <div className="price-update-form">
              <input
                type="number"
                step="0.01"
                placeholder="New price"
                value={newPrice}
                onChange={(e) => setNewPrice(e.target.value)}
              />
              <button onClick={() => {
                if (newPrice) {
                  updatePrice(plan.plan_id, newPrice);
                  setNewPrice('');
                }
              }}>
                Update Price
              </button>
            </div>
            {plan.price_history && plan.price_history.length > 0 && (
              <div className="price-history">
                <h4>Price History</h4>
                <table>
                  <thead>
                    <tr>
                      <th>Price</th>
                      <th>Effective From</th>
                    </tr>
                  </thead>
                  <tbody>
                    {plan.price_history.map((history, idx) => (
                      <tr key={idx}>
                        <td>${history.price}</td>
                        <td>{history.effective_from ? new Date(history.effective_from).toLocaleDateString() : 'N/A'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );

  const renderCompetitorsSection = () => (
    <div className="admin-section">
      <h2>Competitor Analysis</h2>
      {competitors.map(competitor => (
        <div key={competitor.competitor_id} className="competitor-card">
          <h3>{competitor.name}</h3>
          {competitor.website && (
            <p className="competitor-website">
              <a href={competitor.website} target="_blank" rel="noopener noreferrer">
                {competitor.website}
              </a>
            </p>
          )}
          {competitor.notes && <p className="competitor-notes">{competitor.notes}</p>}
          <div className="competitor-plans">
            <h4>Subscription Plans</h4>
            {competitor.plans.map(plan => (
              <div key={plan.plan_id} className="plan-item">
                <div className="plan-name">{plan.plan_name}</div>
                <div className="plan-details">
                  <span>Period: {plan.billing_period}</span>
                  {plan.latest_price && <span>Price: ${plan.latest_price}</span>}
                  {plan.is_student && <span className="badge">Student</span>}
                  {plan.is_family && <span className="badge">Family</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );

  const renderMusicSection = () => (
    <div className="admin-section">
      <h2>Music Analytics</h2>
      {musicAnalytics && (
        <>
          <div className="analytics-stat">
            <span>Total Tracks:</span>
            <strong>{musicAnalytics.total_tracks}</strong>
          </div>
          
          <div className="top-tracks">
            <h3>Top 10 Most Played Tracks</h3>
            <table>
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Artist</th>
                  <th>Play Count</th>
                </tr>
              </thead>
              <tbody>
                {musicAnalytics.top_tracks.map((track, idx) => (
                  <tr key={idx}>
                    <td>{track.title}</td>
                    <td>{track.artist}</td>
                    <td>{track.play_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          <div className="plays-chart">
            <h3>Plays Over Time (Last 30 Days)</h3>
            <div className="simple-chart">
              {musicAnalytics.plays_by_date.map((day, idx) => (
                <div key={idx} className="chart-bar">
                  <div className="bar-label">{new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</div>
                  <div className="bar-container">
                    <div 
                      className="bar-fill" 
                      style={{ 
                        width: `${Math.min(100, (day.play_count / Math.max(...musicAnalytics.plays_by_date.map(d => d.play_count))) * 100)}%` 
                      }}
                    ></div>
                  </div>
                  <div className="bar-value">{day.play_count}</div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );

  const renderMLAnalysisSection = () => (
    <div className="admin-section">
      <h2>ML Price Recommendations</h2>
      <p className="section-description">
        AI-powered pricing analysis based on competitor data and market trends
      </p>
      {mlAnalysis.map((rec, idx) => (
        <div key={idx} className={`ml-recommendation ${rec.recommendation}`}>
          <h3>{rec.plan_name}</h3>
          <div className="ml-stats">
            <div className="stat">
              <span>Current Price:</span>
              <strong>${rec.current_price}</strong>
            </div>
            <div className="stat">
              <span>Recommended Price:</span>
              <strong>${rec.recommended_price}</strong>
            </div>
            <div className="stat">
              <span>Competitor Avg:</span>
              <strong>{rec.competitor_avg ? `$${rec.competitor_avg.toFixed(2)}` : 'N/A'}</strong>
            </div>
          </div>
          <div className={`recommendation-badge ${rec.recommendation}`}>
            {rec.recommendation === 'increase' && '↑ '}
            {rec.recommendation === 'decrease' && '↓ '}
            {rec.recommendation.toUpperCase()}
            {rec.price_diff !== 0 && ` (${rec.price_diff > 0 ? '+' : ''}$${rec.price_diff})`}
          </div>
        </div>
      ))}
    </div>
  );

  const renderUsersSection = () => (
    <div className="admin-section">
      <h2>User Management</h2>
      <table className="users-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Email</th>
            <th>Username</th>
            <th>Role</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map(user => (
            <tr key={user.user_id}>
              <td>{user.user_id}</td>
              <td>{user.email}</td>
              <td>{user.username}</td>
              <td>
                <span className={`role-badge ${user.role}`}>{user.role}</span>
              </td>
              <td>
                <span className={`status-badge ${user.status}`}>{user.status}</span>
              </td>
              <td className="actions-cell">
                <select
                  value={user.status}
                  onChange={(e) => updateUserStatus(user.user_id, e.target.value)}
                  className="action-select"
                >
                  <option value="active">Active</option>
                  <option value="banned">Banned</option>
                  <option value="inactive">Inactive</option>
                </select>
                <select
                  value={user.role}
                  onChange={(e) => updateUserRole(user.user_id, e.target.value)}
                  className="action-select"
                >
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      
      <div className="pagination">
        <button
          disabled={usersPagination.page === 1}
          onClick={() => setUsersPagination({ ...usersPagination, page: usersPagination.page - 1 })}
        >
          Previous
        </button>
        <span>Page {usersPagination.page} of {usersPagination.total_pages}</span>
        <button
          disabled={usersPagination.page >= usersPagination.total_pages}
          onClick={() => setUsersPagination({ ...usersPagination, page: usersPagination.page + 1 })}
        >
          Next
        </button>
      </div>
    </div>
  );

  return (
    <div className="admin-dashboard">
      <div className="admin-header">
        <h1>Admin Dashboard</h1>
        <p>Manage pricing, users, and analyze platform performance</p>
      </div>

      <div className="admin-tabs">
        <button
          className={activeTab === 'pricing' ? 'active' : ''}
          onClick={() => setActiveTab('pricing')}
        >
          Price Trends
        </button>
        <button
          className={activeTab === 'competitors' ? 'active' : ''}
          onClick={() => setActiveTab('competitors')}
        >
          Competitors
        </button>
        <button
          className={activeTab === 'music' ? 'active' : ''}
          onClick={() => setActiveTab('music')}
        >
          Music Analytics
        </button>
        <button
          className={activeTab === 'ml-analysis' ? 'active' : ''}
          onClick={() => setActiveTab('ml-analysis')}
        >
          ML Price Analysis
        </button>
        <button
          className={activeTab === 'users' ? 'active' : ''}
          onClick={() => setActiveTab('users')}
        >
          User Management
        </button>
      </div>

      <div className="admin-content">
        {loading && <div className="loading">Loading...</div>}
        {error && <div className="error">Error: {error}</div>}
        
        {!loading && !error && (
          <>
            {activeTab === 'pricing' && renderPricingSection()}
            {activeTab === 'competitors' && renderCompetitorsSection()}
            {activeTab === 'music' && renderMusicSection()}
            {activeTab === 'ml-analysis' && renderMLAnalysisSection()}
            {activeTab === 'users' && renderUsersSection()}
          </>
        )}
      </div>
    </div>
  );
}

export default AdminDashboard;
