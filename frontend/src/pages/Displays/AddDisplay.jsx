import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";

export default function AddDisplay() {
  const { station_id } = useParams();
  const navigate = useNavigate();

  const [displayTypes, setDisplayTypes] = useState([]);
  const [platforms, setPlatforms] = useState([]);
  const [tracks, setTracks] = useState([]);

  const [formData, setFormData] = useState({
    alias: "",
    type_id: "",
    platform_id: "",
    track_id: "",
    main_color: "00e676",
    background_color: "020203",
    font: "Segoe UI",
    theme: 0, // 0 dla ciemnego, 1 dla jasnego (konwertowane na bool)
    intermediates_number: 5,
  });

  const [error, setError] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [typesRes, platformsRes, tracksRes] = await Promise.all([
          fetch("/api/displays/types"),
          fetch(`/api/displays/platforms/${station_id}`),
          fetch(`/api/displays/tracks/${station_id}`),
        ]);

        if (!typesRes.ok || !platformsRes.ok || !tracksRes.ok) {
          throw new Error("Nie udało się pobrać danych pomocniczych.");
        }

        setDisplayTypes(await typesRes.json());
        setPlatforms(await platformsRes.json());
        setTracks(await tracksRes.json());
      } catch (err) {
        setError(err.message);
      }
    };

    fetchData();
  }, [station_id]);

  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Przygotowanie payloadu zgodnego z klasą NewDisplay (Pydantic)
    const payload = {
      station_id: parseInt(station_id),
      alias: formData.alias.trim() || null,
      platform_id: formData.platform_id ? parseInt(formData.platform_id) : null,
      track_id: formData.track_id ? parseInt(formData.track_id) : null,
      type_id: parseInt(formData.type_id),
      font: formData.font,
      intermediates_number: showIntermediates && formData.intermediates_number !== null ? parseInt(formData.intermediates_number) : null,
      main_color: formData.main_color.replace("#", ""),
      background_color: formData.background_color.replace("#", ""),
      theme: Boolean(formData.theme), // Konwersja 0/1 na true/false dla typu bool
    };

    try {
      const res = await fetch("/api/displays/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Błąd dodawania wyświetlacza.");
      }

      alert("Wyświetlacz został dodany pomyślnie!");
      navigate(`/displays/${station_id}`);
    } catch (err) {
      alert(err.message);
    }
  };

  const showPlatform = formData.type_id === "2" || formData.type_id === "3";
  const showTrack = formData.type_id === "1";
  const showIntermediates = formData.type_id !== 2 && formData.type_id !== 6;

  if (error) return <p style={{ color: "red", padding: "20px" }}>{error}</p>;

  return (
    <div style={containerStyle}>
      <h2 style={{ marginBottom: "20px", color: "#2c3e50" }}>Dodaj nowy wyświetlacz</h2>
      <form onSubmit={handleSubmit} style={formStyle}>
        <label style={labelStyle}>
          Alias wyświetlacza:
          <input
            style={inputStyle}
            type="text"
            placeholder="np. Peronowy Zachodni"
            value={formData.alias}
            onChange={(e) => handleChange("alias", e.target.value)}
          />
        </label>
        
        <label style={labelStyle}>
          Typ wyświetlacza:
          <select
            required
            style={inputStyle}
            value={formData.type_id}
            onChange={(e) => handleChange("type_id", e.target.value)}
          >
            <option value="">-- Wybierz typ --</option>
            {displayTypes.map((t) => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
        </label>

        {showPlatform && (
          <label style={labelStyle}>
            Numer peronu:
            <select
              required
              style={inputStyle}
              value={formData.platform_id}
              onChange={(e) => handleChange("platform_id", e.target.value)}
            >
              <option value="">-- Wybierz peron --</option>
              {platforms.map((p) => (
                <option key={p.id} value={p.id}>{p.number}</option>
              ))}
            </select>
          </label>
        )}

        {showTrack && (
          <label style={labelStyle}>
            Numer toru:
            <select
              required
              style={inputStyle}
              value={formData.track_id}
              onChange={(e) => handleChange("track_id", e.target.value)}
            >
              <option value="">-- Wybierz tor --</option>
              {tracks.map((t) => (
                <option key={t.id} value={t.id}>{t.number}</option>
              ))}
            </select>
          </label>
        )}

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
          <label style={labelStyle}>
            Kolor dominujący:
            <input
              style={{ ...inputStyle, padding: "2px", height: "38px" }}
              type="color"
              value={"#" + formData.main_color}
              onChange={(e) => handleChange("main_color", e.target.value.replace("#", ""))}
              required
            />
          </label>

          <label style={labelStyle}>
            Kolor tła:
            <input
              style={{ ...inputStyle, padding: "2px", height: "38px" }}
              type="color"
              value={"#" + formData.background_color}
              onChange={(e) => handleChange("background_color", e.target.value.replace("#", ""))}
              required
            />
          </label>
        </div>

        <label style={labelStyle}>
          Czcionka:
          <select
            style={inputStyle}
            value={formData.font}
            onChange={(e) => handleChange("font", e.target.value)}
            required
          >
            <option value="Segoe UI">Segoe UI</option>
            <option value="Roboto">Roboto</option>
            <option value="Arial">Arial</option>
            <option value="Helvetica">Helvetica</option>
            <option value="Verdana">Verdana</option>
            <option value="Inter">Inter</option>
            <option value="Tahoma">Tahoma</option>
          </select>
        </label>

        <label style={labelStyle}>
          Motyw kolorystyczny:
          <select
            style={inputStyle}
            value={formData.theme}
            onChange={(e) => handleChange("theme", Number(e.target.value))}
            required
          >
            <option value={0}>Ciemny (Dark)</option>
            <option value={1}>Jasny (Light)</option>
          </select>
        </label>

        {showIntermediates && (
          <div style={{ marginBottom: "5px" }}>
            <label style={labelStyle}>Liczba stacji pośrednich:</label>
            <div style={{ display: "flex", alignItems: "center", gap: "15px", marginTop: "5px" }}>
              <input
                type="number"
                min={0}
                placeholder={formData.intermediates_number === null ? "Wszystkie" : ""}
                value={formData.intermediates_number === null ? "" : formData.intermediates_number}
                disabled={formData.intermediates_number === null}
                onChange={(e) => handleChange("intermediates_number", e.target.value === "" ? null : Number(e.target.value))}
                style={{
                  ...inputStyle,
                  width: "100px",
                  backgroundColor: formData.intermediates_number === null ? "#f1f2f6" : "white"
                }}
              />
              <label style={{ display: "flex", alignItems: "center", gap: "6px", cursor: "pointer", fontSize: "14px" }}>
                <input
                  type="checkbox"
                  checked={formData.intermediates_number === null}
                  onChange={(e) => handleChange("intermediates_number", e.target.checked ? null : 5)}
                />
                Pokaż wszystkie
              </label>
            </div>
          </div>
        )}

        <button type="submit" style={buttonStyle}>
          Dodaj wyświetlacz
        </button>
      </form>
    </div>
  );
}

// 🎨 Style inline
const containerStyle = {
  maxWidth: "500px",
  margin: "40px auto",
  backgroundColor: "#ffffff",
  padding: "30px",
  borderRadius: "12px",
  boxShadow: "0 4px 15px rgba(0,0,0,0.1)",
};

const formStyle = {
  display: "flex",
  flexDirection: "column",
  gap: "15px",
};

const labelStyle = {
  display: "flex",
  flexDirection: "column",
  gap: "5px",
  fontSize: "14px",
  fontWeight: "600",
  color: "#34495e",
};

const inputStyle = {
  padding: "10px",
  borderRadius: "6px",
  border: "1px solid #dcdde1",
  fontSize: "15px",
  outline: "none",
};

const buttonStyle = {
  backgroundColor: "#2c3e50",
  color: "white",
  border: "none",
  padding: "12px",
  borderRadius: "6px",
  cursor: "pointer",
  fontWeight: "bold",
  fontSize: "16px",
  marginTop: "10px",
  transition: "background-color 0.2s ease",
};