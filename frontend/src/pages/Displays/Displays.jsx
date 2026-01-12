import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useStationData } from "../../hooks/useStationData";

export default function Displays() {
  const [displays, setDisplays] = useState([]);
  const [hoveredId, setHoveredId] = useState(null);
  
  const navigate = useNavigate();

  const { stationId, stationName, loading, error, roleId, setLoading, setError } = useStationData();

  const displayViewStrategies = {
    1: (display) => ({
      address: `/edge-display-view.html?display_id=${display.id}`,
      width: 800,
      height: 450
    }),

    2: (display) => ({
      address: `/entrance-platform-display-view.html?display_id=${display.id}`,
      width: 800,
      height: 450
    }),

    3: (display) => ({
      address: `/platform-display-view.html?display_id=${display.id}`,
      width: 800,
      height: 450
    }),

    4: (display) => ({
      address: `/station-display-view.html?display_id=${display.id}&view=departures&orientation=vertical`,
      width: 459,
      height: 816
    }),

    5: (display) => ({
      address: `/station-display-view.html?display_id=${display.id}&view=arrivals&orientation=vertical`,
      width: 459,
      height: 816
    }),

    6: (display) => ({
      address: `/infokiosk-view.html?display_id=${display.id}`,
      width: 459,
      height: 816
    }),

    7: (display) => ({
      address: `/station-display-view.html?display_id=${display.id}&view=departures&orientation=horizontal`,
      width: 1600,
      height: 900
    }),

    8: (display) => ({
      address: `/station-display-view.html?display_id=${display.id}&view=arrivals&orientation=horizontal`,
      width: 1600,
      height: 900
    })
  };


  const handleView = (display, isApply) => {
    const strategy = displayViewStrategies[display.type_id];

    if (!strategy) {
      console.error("Nieznany typ wyświetlacza:", display.type_id);
      return;
    }

    const { address, width, height } = strategy(display);

    window.open(
      address,
      "_blank",
      `width=${width},height=${height},menubar=no,toolbar=no,location=no,status=no`
    );

    if (isApply) {
      navigate(`/`);
      sessionStorage.removeItem("role_id");
      sessionStorage.removeItem("admin_id");
      setIsLoggedIn(false);
    }
  };


  useEffect(() => {
    if (!stationId) return;
    setLoading(true);
    setError("");

    fetch(`/api/displays/${stationId}`)
      .then((res) => {
        if (!res.ok) throw new Error("Nie udało się pobrać wyświetlaczy.");
        return res.json();
      })
      .then((data) => setDisplays(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [stationId]);

  if (error) return <p style={{ color: "red" }}>{error}</p>;

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2>Wyświetlacze na stacji {`${stationName}`}</h2>
        {sessionStorage.getItem("role_id") !== "3" && (
        <button
          onClick={() => navigate(`/add-display/${stationId}`)}
          style={styles.addButton}
        >
          ➕ Dodaj nowy wyświetlacz
        </button>
        )}
      </div>

      {loading && <p>⏳ Wczytywanie danych...</p>}
      {error && <p style={{ color: "red" }}>❌ {error}</p>}

      {!loading && displays.length === 0 && !error && (
        <p>Brak wyświetlaczy.</p>
      )}

      <div style={styles.grid}>
        {displays.map((display) => (
          <div
            key={display.id}
            style={styles.card}
            onMouseEnter={() => setHoveredId(display.id)}
            onMouseLeave={() => setHoveredId(null)}
            onClick={() => setHoveredId(display.id)} // dla dotyku
          >
            <img
              src={`/displays/${display.image_url}` || "/placeholder-display.jpg"}
              alt={display.name}
              style={styles.image}
            />
            <div style={styles.info}>
              <h3 style={styles.title}>{display.name}</h3>
              {display.alias ?? <h2 style={styles.title}>{display.alias}</h2>}
              <p style={styles.location}>{display.location}</p>
            </div>
            {hoveredId === display.id && (
              <div style={styles.overlay}>
                <button
                  style={styles.actionButton}
                  onClick={() => handleView(display, 1)}
                >
                  Zastosuj
                </button>
                <button
                  style={styles.actionButton}
                  onClick={() => handleView(display, 0)}
                >
                  Podgląd
                </button>
                {sessionStorage.getItem("role_id") !== "3" && (
                  <button
                    style={styles.actionButton}
                    onClick={() => navigate(`/edit-display/${display.id}`)}
                  >
                    Edytuj
                  </button>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

const styles = {
  container: {
    padding: "40px",
    maxWidth: "1200px",
    margin: "0 auto",
    fontFamily: "Arial, sans-serif",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "20px",
  },
  addButton: {
    backgroundColor: "#2ecc71",
    color: "white",
    border: "none",
    padding: "10px 20px",
    borderRadius: "8px",
    cursor: "pointer",
    fontWeight: "bold",
    fontSize: "15px",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
    gap: "20px",
  },
  card: {
    position: "relative",
    backgroundColor: "#f8f9fa",
    borderRadius: "12px",
    boxShadow: "0 3px 8px rgba(0,0,0,0.15)",
    overflow: "hidden",
    transition: "transform 0.2s ease, box-shadow 0.2s ease",
  },
  image: {
    width: "100%",
    height: "160px",
    objectFit: "cover",
  },
  info: {
    padding: "10px 15px",
  },
  title: {
    margin: "5px 0",
    fontSize: "18px",
    color: "#2c3e50",
  },
  location: {
    color: "#7f8c8d",
    fontSize: "14px",
  },
  overlay: {
    position: "absolute",
    top: "0",
    left: "0",
    width: "100%",
    height: "100%",
    background: "rgba(0,0,0,0.6)",
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    gap: "10px",
    transition: "opacity 0.2s ease",
  },
  actionButton: {
    backgroundColor: "#3498db",
    border: "none",
    color: "white",
    padding: "8px 16px",
    borderRadius: "6px",
    cursor: "pointer",
    fontWeight: "bold",
  },
};
