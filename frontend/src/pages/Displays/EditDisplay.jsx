import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";

export default function EditDisplay() {
  const { displayId } = useParams();
  const navigate = useNavigate();

  const [display, setDisplay] = useState(null);
  const [platforms, setPlatforms] = useState([]);
  const [tracks, setTracks] = useState([]);
  const [error, setError] = useState("");

  const [formData, setFormData] = useState({
    alias: "",
    type_id: "",
    platform_id: "",
    track_id: "",
    main_color: "",
    background_color: "",
    font: "",
    theme: 0,
    intermediates_number: null,
  });

  const fonts = ["Segoe UI", "Roboto", "Arial", "Helvetica", "Verdana", "Inter", "Tahoma"];

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const showPlatform = formData.type_id === 2 || formData.type_id === 3;
  const showTrack = formData.type_id === 1;
  const showIntermediates = formData.type_id !== 2 && formData.type_id !== 6;

  useEffect(() => {
    const loadDisplay = async () => {
      try {
        const res = await fetch(`/api/displays/display/${displayId}`);
        if (!res.ok) throw new Error("Nie udało się pobrać danych wyświetlacza.");

        const data = await res.json();
        setDisplay(data);

        setFormData({
          alias: data.alias || "",
          type_id: data.type_id,
          platform_id: data.platform_id || "",
          track_id: data.track_id || "",
          main_color: data.main_color || "00e676",
          background_color: data.background_color || "020203",
          font: data.font || "Segoe UI",
          theme: data.theme ? 1 : 0,
          intermediates_number: data.intermediates_number,
        });

        // Pobieranie list peronów/torów dla stacji, do której przypisany jest wyświetlacz
        if (data.type_id === 1) {
          const tr = await fetch(`/api/displays/tracks/${data.station_id}`);
          setTracks(await tr.json());
        } else if (data.type_id === 2 || data.type_id === 3) {
          const pl = await fetch(`/api/displays/platforms/${data.station_id}`);
          setPlatforms(await pl.json());
        }
      } catch (err) {
        setError(err.message);
      }
    };

    loadDisplay();
  }, [displayId]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Przygotowanie payloadu zgodnego z klasą DisplayUpdate (analogiczną do NewDisplay)
    const payload = {
      station_id: parseInt(display.station_id),
      alias: formData.alias.trim() || null,
      platform_id: (formData.type_id === 2 || formData.type_id === 3) && formData.platform_id 
                   ? parseInt(formData.platform_id) : null,
      track_id: formData.type_id === 1 && formData.track_id 
                ? parseInt(formData.track_id) : null,
      type_id: parseInt(formData.type_id),
      font: formData.font,
      intermediates_number: showIntermediates && formData.intermediates_number !== null 
                            ? parseInt(formData.intermediates_number) : null,
      main_color: formData.main_color.replace("#", ""),
      background_color: formData.background_color.replace("#", ""),
      theme: Boolean(formData.theme), // Konwersja na bool
    };

    try {
      const res = await fetch(`/api/displays/edit/${displayId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Błąd podczas zapisu zmian.");
      }

      alert("Zapisano zmiany pomyślnie.");
      navigate(-1);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm("Czy na pewno chcesz usunąć ten wyświetlacz?")) return;

    try {
      const res = await fetch(`/api/displays/delete/${displayId}`, {
        method: "DELETE",
      });

      if (!res.ok) throw new Error("Nie udało się usunąć wyświetlacza.");

      alert("Wyświetlacz został usunięty.");
      navigate(-1);
    } catch (err) {
      alert(err.message);
    }
  };

  if (error) return <p style={{ color: "red", padding: "20px" }}>{error}</p>;
  if (!display) return <p style={{ padding: "20px" }}>Wczytywanie danych...</p>;

  return (
    <div style={containerStyle}>
      <h2 style={{ marginBottom: "20px", color: "#2c3e50" }}>Edytuj wyświetlacz #{displayId}</h2>

      <form onSubmit={handleSubmit} style={formStyle}>
        <label style={labelStyle}>
          Alias wyświetlacza:
          <input
            style={inputStyle}
            type="text"
            placeholder="np. Peronowy Główny"
            value={formData.alias}
            onChange={(e) => handleChange("alias", e.target.value)}
          />
        </label>

        {showPlatform && (
          <label style={labelStyle}>
            Numer peronu:
            <select
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
            />
          </label>

          <label style={labelStyle}>
            Kolor tła:
            <input
              style={{ ...inputStyle, padding: "2px", height: "38px" }}
              type="color"
              value={"#" + formData.background_color}
              onChange={(e) => handleChange("background_color", e.target.value.replace("#", ""))}
            />
          </label>
        </div>

        <label style={labelStyle}>
          Czcionka:
          <select
            style={inputStyle}
            value={formData.font}
            onChange={(e) => handleChange("font", e.target.value)}
          >
            {fonts.map((f) => (
              <option key={f} value={f}>{f}</option>
            ))}
          </select>
        </label>

        <label style={labelStyle}>
          Motyw kolorystyczny:
          <select
            style={inputStyle}
            value={formData.theme}
            onChange={(e) => handleChange("theme", Number(e.target.value))}
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

        <div style={{ display: "flex", gap: "10px", marginTop: "15px" }}>
          <button type="submit" style={buttonStyle}>Zapisz zmiany</button>
          <button type="button" onClick={handleDelete} style={deleteButtonStyle}>Usuń</button>
        </div>
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
  flex: 1,
  backgroundColor: "#2c3e50",
  color: "white",
  border: "none",
  padding: "12px",
  borderRadius: "6px",
  cursor: "pointer",
  fontWeight: "bold",
  fontSize: "16px",
  transition: "background-color 0.2s ease",
};

const deleteButtonStyle = {
  backgroundColor: "#e74c3c",
  color: "white",
  border: "none",
  padding: "12px",
  borderRadius: "6px",
  cursor: "pointer",
  fontWeight: "bold",
  fontSize: "16px",
  transition: "background-color 0.2s ease",
};