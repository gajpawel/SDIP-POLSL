import { useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import "./Layout.css";

// Czas bezczynności w milisekundach (60 minut * 60 sekund * 1000 ms)
const SESSION_TIMEOUT = 60 * 60 * 1000; 

export default function Layout({ children, isLoggedIn, setIsLoggedIn }) {
  const navigate = useNavigate();
  const roleId = sessionStorage.getItem("role_id");

  // Funkcja wylogowania (używamy useCallback, aby była stabilna w zależnościach useEffect)
  const handleLogout = useCallback(() => {
    // Czyścimy dane sesji
    sessionStorage.removeItem("role_id");
    sessionStorage.removeItem("admin_id");
    sessionStorage.removeItem("last_activity"); // Czyścimy znacznik czasu
    
    setIsLoggedIn(false);
    navigate("/");
  }, [navigate, setIsLoggedIn]);

  useEffect(() => {
    // Jeśli użytkownik nie jest zalogowany, nie uruchamiamy licznika
    if (!isLoggedIn) return;

    let timeoutId;

    // Funkcja resetująca licznik czasu
    const resetTimer = () => {
      const now = Date.now();
      
      // Zapisz czas ostatniej aktywności
      sessionStorage.setItem("last_activity", now.toString());

      // Wyczyść poprzedni timeout i ustaw nowy
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        alert("Sesja wygasła z powodu bezczynności.");
        handleLogout();
      }, SESSION_TIMEOUT);
    };

    // Funkcja sprawdzająca sesję przy załadowaniu (np. po odświeżeniu strony)
    const checkInitialSession = () => {
      const lastActivity = sessionStorage.getItem("last_activity");
      
      if (lastActivity) {
        const timePassed = Date.now() - parseInt(lastActivity, 10);
        
        if (timePassed > SESSION_TIMEOUT) {
          // Jeśli od ostatniej aktywności minęło więcej niż 15 minut -> wyloguj od razu
          handleLogout();
          return; 
        }
      }
      
      // Jeśli sesja jest ok, uruchom timer
      resetTimer();
    };

    // Sprawdź sesję natychmiast po załadowaniu Layoutu
    checkInitialSession();

    // Lista zdarzeń, które uznajemy za "aktywność" użytkownika
    const events = [
      "click",
      "mousemove",
      "keypress",
      "scroll",
      "touchstart" // dla dotykowych ekranów
    ];

    // Dodajemy nasłuchiwacze do całego okna
    events.forEach((event) => window.addEventListener(event, resetTimer));

    // Sprzątanie po odmontowaniu komponentu (lub wylogowaniu)
    return () => {
      clearTimeout(timeoutId);
      events.forEach((event) => window.removeEventListener(event, resetTimer));
    };
  }, [isLoggedIn, handleLogout]);

  return (
    <div className="layout-container">
      {/* Pasek górny */}
      <header className="layout-header">
        <h1 className="header-logo">
            🧭 SDIP <span style={{ fontWeight: "normal", fontSize: "0.8em" }}>– System Informacji Pasażerskiej</span>
        </h1>
        
        <div className="header-actions">
          {roleId !== null && (
            <button className="btn-nav" onClick={() => navigate("/dashboard")}>
              {roleId === "1" ? "Panel Admina" : roleId === "2" ? "Panel Zarządcy" : "Panel Dyżurnego"}
            </button>
          )}
          {isLoggedIn && (
            <button className="btn-logout" onClick={handleLogout}>
              Wyloguj
            </button>
          )}
        </div>
      </header>

      {/* Główna zawartość */}
      <main className="layout-main">{children}</main>

      {/* Stopka */}
      <footer className="layout-footer">
        <p>© 2025 SDIP | Projekt inżynierski – PolSl</p>
      </footer>
    </div>
  );
}