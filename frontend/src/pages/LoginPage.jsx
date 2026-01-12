import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { LogIn, Train, Monitor, Volume2, Users } from 'lucide-react';

export default function LoginPage({ setIsLoggedIn
}) {
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  const navigate = useNavigate();

  useEffect(() => {
    const roleId = sessionStorage.getItem("role_id");
    if (roleId) {
      if (roleId !== null) navigate("/dashboard");
      else navigate("/");
    }
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
      setIsLoggedIn(true); // <-- aktualizujemy Layout
      if (data.role_id !== null) navigate("/dashboard");
      else navigate("/");
    } else {
      setMessage("Błąd logowania");
    }
  };

  // Definicja dostępnych funkcji w systemie
    const systemFeatures = [
        {
            icon: Train,
            title: "Zarządzanie Rozkładem",
            description: "Pełna kontrola nad rozkładem jazdy. Możliwość edycji i aktualizacji czasów przyjazdów, odjazdów oraz torów/peronów w czasie rzeczywistym.",
        },
        {
            icon: Monitor,
            title: "Wyświetlacze Dworcowe",
            description: "Zdalne zarządzanie treścią i wyglądem tablic informacyjnych i wyświetlaczy stacyjnych.",
        },
        {
            icon: Volume2,
            title: "Komunikaty Głosowe (TTS)",
            description: "Automatyczne generowanie zapowiedzi głosowych w oparciu o technologię Text-to-Speech (ElevenLabs) z uwzględnieniem opóźnień.",
        },
        {
            icon: Users,
            title: "Zarządzanie Użytkownikami",
            description: "Dostęp dla Administratora Głównego: kontrola ról, uprawnień i przypisywania użytkowników do stacji.",
        },
    ];

    return (
        <div style={styles.pageContainer}>
            <div style={styles.mainContent}>
                {/* 1. Panel Logowania */}
                <div style={styles.loginPanel}>
                    <div style={styles.loginBox}>
                        <LogIn style={styles.loginIcon} />
                        <h2 style={styles.loginHeader}>Logowanie</h2>
                        
                        <form onSubmit={handleLogin} style={styles.form}>
                            <input
                                type="text"
                                placeholder="Login / Nazwa Użytkownika"
                                value={login}
                                onChange={(e) => setLogin(e.target.value)}
                                style={styles.input}
                            />
                            <input
                                type="password"
                                placeholder="Hasło"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                style={styles.input}
                            />
                            
                            <button type="submit" style={styles.button}>
                                Zaloguj się
                            </button>
                        </form>
                        
                        {message && <h3 style={styles.message}>{message}</h3>}
                    </div>
                </div>
                {/* 2. Panel Powitalny / Informacyjny */}
                <div style={styles.infoPanel}>
                    <h1 style={styles.welcomeHeader}>
                        System Dynamicznej Informacji Pasażerskiej (SDIP)
                    </h1>
                    <p style={styles.tagline}>
                        Centralne narzędzie do zarządzania ruchem, rozkładem i komunikacją na Twojej stacji.
                    </p>

                    <div style={styles.featuresGrid}>
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
                        Nie masz konta? Prosimy o kontakt z Administratorem Systemu w celu nadania dostępu.
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
        padding: '20px',
    },
    mainContent: {
        display: 'flex',
        flexDirection: 'row',
        maxWidth: '1200px',
        width: '100%',
        borderRadius: '15px',
        overflow: 'hidden',
        boxShadow: '0 10px 30px rgba(0,0,0,0.1)',
    },
    
    // --- Panel Powitalny (Lewa strona) ---
    infoPanel: {
        flex: 1.5,
        backgroundColor: '#ffffff',
        padding: '40px',
        textAlign: 'left',
    },
    welcomeHeader: {
        color: '#003366',
        fontSize: '2.5rem',
        marginBottom: '10px',
    },
    tagline: {
        color: '#666',
        fontSize: '1.2rem',
        marginBottom: '30px',
        borderBottom: '1px solid #eee',
        paddingBottom: '20px',
    },
    featuresGrid: {
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '20px',
        marginBottom: '30px',
    },
    featureItem: {
        display: 'flex',
        alignItems: 'flex-start',
        gap: '15px',
    },
    featureIcon: {
        width: 32,
        height: 32,
        color: '#0055aa',
        flexShrink: 0,
        marginTop: '5px',
    },
    featureTitle: {
        color: '#333',
        margin: '0 0 5px 0',
        fontSize: '1rem',
    },
    featureDescription: {
        color: '#777',
        margin: 0,
        fontSize: '0.85rem',
    },
    contactText: {
        color: '#003366',
        marginTop: '20px',
        padding: '10px',
        borderTop: '1px solid #eee',
        fontSize: '0.9rem',
    },

    // --- Panel Logowania (Prawa strona) ---
    loginPanel: {
        flex: 1,
        backgroundColor: '#0055aa',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '40px',
    },
    loginBox: {
        width: '100%',
        maxWidth: '300px',
        backgroundColor: 'white',
        padding: '30px',
        borderRadius: '10px',
        boxShadow: '0 5px 15px rgba(0,0,0,0.2)',
        textAlign: 'center',
    },
    loginIcon: {
        width: 40,
        height: 40,
        color: '#0055aa',
        marginBottom: '15px',
    },
    loginHeader: {
        color: '#003366',
        marginBottom: '25px',
        fontSize: '1.8rem',
    },
    form: {
        display: 'flex',
        flexDirection: 'column',
        gap: '15px',
    },
    input: {
        padding: '12px',
        borderRadius: '8px',
        border: '1px solid #ddd',
        fontSize: '16px',
        outlineColor: '#0055aa',
    },
    button: {
        padding: '12px',
        backgroundColor: '#003366',
        color: 'white',
        border: 'none',
        borderRadius: '8px',
        fontSize: '16px',
        cursor: 'pointer',
        fontWeight: 'bold',
        transition: 'background-color 0.2s',
    },
    message: {
        color: '#cc0000',
        marginTop: '20px',
        fontSize: '0.9rem',
        fontWeight: 'bold',
    },
};
