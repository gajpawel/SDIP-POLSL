import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { LogIn, Train, Monitor, Volume2, Users } from 'lucide-react';

export default function LoginPage({ setIsLoggedIn }) {
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);

  const navigate = useNavigate();

  // Monitorowanie rozmiaru okna dla ewentualnych dynamicznych zmian w logice (opcjonalne)
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    window.addEventListener('resize', handleResize);
    
    const roleId = sessionStorage.getItem("role_id");
    if (roleId) {
      navigate(roleId !== null ? "/dashboard" : "/");
    }

    return () => window.removeEventListener('resize', handleResize);
  }, [navigate]);

  const handleLogin = async (e) => {
    e.preventDefault();

    const response = await fetch(`/api/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ login, password }),
    });

    if (response.ok) {
      const data = await response.json();
      sessionStorage.setItem("role_id", data.role_id);
      sessionStorage.setItem("admin_id", data.admin_id);
      setIsLoggedIn(true);
      navigate(data.role_id !== null ? "/dashboard" : "/");
    } else {
      setMessage("Błąd logowania - sprawdź dane");
    }
  };

  const systemFeatures = [
    {
      icon: Train,
      title: "Zarządzanie Rozkładem",
      description: "Pełna kontrola nad rozkładem jazdy. Edycja czasów i torów w czasie rzeczywistym.",
    },
    {
      icon: Monitor,
      title: "Wyświetlacze Dworcowe",
      description: "Zdalne zarządzanie treścią i wyglądem tablic informacyjnych.",
    },
    {
      icon: Volume2,
      title: "Komunikaty Głosowe",
      description: "Automatyczne zapowiedzi TTS ElevenLabs z uwzględnieniem opóźnień.",
    },
    {
      icon: Users,
      title: "Użytkownicy",
      description: "Zarządzanie uprawnieniami i przypisywanie pracowników do stacji.",
    },
  ];

  return (
    <div style={styles.pageContainer}>
      {/* Wstrzyknięcie Media Queries do obsługi responsywności */}
      <style>{`
        @media (max-width: 992px) {
          .main-content {
            flex-direction: column-reverse !important;
            max-width: 500px !important;
          }
          .info-panel {
            padding: 25px !important;
          }
          .features-grid {
            grid-template-columns: 1fr !important;
            gap: 15px !important;
          }
          .welcome-header {
            font-size: 1.8rem !important;
          }
        }
        @media (max-width: 480px) {
          .login-panel {
            padding: 20px !important;
          }
          .login-box {
            padding: 20px !important;
          }
        }
      `}</style>

      <div style={styles.mainContent} className="main-content">
        {/* Panel Logowania */}
        <div style={styles.loginPanel} className="login-panel">
          <div style={styles.loginBox} className="login-box">
            <LogIn style={styles.loginIcon} />
            <h2 style={styles.loginHeader}>Logowanie</h2>
            
            <form onSubmit={handleLogin} style={styles.form}>
              <input
                type="text"
                placeholder="Login / Nazwa Użytkownika"
                value={login}
                onChange={(e) => setLogin(e.target.value)}
                style={styles.input}
                autoComplete="username"
              />
              <input
                type="password"
                placeholder="Hasło"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={styles.input}
                autoComplete="current-password"
              />
              
              <button type="submit" style={styles.button}>
                Zaloguj się
              </button>
            </form>
            
            {message && <h3 style={styles.message}>{message}</h3>}
          </div>
        </div>
        {/* Panel Powitalny / Informacyjny */}
        <div style={styles.infoPanel} className="info-panel">
          <h1 style={styles.welcomeHeader} className="welcome-header">
            System Dynamicznej Informacji Pasażerskiej (SDIP)
          </h1>
          <p style={styles.tagline}>
            Centralne narzędzie do zarządzania ruchem i komunikacją na Twojej stacji.
          </p>

          <div style={styles.featuresGrid} className="features-grid">
            {systemFeatures.map((feature, index) => (
              <div key={index} style={styles.featureItem}>
                <feature.icon style={styles.featureIcon} />
                <div>
                  <h4 style={styles.featureTitle}>{feature.title}</h4>
                  <p style={styles.featureDescription}>{feature.description}</p>
                </div>
              </div>
            ))}
          </div>

          <p style={styles.contactText}>
            Nie masz konta? Skontaktuj się z Administratorem Systemu.
          </p>
        </div>
      </div>
    </div>
  );
}

const styles = {
  pageContainer: {
    minHeight: '100vh',
    backgroundColor: '#f0f2f5',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    padding: '10px', // Zmniejszone na mobile
    boxSizing: 'border-box',
  },
  mainContent: {
    display: 'flex',
    flexDirection: 'row',
    maxWidth: '1100px',
    width: '100%',
    borderRadius: '16px',
    overflow: 'hidden',
    boxShadow: '0 15px 35px rgba(0,0,0,0.12)',
    backgroundColor: '#fff',
  },
  
  // Panel Informacyjny
  infoPanel: {
    flex: 1.4,
    backgroundColor: '#ffffff',
    padding: '50px',
    textAlign: 'left',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
  },
  welcomeHeader: {
    color: '#002244',
    fontSize: '2.2rem',
    fontWeight: '800',
    marginBottom: '10px',
    lineHeight: '1.2',
  },
  tagline: {
    color: '#555',
    fontSize: '1.1rem',
    marginBottom: '25px',
    borderBottom: '2px solid #f0f4f8',
    paddingBottom: '20px',
  },
  featuresGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '25px',
    marginBottom: '20px',
  },
  featureItem: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '12px',
  },
  featureIcon: {
    width: 28,
    height: 28,
    color: '#0055aa',
    flexShrink: 0,
    marginTop: '3px',
  },
  featureTitle: {
    color: '#2c3e50',
    margin: '0 0 4px 0',
    fontSize: '0.95rem',
    fontWeight: '700',
  },
  featureDescription: {
    color: '#7f8c8d',
    margin: 0,
    fontSize: '0.8rem',
    lineHeight: '1.4',
  },
  contactText: {
    color: '#7f8c8d',
    marginTop: 'auto',
    paddingTop: '20px',
    borderTop: '1px solid #f0f4f8',
    fontSize: '0.85rem',
  },

  // Panel Logowania
  loginPanel: {
    flex: 1,
    backgroundColor: '#0055aa',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    padding: '40px',
    position: 'relative',
  },
  loginBox: {
    width: '100%',
    maxWidth: '320px',
    backgroundColor: 'white',
    padding: '35px',
    borderRadius: '12px',
    boxShadow: '0 8px 25px rgba(0,0,0,0.15)',
    textAlign: 'center',
  },
  loginIcon: {
    width: 44,
    height: 44,
    color: '#0055aa',
    marginBottom: '15px',
  },
  loginHeader: {
    color: '#002244',
    marginBottom: '25px',
    fontSize: '1.6rem',
    fontWeight: '700',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  input: {
    padding: '14px',
    borderRadius: '10px',
    border: '1.5px solid #e1e8ed',
    fontSize: '1rem',
    outline: 'none',
    transition: 'border-color 0.2s',
  },
  button: {
    padding: '14px',
    backgroundColor: '#003366',
    color: 'white',
    border: 'none',
    borderRadius: '10px',
    fontSize: '1rem',
    cursor: 'pointer',
    fontWeight: '700',
    transition: 'transform 0.1s, background-color 0.2s',
    marginTop: '10px',
  },
  message: {
    color: '#e74c3c',
    marginTop: '20px',
    fontSize: '0.9rem',
    fontWeight: '600',
  },
};