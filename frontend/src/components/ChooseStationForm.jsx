import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";

export default function ChooseStationForm() {
  const [stations, setStations] = useState([]);
  const [recentStations, setRecentStations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const { type } = useParams();
  const navigate = useNavigate();

  // 🔹 Pobieranie stacji z API i historii z sessionStorage
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch("/api/admin/stations");
        if (!response.ok) throw new Error("Błąd pobierania stacji");
        const data = await response.json();
        setStations(data);
      } catch (err) {
        console.error("Błąd pobierania danych:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    // Ładowanie ostatnich stacji z sessionStorage
    const savedRecent = localStorage.getItem("recent_stations");
    if (savedRecent) {
      setRecentStations(JSON.parse(savedRecent));
    }
  }, []);

  // 🔹 Funkcja obsługująca wybór stacji (zarówno z szukajki jak i historii)
  const handleStationSelect = (station) => {
    // 1. Logika zapisu do historii (ostatnie 5)
    const newRecent = [
      station,
      ...recentStations.filter((s) => s.id !== station.id),
    ].slice(0, 5);
    
    setRecentStations(newRecent);
    localStorage.setItem("recent_stations", JSON.stringify(newRecent));

    // 2. Logika nawigacji (obsługa różnych typów z URL)
    // Uwaga: Obsługuje zarówno stringi (timetable) jak i ID z AdminPage (0, 1, 2)
    let path = "";
    if (type === "timetable" || type === "0") {
      path = `/timetable/${station.id}`;
    } else if (type === "displays" || type === "1") {
      path = `/displays/${station.id}`;
    } else if (type === "voice-announcements" || type === "2") {
      path = `/voice-announcements/${station.id}`; // lub /voice/ jeśli tak masz w routingu
    } else {
      // Fallback
      path = `/timetable/${station.id}`;
    }

    navigate(path);
  };

  // Filtruj stacje po wpisanym tekście
  const filteredStations = stations.filter((station) =>
    station.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) return <p style={{textAlign: "center", padding: "20px"}}>Ładowanie danych...</p>;

  return (
    <div style={styles.wrapper}>
      <h2 style={styles.header}>Wybierz stację</h2>

      {/* Kontener Wyszukiwarki */}
      <div style={styles.searchContainer}>
        <input
          type="text"
          placeholder="Wpisz nazwę stacji..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={styles.input}
          autoFocus
        />

        {/* Lista podpowiedzi (Google Style) - widoczna tylko gdy coś wpisano */}
        {searchTerm && (
          <div style={styles.suggestionsList}>
            {filteredStations.length > 0 ? (
              filteredStations.map((station) => (
                <div
                  key={station.id}
                  style={styles.suggestionItem}
                  onClick={() => handleStationSelect(station)}
                  onMouseEnter={(e) => (e.target.style.backgroundColor = "#f0f0f0")}
                  onMouseLeave={(e) => (e.target.style.backgroundColor = "white")}
                >
                  {station.name}
                </div>
              ))
            ) : (
              <div style={{ padding: "10px", color: "#888" }}>Nie znaleziono stacji</div>
            )}
          </div>
        )}
      </div>

      {/* Sekcja Ostatnio Wybranych */}
      {recentStations.length > 0 && !searchTerm && (
        <div style={styles.recentContainer}>
          <h3 style={styles.recentHeader}>🕒 Ostatnio wybrane:</h3>
          <div style={styles.recentGrid}>
            {recentStations.map((station) => (
              <button
                key={station.id}
                style={styles.recentBtn}
                onClick={() => handleStationSelect(station)}
                onMouseEnter={(e) => {
                    e.currentTarget.style.transform = "translateY(-2px)";
                    e.currentTarget.style.boxShadow = "0 4px 8px rgba(0,0,0,0.15)";
                }}
                onMouseLeave={(e) => {
                    e.currentTarget.style.transform = "none";
                    e.currentTarget.style.boxShadow = "0 2px 4px rgba(0,0,0,0.1)";
                }}
              >
                {station.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Opcjonalnie: Pełna lista stacji jeśli nic nie wpisano (jako siatka) */}
      {!searchTerm && (
        <div style={{ marginTop: "40px", textAlign: "left" }}>
            <p style={{color: "#666", fontSize: "14px", borderBottom: "1px solid #eee", paddingBottom: "5px"}}>Wszystkie stacje ({stations.length}):</p>
            <div style={{display: "flex", flexWrap: "wrap", gap: "10px"}}>
                {stations.map(station => (
                    <span 
                        key={station.id} 
                        onClick={() => handleStationSelect(station)}
                        style={{
                            cursor: "pointer", 
                            color: "#0055aa", 
                            fontSize: "14px",
                            padding: "4px 8px",
                            backgroundColor: "#f9f9f9",
                            borderRadius: "4px"
                        }}
                    >
                        {station.name}
                    </span>
                ))}
            </div>
        </div>
      )}
    </div>
  );
}

const styles = {
  wrapper: {
    textAlign: "center",
    padding: "40px 20px",
    maxWidth: "600px",
    margin: "0 auto",
  },
  header: {
    color: "#003366",
    marginBottom: "30px",
  },
  searchContainer: {
    position: "relative",
    marginBottom: "30px",
  },
  input: {
    width: "100%",
    padding: "15px 20px",
    borderRadius: "25px",
    border: "1px solid #ddd",
    fontSize: "18px",
    boxShadow: "0 2px 5px rgba(0,0,0,0.05)",
    outline: "none",
    boxSizing: "border-box", // Ważne przy width: 100%
  },
  suggestionsList: {
    position: "absolute",
    top: "100%",
    left: 0,
    right: 0,
    backgroundColor: "white",
    border: "1px solid #ddd",
    borderRadius: "0 0 10px 10px",
    boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
    zIndex: 10,
    maxHeight: "300px",
    overflowY: "auto",
    textAlign: "left",
    marginTop: "5px",
  },
  suggestionItem: {
    padding: "12px 20px",
    cursor: "pointer",
    borderBottom: "1px solid #f5f5f5",
    fontSize: "16px",
    color: "#333",
    transition: "background-color 0.2s",
  },
  recentContainer: {
    textAlign: "left",
    marginTop: "20px",
  },
  recentHeader: {
    fontSize: "16px",
    color: "#888",
    marginBottom: "10px",
    fontWeight: "normal",
  },
  recentGrid: {
    display: "flex",
    flexWrap: "wrap",
    gap: "10px",
  },
  recentBtn: {
    backgroundColor: "white",
    border: "1px solid #e0e0e0",
    borderRadius: "20px",
    padding: "8px 16px",
    cursor: "pointer",
    color: "#003366",
    fontWeight: "500",
    fontSize: "14px",
    boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
    transition: "all 0.2s ease",
  },
};