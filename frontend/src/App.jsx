// src/App.jsx
import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { PlayerProvider } from "./context/PlayerContext";
import ProtectedRoute from "./components/ProtectedRoute";
import NavigationHeader from "./components/NavigationHeader";
import LandingPage from "./pages/LandingPage.jsx";
import Home from "./pages/Home.jsx";
import Login from "./pages/Login.jsx";
import Signup from "./pages/Signup.jsx";
import ForgotPassword from "./pages/ForgotPassword.jsx";
import ResetPassword from "./pages/ResetPassword.jsx";
import Settings from "./pages/Settings.jsx";
import Library from "./pages/Library.jsx";
import AlbumDetail from "./pages/AlbumDetail.jsx";
import PlaylistPage from "./pages/Playlist.jsx";
import Playlists from "./pages/Playlists.jsx";
import LikedSongs from "./pages/LikedSongs.jsx";
import NowPlaying from "./pages/NowPlaying.jsx";
import PaymentSuccess from "./pages/PaymentSuccess.jsx";
import PaymentCancelled from "./pages/PaymentCancelled.jsx";
import PlayerBar from "./components/PlayerBar.jsx";
import "./styles/App.css";

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <PlayerProvider>
          <div className="app-root">
            <Routes>
            {/* Public routes */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            
            {/* Protected routes with NavigationHeader */}
            <Route
              path="/app"
              element={
                <ProtectedRoute>
                  <>
                    <NavigationHeader />
                    <Home />
                  </>
                </ProtectedRoute>
              }
            />
              <Route
                path="/playlists"
                element={
                  <ProtectedRoute>
                    <>
                      <NavigationHeader />
                      <Playlists />
                    </>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/liked"
                element={
                  <ProtectedRoute>
                    <>
                      <NavigationHeader />
                      <LikedSongs />
                    </>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/library"
                element={
                  <ProtectedRoute>
                    <>
                      <NavigationHeader />
                      <Library />
                    </>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/album/:albumName"
                element={
                  <ProtectedRoute>
                    <>
                      <NavigationHeader />
                      <AlbumDetail />
                    </>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/playlist/:id"
                element={
                  <ProtectedRoute>
                    <>
                      <NavigationHeader />
                      <PlaylistPage />
                    </>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/now-playing"
                element={
                  <ProtectedRoute>
                    <>
                      <NavigationHeader />
                      <NowPlaying />
                    </>
                  </ProtectedRoute>
                }
              />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <>
                    <NavigationHeader />
                    <Settings />
                  </>
                </ProtectedRoute>
              }
            />
            <Route path="/payment-success" element={<PaymentSuccess />} />
            <Route path="/payment-cancelled" element={<PaymentCancelled />} />
            
            {/* Catch all - redirect to landing page */}
            <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
            <PlayerBar />
          </div>
        </PlayerProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
