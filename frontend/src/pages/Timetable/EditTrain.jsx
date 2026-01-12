import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";

export default function EditTrain() {
  const { id } = useParams();
  const [stopDetails, setStopDetails] = useState(null);
  const [tracks, setTracks] = useState([]);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  // Pobierz dane postoju
  useEffect(() => {
    const fetchStopDetails = async () => {
      try {
        const res = await fetch(`/api/timetable/stop/${id}`);
        if (!res.ok) throw new Error("Nie udało się pobrać szczegółów postoju.");
        const data = await res.json();
        setStopDetails(data);
      } catch (err) {
        setError(err.message);
      }
    };
    fetchStopDetails();
  }, [id]);

  // Pobierz listę torów
  useEffect(() => {
    const fetchSelectData = async () => {
      try {
        const res = await fetch(`/api/timetable/tracks/${id}`);
        if (!res.ok) throw new Error("Błąd podczas pobierania listy torów.");
        const data = await res.json();
        setTracks(data);
      } catch (err) {
        console.error(err);
        setError("Nie udało się pobrać listy torów.");
      }
    };
    fetchSelectData();
  }, [id]);

  const handleChange = (field, value) => {
    setStopDetails((prev) => {
      const updated = { ...prev, [field]: value };

      // Sugestia opóźnienia odjazdu na podstawie opóźnienia przyjazdu
      if (field === "arrival_delay" && prev.arrival && prev.departure) {
        const arr = parseTime(prev.arrival);
        const dep = parseTime(prev.departure);

        if (arr && dep) {
          const minTravel = (dep - arr) / 60000;
          const ad = parseInt(value) || 0;
          const calculatedDepDelay = ad - minTravel;

          if (calculatedDepDelay >= 0) {
            updated.departure_delay = Math.max(updated.departure_delay || 0, calculatedDepDelay);
          }
        }
      }
      return updated;
    });
  };

  function parseTime(t) {
    if (!t) return null;
    const [h, m, s] = t.split(":").map(Number);
    return new Date(2000, 1, 1, h, m, s ?? 0);
  }

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Przygotowanie danych zgodnie z Twoją klasą edycyjną
    const payload = {
      arrival_delay: parseInt(stopDetails.arrival_delay) || 0,
      departure_delay: parseInt(stopDetails.departure_delay) || 0,
      track_id: stopDetails.bus ? null : (parseInt(stopDetails.track_id) || null),
      is_cancelled: !!stopDetails.is_cancelled,
      bus: !!stopDetails.bus,
    };

    try {
      const res = await fetch(`/api/timetable/edit/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        alert("Zmiany zapisane pomyślnie!");
        const stationId = stopDetails.station_id;
        navigate(sessionStorage.getItem("role_id") === "1" ? `/timetable/${stationId}` : `/timetable`);
      } else {
        const err = await res.json();
        alert(err.detail || "Błąd zapisu zmian");
      }
    } catch (error) {
      alert("Nie udało się połączyć z serwerem");
    }
  };

  if (error) return <p style={{ color: "red", padding: "20px" }}>{error}</p>;
  if (!stopDetails) return <p style={{ padding: "20px" }}>Wczytywanie danych pociągu...</p>;

  return (
    <div style={{ padding: 20 }}>
      <h2 style={{ color: "#2c3e50", marginBottom: "10px" }}>
        Edycja pociągu {stopDetails.train_type} {stopDetails.train_number}
      </h2>
      <div style={{ marginBottom: "20px", color: "#7f8c8d" }}>
        <p><strong>Przewoźnik:</strong> {stopDetails.carrier}</p>
        <p><strong>Kierunek:</strong> {stopDetails.final_station}</p>
        <p><strong>Stacja:</strong> {stopDetails.station}</p>
      </div>

      <form onSubmit={handleSubmit} style={formStyle}>
        
        {/* Sekcja: Odwołanie */}
        <div style={statusBoxStyle(stopDetails.is_cancelled, "#e74c3c")}>
          <label style={checkboxLabelStyle}>
            <input
              type="checkbox"
              style={checkboxStyle}
              checked={stopDetails.is_cancelled || false}
              onChange={(e) => handleChange("is_cancelled", e.target.checked)}
            />
            <strong style={{ color: stopDetails.is_cancelled ? "#c0392b" : "inherit" }}>
              {stopDetails.is_cancelled ? "POCIĄG ODWOŁANY" : "Odwołaj pociąg na tej stacji"}
            </strong>
          </label>
        </div>

        {/* Sekcja: Autobus zastępczy (ZKA) */}
        {!stopDetails.is_cancelled && (
          <div style={statusBoxStyle(stopDetails.bus, "#f39c12")}>
            <label style={checkboxLabelStyle}>
              <input
                type="checkbox"
                style={checkboxStyle}
                checked={stopDetails.bus || false}
                onChange={(e) => handleChange("bus", e.target.checked)}
              />
              <strong style={{ color: stopDetails.bus ? "#d35400" : "inherit" }}>
                {stopDetails.bus ? "ZASTĘPCZA KOMUNIKACJA AUTOBUSOWA" : "Uruchom autobus zastępczy (ZKA)"}
              </strong>
            </label>
          </div>
        )}

        {!stopDetails.is_cancelled && (
          <>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "15px" }}>
              {stopDetails.arrival &&(
              <div>
                <p style={labelStyle}>Planowy przyjazd: {stopDetails.arrival?.substring(0, 5)}</p>
                <input
                  type="number"
                  placeholder="Opóźnienie (min)"
                  value={stopDetails.arrival_delay || ""}
                  onChange={(e) => handleChange("arrival_delay", e.target.value)}
                  style={inputStyle}
                />
              </div>
              )}
              {stopDetails.departure &&(
              <div>
                <p style={labelStyle}>Planowy odjazd: {stopDetails.departure?.substring(0, 5)}</p>
                <input
                  type="number"
                  placeholder="Opóźnienie (min)"
                  value={stopDetails.departure_delay || ""}
                  onChange={(e) => handleChange("departure_delay", e.target.value)}
                  style={inputStyle}
                />
              </div>
              )}
            </div>

            {!stopDetails.bus && (
              <div>
                <p style={labelStyle}>Peron / Tor</p>
                <select
                  value={stopDetails.track_id || ""}
                  onChange={(e) => handleChange("track_id", e.target.value)}
                  style={inputStyle}
                >
                  <option value="">Wybierz peron/tor</option>
                  {tracks.map((t) => (
                    <option key={t.id} value={t.id}>
                      Peron {t.platform_number}, Tor {t.number} {t.available_to ? `(wolny do ${t.available_to})` : ''}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </>
        )}

        <button type="submit" style={buttonStyle}>
          {stopDetails.is_cancelled ? "Potwierdź odwołanie" : "Zapisz zmiany"}
        </button>
      </form>
    </div>
  );
}

// --- Style ---
const formStyle = {
  padding: "20px",
  maxWidth: "450px",
  margin: "0 auto",
  display: "flex",
  flexDirection: "column",
  gap: "15px",
  backgroundColor: "#fff",
  borderRadius: "10px",
  boxShadow: "0 4px 6px rgba(0,0,0,0.1)"
};

const inputStyle = {
  width: "100%",
  padding: "10px",
  borderRadius: "5px",
  border: "1px solid #ccc",
  fontSize: "14px",
  boxSizing: "border-box"
};

const labelStyle = {
  fontSize: "13px",
  fontWeight: "bold",
  marginBottom: "5px",
  color: "#34495e"
};

const statusBoxStyle = (isActive, color) => ({
  padding: "15px",
  borderRadius: "8px",
  border: isActive ? `2px solid ${color}` : "1px solid #ddd",
  backgroundColor: isActive ? `${color}10` : "#f9f9f9",
  transition: "all 0.2s ease"
});

const checkboxLabelStyle = {
  cursor: "pointer",
  display: "flex",
  alignItems: "center",
  gap: "12px"
};

const checkboxStyle = {
  width: "20px",
  height: "20px",
  cursor: "pointer"
};

const buttonStyle = {
  backgroundColor: "#2c3e50",
  color: "white",
  border: "none",
  padding: "14px",
  borderRadius: "5px",
  cursor: "pointer",
  fontWeight: "bold",
  fontSize: "16px",
  marginTop: "10px"
};