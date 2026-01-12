import { useNavigate } from "react-router-dom";
import { Users, Train, Monitor, Speaker } from "lucide-react";
import { useStationData } from "../hooks/useStationData";

export default function Dashboard() {
  const navigate = useNavigate();
  
  const { roleId, stationId, stationName, loading, error } = useStationData();
    // Style kafelków
  const styles = {
    container: { padding: 40 },
    header: { color: "#003366", marginBottom: 30 },
    grid: {
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
      gap: "25px",
    },
    tile: {
      backgroundColor: "#ffffff",
      padding: "30px 20px",
      borderRadius: "10px",
      boxShadow: "0 3px 8px rgba(0,0,0,0.15)",
      cursor: "pointer",
      textAlign: "center",
      transition: "transform 0.15s ease, box-shadow 0.2s ease",
    },
    icon: { width: 48, height: 48, color: "#003366", marginBottom: 10 },
  };

  // Funkcja pomocnicza do efektu hover (w React inline styles to trochę uciążliwe)
  const handleMouseEnter = (e) => {
    e.currentTarget.style.transform = "translateY(-4px)";
    e.currentTarget.style.boxShadow = "0 6px 14px rgba(0,0,0,0.25)";
  };
  const handleMouseLeave = (e) => {
    e.currentTarget.style.transform = "none";
    e.currentTarget.style.boxShadow = "0 3px 8px rgba(0,0,0,0.15)";
  };

  // 3. Logika dla Dyżurnego (szybkie uruchamianie komunikatów)
  const handleDispatcherVoice = () => {
    alert("Tu uruchomi się komunikat głosowy natychmiast!");
    // Tu możesz wywołać fetch/socket do uruchomienia komunikatu
  };

  // KONFIGURACJA KAFELKÓW (Strategy Pattern)
  const allTiles = [
    {
      title: "Użytkownicy systemu",
      icon: Users,
      isVisible: roleId === 1, // Tylko Global Admin
      action: () => navigate("/users"),
    },
    {
      title: "Rozkład jazdy",
      icon: Train,
      isVisible: true, // Wszyscy widzą
      action: () => {
        if (roleId === 1) navigate("/choose-station/timetable"); // Admin wybiera stację
        else navigate(`/timetable`); // Reszta idzie do swojej stacji
      },
    },
    {
      title: "Wyświetlacze",
      icon: Monitor,
      isVisible: true, // Wszyscy widzą
      action: () => {
        if (roleId === 1) navigate("/choose-station/displays");
        else navigate(`/displays`);
      },
    },
    {
      title: "Komunikaty głosowe",
      icon: Speaker,
      isVisible: true, // Załóżmy, że wszyscy, ale działanie jest inne
      action: () => {
        if (roleId === 1) {
          navigate("/choose-station/voice-announcements"); // Admin wybiera stację
        } else {
          navigate(`/voice-announcements`); // Zarządca i dyżurny idzie do panelu
        }
      },
    },
  ];

  // Filtrujemy kafelki, które mają być widoczne dla danej roli
  const visibleTiles = allTiles.filter((tile) => tile.isVisible);

  if (loading) return <div style={{ padding: 40 }}>Ładowanie panelu...</div>;
  if (error) return <div style={{ padding: 40, color: "red" }}>Błąd: {error}</div>;

  return (
    <div style={styles.container}>
      <h2 style={styles.header}>
        {/* Wyświetlamy nazwę stacji jeśli użytkownik jest przypisany, w przeciwnym razie ogólny tytuł */}
        {stationName ? `${stationName} – Panel sterowania` : "Panel Administratora"}
      </h2>

      <div style={styles.grid}>
        {visibleTiles.map((tile, index) => {
          const IconComponent = tile.icon;
          return (
            <div
              key={index}
              style={styles.tile}
              onClick={tile.action}
              onMouseEnter={handleMouseEnter}
              onMouseLeave={handleMouseLeave}
            >
              <IconComponent style={styles.icon} />
              <h3 style={{ margin: 0, color: "#34495e" }}>{tile.title}</h3>
            </div>
          );
        })}
      </div>
    </div>
  );
}