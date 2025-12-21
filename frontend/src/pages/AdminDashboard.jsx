// src/pages/AdminDashboard.jsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import '../styles/AdminDashboard.css';
import PricingCard from '../components/PricingCard.jsx';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5173';

function AdminDashboard() {
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState('pricing');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // State for different sections
  const [pricingTrends, setPricingTrends] = useState([]);
  const [pricingRollups, setPricingRollups] = useState({
    active_plans: 0,
    total_price_changes: 0,
    avg_current_price: null,
  });
  const [competitors, setCompetitors] = useState([]);
  const [musicAnalytics, setMusicAnalytics] = useState(null);
  const [mlAnalysis, setMlAnalysis] = useState([]);
  const [users, setUsers] = useState([]);
  const [usersPagination, setUsersPagination] = useState({ page: 1, per_page: 20 });
  const [revenueAnalytics, setRevenueAnalytics] = useState(null);
  const [platformStats, setPlatformStats] = useState(null);
  const [userActivity, setUserActivity] = useState(null);
  
  // Fetch data based on active tab
  useEffect(() => {
    fetchTabData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
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
        case 'revenue':
          await fetchRevenueAnalytics();
          break;
        case 'platform':
          await fetchPlatformStats();
          break;
        case 'activity':
          await fetchUserActivity();
          break;
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchPricingTrends = async () => {
    const qs = new URLSearchParams({
      granularity: "monthly",
      include_series: "true",
      include_rollups: "true",
    }).toString();

    const response = await fetch(
      `${API_BASE_URL}/api/admin/pricing-trends?${qs}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );

    if (!response.ok) throw new Error("Failed to fetch pricing trends");

    const data = await response.json();

    // NEW SHAPE: pricing_trends = { plans: [...], rollups: {...} }
    const payload = data.pricing_trends || { plans: [], rollups: null };

    setPricingTrends(payload.plans || []);
    setPricingRollups(payload.rollups || null); // add a state var for rollups
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

  const fetchRevenueAnalytics = async () => {
    // Mock data for demonstration - in production, this would be a real API endpoint
    // This shows what kind of revenue analytics would be useful
    const mockRevenue = {
      total_revenue: 125430.50,
      monthly_recurring_revenue: 15678.90,
      annual_recurring_revenue: 188146.80,
      revenue_by_plan: [
        { plan_name: 'Basic', revenue: 35670.20, subscribers: 1234 },
        { plan_name: 'Premium', revenue: 67890.50, subscribers: 678 },
        { plan_name: 'Family', revenue: 21870.80, subscribers: 234 }
      ],
      revenue_trend: [
        { month: 'Jan', revenue: 10234.50 },
        { month: 'Feb', revenue: 11456.80 },
        { month: 'Mar', revenue: 12890.40 },
        { month: 'Apr', revenue: 13670.20 },
        { month: 'May', revenue: 14567.30 },
        { month: 'Jun', revenue: 15678.90 }
      ],
      churn_rate: 2.3,
      growth_rate: 8.5
    };
    setRevenueAnalytics(mockRevenue);
  };

  const fetchPlatformStats = async () => {
    // Mock data for demonstration - in production, this would be a real API endpoint
    const mockStats = {
      total_users: 5432,
      active_users: 4123,
      total_tracks: 125678,
      total_albums: 8945,
      total_artists: 4567,
      total_playlists: 12345,
      total_plays: 2345678,
      storage_used: '1.2 TB',
      bandwidth_used: '45.6 TB',
      user_growth: [
        { month: 'Jan', users: 4200 },
        { month: 'Feb', users: 4456 },
        { month: 'Mar', users: 4789 },
        { month: 'Apr', users: 5012 },
        { month: 'May', users: 5234 },
        { month: 'Jun', users: 5432 }
      ]
    };
    setPlatformStats(mockStats);
  };

  const fetchUserActivity = async () => {
    // Mock data for demonstration - in production, this would be a real API endpoint
    const mockActivity = {
      daily_active_users: 1234,
      weekly_active_users: 3456,
      monthly_active_users: 4123,
      avg_session_duration: '23.5 min',
      avg_sessions_per_user: 4.2,
      peak_hours: [
        { hour: '6 AM', users: 234 },
        { hour: '12 PM', users: 678 },
        { hour: '6 PM', users: 1234 },
        { hour: '9 PM', users: 1089 }
      ],
      top_features: [
        { feature: 'Music Streaming', usage: 89.5 },
        { feature: 'Playlists', usage: 67.8 },
        { feature: 'Search', usage: 54.3 },
        { feature: 'Recommendations', usage: 42.1 }
      ],
      retention_rate: {
        day_1: 85.2,
        day_7: 62.4,
        day_30: 45.8
      }
    };
    setUserActivity(mockActivity);
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

      {pricingRollups && (
        <div className="pricing-rollups">
          <div><strong>Active Plans:</strong> {pricingRollups.active_plans}</div>
          <div><strong>Total Changes:</strong> {pricingRollups.total_price_changes}</div>
          <div><strong>Avg Current Price:</strong> ${pricingRollups.avg_current_price?.toFixed(2)}</div>
        </div>
      )}

      {pricingTrends.map((plan) => (
        <PricingCard
          key={plan.plan_id}
          plan={plan}
          onUpdatePrice={updatePrice}
        />
      ))}
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
      <div className="users-table-container">
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
      </div>
      
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

  const renderRevenueSection = () => (
    <div className="admin-section">
      <h2>Revenue Analytics</h2>
      {revenueAnalytics && (
        <>
          <div className="stats-grid">
            <div className="stat-card">
              <h3>Total Revenue</h3>
              <div className="stat-value">${revenueAnalytics.total_revenue.toLocaleString()}</div>
            </div>
            <div className="stat-card">
              <h3>MRR</h3>
              <div className="stat-value">${revenueAnalytics.monthly_recurring_revenue.toLocaleString()}</div>
              <div className="stat-label">Monthly Recurring Revenue</div>
            </div>
            <div className="stat-card">
              <h3>ARR</h3>
              <div className="stat-value">${revenueAnalytics.annual_recurring_revenue.toLocaleString()}</div>
              <div className="stat-label">Annual Recurring Revenue</div>
            </div>
            <div className="stat-card">
              <h3>Growth Rate</h3>
              <div className="stat-value positive">{revenueAnalytics.growth_rate}%</div>
            </div>
          </div>

          <div className="revenue-by-plan">
            <h3>Revenue by Subscription Plan</h3>
            <div className="plan-revenue-grid">
              {revenueAnalytics.revenue_by_plan.map((plan, idx) => (
                <div key={idx} className="plan-revenue-card">
                  <h4>{plan.plan_name}</h4>
                  <div className="revenue-amount">${plan.revenue.toLocaleString()}</div>
                  <div className="subscriber-count">{plan.subscribers} subscribers</div>
                </div>
              ))}
            </div>
          </div>

          <div className="revenue-trend-section">
            <h3>Revenue Trend (Last 6 Months)</h3>
            <div className="simple-chart">
              {revenueAnalytics.revenue_trend.map((item, idx) => {
                const maxRevenue = Math.max(...revenueAnalytics.revenue_trend.map(d => d.revenue));
                return (
                  <div key={idx} className="chart-bar">
                    <div className="bar-label">{item.month}</div>
                    <div className="bar-container">
                      <div 
                        className="bar-fill revenue-bar" 
                        style={{ width: `${(item.revenue / maxRevenue) * 100}%` }}
                      ></div>
                    </div>
                    <div className="bar-value">${(item.revenue / 1000).toFixed(1)}k</div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="stats-row">
            <div className="stat-card">
              <h3>Churn Rate</h3>
              <div className="stat-value negative">{revenueAnalytics.churn_rate}%</div>
            </div>
          </div>
        </>
      )}
    </div>
  );

  const renderPlatformStatsSection = () => (
    <div className="admin-section">
      <h2>Platform Statistics</h2>
      {platformStats && (
        <>
          <div className="stats-grid">
            <div className="stat-card">
              <h3>Total Users</h3>
              <div className="stat-value">{platformStats.total_users.toLocaleString()}</div>
              <div className="stat-sublabel">Active: {platformStats.active_users.toLocaleString()}</div>
            </div>
            <div className="stat-card">
              <h3>Music Library</h3>
              <div className="stat-value">{platformStats.total_tracks.toLocaleString()}</div>
              <div className="stat-sublabel">Tracks</div>
            </div>
            <div className="stat-card">
              <h3>Albums</h3>
              <div className="stat-value">{platformStats.total_albums.toLocaleString()}</div>
            </div>
            <div className="stat-card">
              <h3>Artists</h3>
              <div className="stat-value">{platformStats.total_artists.toLocaleString()}</div>
            </div>
            <div className="stat-card">
              <h3>Playlists</h3>
              <div className="stat-value">{platformStats.total_playlists.toLocaleString()}</div>
            </div>
            <div className="stat-card">
              <h3>Total Plays</h3>
              <div className="stat-value">{(platformStats.total_plays / 1000000).toFixed(1)}M</div>
            </div>
            <div className="stat-card">
              <h3>Storage Used</h3>
              <div className="stat-value">{platformStats.storage_used}</div>
            </div>
            <div className="stat-card">
              <h3>Bandwidth</h3>
              <div className="stat-value">{platformStats.bandwidth_used}</div>
            </div>
          </div>

          <div className="user-growth-section">
            <h3>User Growth (Last 6 Months)</h3>
            <div className="simple-chart">
              {platformStats.user_growth.map((item, idx) => {
                const maxUsers = Math.max(...platformStats.user_growth.map(d => d.users));
                return (
                  <div key={idx} className="chart-bar">
                    <div className="bar-label">{item.month}</div>
                    <div className="bar-container">
                      <div 
                        className="bar-fill growth-bar" 
                        style={{ width: `${(item.users / maxUsers) * 100}%` }}
                      ></div>
                    </div>
                    <div className="bar-value">{item.users.toLocaleString()}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );

  const renderUserActivitySection = () => (
    <div className="admin-section">
      <h2>User Activity Analytics</h2>
      {userActivity && (
        <>
          <div className="stats-grid">
            <div className="stat-card">
              <h3>Daily Active Users</h3>
              <div className="stat-value">{userActivity.daily_active_users.toLocaleString()}</div>
            </div>
            <div className="stat-card">
              <h3>Weekly Active Users</h3>
              <div className="stat-value">{userActivity.weekly_active_users.toLocaleString()}</div>
            </div>
            <div className="stat-card">
              <h3>Monthly Active Users</h3>
              <div className="stat-value">{userActivity.monthly_active_users.toLocaleString()}</div>
            </div>
            <div className="stat-card">
              <h3>Avg Session Duration</h3>
              <div className="stat-value">{userActivity.avg_session_duration}</div>
            </div>
          </div>

          <div className="peak-hours-section">
            <h3>Peak Usage Hours</h3>
            <div className="simple-chart">
              {userActivity.peak_hours.map((item, idx) => {
                const maxUsers = Math.max(...userActivity.peak_hours.map(d => d.users));
                return (
                  <div key={idx} className="chart-bar">
                    <div className="bar-label">{item.hour}</div>
                    <div className="bar-container">
                      <div 
                        className="bar-fill activity-bar" 
                        style={{ width: `${(item.users / maxUsers) * 100}%` }}
                      ></div>
                    </div>
                    <div className="bar-value">{item.users.toLocaleString()}</div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="feature-usage-section">
            <h3>Feature Usage</h3>
            <div className="feature-grid">
              {userActivity.top_features.map((feature, idx) => (
                <div key={idx} className="feature-card">
                  <div className="feature-name">{feature.feature}</div>
                  <div className="usage-bar-container">
                    <div className="usage-bar" style={{ width: `${feature.usage}%` }}></div>
                  </div>
                  <div className="usage-percentage">{feature.usage}%</div>
                </div>
              ))}
            </div>
          </div>

          <div className="retention-section">
            <h3>User Retention</h3>
            <div className="retention-grid">
              <div className="retention-card">
                <h4>Day 1</h4>
                <div className="retention-value">{userActivity.retention_rate.day_1}%</div>
              </div>
              <div className="retention-card">
                <h4>Day 7</h4>
                <div className="retention-value">{userActivity.retention_rate.day_7}%</div>
              </div>
              <div className="retention-card">
                <h4>Day 30</h4>
                <div className="retention-value">{userActivity.retention_rate.day_30}%</div>
              </div>
            </div>
          </div>
        </>
      )}
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
          className={activeTab === 'revenue' ? 'active' : ''}
          onClick={() => setActiveTab('revenue')}
        >
          Revenue
        </button>
        <button
          className={activeTab === 'platform' ? 'active' : ''}
          onClick={() => setActiveTab('platform')}
        >
          Platform Stats
        </button>
        <button
          className={activeTab === 'activity' ? 'active' : ''}
          onClick={() => setActiveTab('activity')}
        >
          User Activity
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
            {activeTab === 'revenue' && renderRevenueSection()}
            {activeTab === 'platform' && renderPlatformStatsSection()}
            {activeTab === 'activity' && renderUserActivitySection()}
            {activeTab === 'users' && renderUsersSection()}
          </>
        )}
      </div>
    </div>
  );
}

export default AdminDashboard;
