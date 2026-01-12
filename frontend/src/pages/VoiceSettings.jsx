import React, { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";

export default function VoiceSettings() {
  const { stationId } = useParams();
  const navigate = useNavigate();
  
  // Wartości są w skali 0-100 (zgodnie z bazą danych)
  const [stabilityRaw, setStabilityRaw] = useState(90); 
  const [similarityRaw, setSimilarityRaw] = useState(80);
  const [styleRaw, setStyleRaw] = useState(0);
  const [stationName, setStationName] = useState("");

  // ID głosu (string) - np. "ErXwobaYiN019PkySvjV" (Antoni)
  const [voiceId, setVoiceId] = useState(""); 
  
  const [models, setModels] = useState([]); // Lista dostępnych głosów (do selektora)
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // 🔹 Funkcja pomocnicza do pobierania list głosów
  const fetchVoiceModels = useCallback(async () => {
    try {
      const voiceRes = await fetch("/api/voice-models"); 
      if (!voiceRes.ok)
        throw new Error("Błąd podczas pobierania listy głosów.");
      const voiceData = await voiceRes.json();
      setModels(voiceData);
      return voiceData;
    } catch (err) {
      console.error(err);
      setError("Nie udało się pobrać listy modeli głosowych.");
      return [];
    }
  }, []);


  // 🔹 1. Pobieranie bieżących ustawień stacji
  useEffect(() => {
    if (!stationId) return;
    setLoading(true);
    
    // Zmieniono, aby używać wartości 0-100 bezpośrednio
    fetch(`/api/voice-settings/${stationId}`)
      .then((res) => {
        if (!res.ok) throw new Error("Nie udało się pobrać ustawień głosu.");
        return res.json();
      })
      .then((data) => {
          // Ładowanie wartości RAW (0-100) z bazy
          setStabilityRaw(data.stability || 90);
          setSimilarityRaw(data.similarity || 80);
          setStyleRaw(data.style || 0);
          
          setVoiceId(data.model_id || "JBFqnCBsd6RMkjVDRZzb");
          setStationName(data.station_name || "");
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));

    // Ładowanie listy modeli i ustawienie domyślnego, jeśli brakuje ID
    fetchVoiceModels().then(voiceData => {
      if (!voiceId && voiceData.length > 0) {
        setVoiceId(voiceData[0].id);
      }
    });
  }, [stationId, fetchVoiceModels]);


  // 🔹 3. Funkcja zapisu
  const handleSave = () => {
    setLoading(true);
    setError("");
    
    // Wysyłamy wartości RAW (0-100)
    const apiData = {
        stability: stabilityRaw,
        similarity: similarityRaw,
        style: styleRaw,
        model_id: voiceId, // String
    };
    
    if (!voiceId) {
        setError("Wybierz model głosowy.");
        setLoading(false);
        return;
    }

    fetch(`/api/edit-voice/${stationId}`, {
        method: "PUT", // Zmieniono na PUT, aby być zgodne z CRUD (edycja)
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(apiData),
    })
    .then((res) => {
        if (!res.ok) throw new Error("Nie udało się zapisać ustawień głosu.");
        // Sprawdź czy odpowiedź jest JSON, jeśli nie, zwróć pusty obiekt lub tekst
        return res.text().then(text => text ? JSON.parse(text) : {});
    })
    .then(() => {
        alert("Ustawienia głosu zostały zapisane.");
        navigate(-1);
    })
    .catch((err) => setError(err.message))
    .finally(() => setLoading(false));
  };

  // Używamy konwersji tylko do wyświetlania w tooltipie dla Eleven Labs (0.00)
  const displayAsApi = (value) => (value / 100).toFixed(2);

  return (
    <div style={{ padding: "40px", maxWidth: "600px", margin: "0 auto", backgroundColor: "white", borderRadius: "8px", boxShadow: "0 2px 8px rgba(0,0,0,0.1)" }}>
      <h2>Ustawienia głosu dla stacji {stationName}</h2>
      {loading && <p>Ładowanie ustawień...</p>}
      {error && <div style={{ color: "red", marginBottom: "20px" }}>{error}</div>}

      <div style={{ marginBottom: "20px" }}>
        <label style={{display: "block", marginBottom: "5px", fontWeight: "bold"}}>Model głosowy:</label>
        <select 
          style={{ width: "100%", padding: "8px", fontSize: "16px", borderRadius: "4px" }}
          value={voiceId || ""}
          onChange={(e) => setVoiceId(e.target.value)}
          disabled={loading || models.length === 0}
        >
          <option value="" disabled>-- Wybierz głos (np. George) --</option>
          {models.map((m) => (
            <option key={m.id} value={m.id}>
              {m.name}
            </option>
          ))}
        </select>
      </div>

      <div style={{ marginBottom: "20px" }}>
          <label style={{display: "block", marginBottom: "5px", fontWeight: "bold"}}>Stabilność (Stability): {stabilityRaw} ({displayAsApi(stabilityRaw)})</label>
          <p style={{fontSize: "0.8em", color: "#666", margin: 0}}>Im wyżej, tym bardziej monotonny i profesjonalny głos (zalecane na dworzec: 70-90).</p>
          <input
              type="range"
              min="0"
              max="100"
              value={stabilityRaw}
              onChange={(e) => setStabilityRaw(parseInt(e.target.value))}
              style={{ width: "100%", padding: "0", marginTop: "10px" }}
              disabled={loading}
          />
      </div>

      <div style={{ marginBottom: "20px" }}>
          <label style={{display: "block", marginBottom: "5px", fontWeight: "bold"}}>Podobieństwo (Similarity Boost): {similarityRaw} ({displayAsApi(similarityRaw)})</label>
          <p style={{fontSize: "0.8em", color: "#666", margin: 0}}>Wysokie wartości poprawiają jakość głosu w syntezie.</p>
          <input
              type="range"
              min="0"
              max="100"
              value={similarityRaw}
              onChange={(e) => setSimilarityRaw(parseInt(e.target.value))}
              style={{ width: "100%", padding: "0", marginTop: "10px" }}
              disabled={loading}
          />
      </div>
      
      <div style={{ marginBottom: "20px" }}>
          <label style={{display: "block", marginBottom: "5px", fontWeight: "bold"}}>Styl (Style): {styleRaw} ({displayAsApi(styleRaw)})</label>
          <p style={{fontSize: "0.8em", color: "#666", margin: 0}}>Kontroluje ekspresję i emocje. Zalecane 0 dla komunikatów publicznych.</p>
          <input 
              type="range"
              min="0"
              max="100"
              value={styleRaw}
              onChange={(e) => setStyleRaw(parseInt(e.target.value))}
              style={{ width: "100%", padding: "0", marginTop: "10px" }}
              disabled={loading}
          />
      </div>
      
      <button
          onClick={handleSave}
          style={{
              backgroundColor: "#0055aa",
              color: "white",
              border: "none",
              padding: "12px 24px",
              borderRadius: "8px",
              fontSize: "16px",
              cursor: "pointer",
          }}
          disabled={loading}
      >
          {loading ? "Zapisywanie..." : "Zapisz Ustawienia"}
      </button>
    </div>
  );
}