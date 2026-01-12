import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useStationData } from "../../hooks/useStationData";

export default function TimeTable() {
  const [departures, setDepartures] = useState([]);
  const [arrivals, setArrivals] = useState([]);
  const [activeTab, setActiveTab] = useState("departures"); // "departures" | "arrivals"
  
  const navigate = useNavigate();
  
  const { stationId, stationName, loading, error, roleId, setLoading, setError } = useStationData();

  // 🔹 Pobieranie danych w zależności od aktywnej zakładki
  useEffect(() => {
    if (!stationId) return;
    
    setLoading(true);
    setError("");

    const endpoint = activeTab === "departures" 
      ? `/api/timetable/departures/${stationId}`
      : `/api/timetable/arrivals/${stationId}`;

    fetch(endpoint)
      .then((res) => {
        if (!res.ok) throw new Error("Nie udało się pobrać rozkładu jazdy.");
        return res.json();
      })
      .then((data) => {
        if (activeTab === "departures") {
          setDepartures(data);
        } else {
          setArrivals(data);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [stationId, activeTab]);

  // Helper do wyświetlania danych w tabeli
  const dataToDisplay = activeTab === "departures" ? departures : arrivals;

  return (
    <div style={styles.wrapper}>
      <h2>🚉 Rozkład {stationName ? `– ${stationName}` : ""}</h2>

      {/* Zakładki */}
      <div style={styles.tabsContainer}>
        <button 
          style={activeTab === "departures" ? styles.activeTab : styles.tab} 
          onClick={() => setActiveTab("departures")}
        >
          Odjazdy
        </button>
        <button 
          style={activeTab === "arrivals" ? styles.activeTab : styles.tab} 
          onClick={() => setActiveTab("arrivals")}
        >
          Przyjazdy
        </button>
      </div>

      {loading && <p>⏳ Wczytywanie danych...</p>}
      {error && <p style={{ color: "red" }}>❌ {error}</p>}

      {!loading && dataToDisplay.length === 0 && !error && (
        <p>Brak zaplanowanych {activeTab === "departures" ? "odjazdów" : "przyjazdów"}.</p>
      )}

      {!loading && dataToDisplay.length > 0 && (
        <div className="table-wrapper">
          <table style={styles.table}>
            <thead>
              <tr>
                <th>Godzina</th>
                <th>{activeTab === "departures" ? "Stacja docelowa" : "Stacja początkowa"}</th>
                <th>Typ i numer pociągu</th>
                <th>Peron/Tor</th>
                <th>Opóźnienie</th>
                <th>Akcje</th>
              </tr>
            </thead>
            <tbody>
              {dataToDisplay.map((train) => (
                <tr key={train.id} style={{ textAlign: "center" }}>
                  {/* Rozróżnienie pola czasu w zależności od typu danych */}
                  <td>
                    {activeTab === "departures" ? train.departure_time : train.arrival_time}
                  </td>
                  
                  <td>{train.station}</td>
                  
                  <td>{train.train_type} {train.train_number}</td>
                  
                  {/* Obsługa pogrubienia dla zmienionego peronu (original === false) */}
                  {train.bus === true ? <td><b>BUS</b></td> : train.original === false ? 
                    <td><b>{train.platform}/{train.track}</b></td> : 
                    <td>{train.platform}/{train.track}</td>
                  }
                  
                  <td>
                    {train.delay ? `${train.delay}` + (train.delay !== "Odwołany" ? ` min` : "") : "—"}
                  </td>
                  
                  <td>
                    <button
                      style={styles.detailsBtn}
                      onClick={() => navigate(`/train-details/${train.id}`)}
                    >
                      Szczegóły
                    </button>{" "}
                    <button
                      style={styles.detailsBtn}
                      onClick={() => navigate(`/edit-train/${train.id}`)}
                    >
                      Edytuj
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

const styles = {
  wrapper: {
    padding: "20px",
    backgroundColor: "white",
    borderRadius: "8px",
    boxShadow: "0 2px 6px rgba(0,0,0,0.1)",
  },
  tabsContainer: {
    display: "flex",
    gap: "10px",
    marginBottom: "15px",
    borderBottom: "2px solid #eee",
    paddingBottom: "10px",
  },
  tab: {
    padding: "10px 20px",
    cursor: "pointer",
    backgroundColor: "#f0f0f0",
    border: "none",
    borderRadius: "4px",
    fontSize: "16px",
    color: "#333",
  },
  activeTab: {
    padding: "10px 20px",
    cursor: "pointer",
    backgroundColor: "#0055aa",
    color: "white",
    border: "none",
    borderRadius: "4px",
    fontSize: "16px",
    fontWeight: "bold",
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
    marginTop: "15px",
    border: "1px solid #ccc",
  },
  detailsBtn: {
    backgroundColor: "#0055aa",
    color: "white",
    border: "none",
    borderRadius: "4px",
    padding: "6px 10px",
    cursor: "pointer",
  },
};