import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Mic, Settings, ExternalLink } from "lucide-react";
import { useStationData } from "../hooks/useStationData";

export default function VoiceAnnouncements() {
  const { selectedStationId } = useParams();
  const navigate = useNavigate();

  const { stationId, stationName, loading, error, roleId, setLoading, setError } = useStationData();

  const openController = () => {
    // Otwiera plik HTML w nowym oknie typu popup
    window.open(
      `/voice-controller.html?station_id=${stationId}`,
      "VoiceController",
      "width=600,height=800,menubar=no,toolbar=no,location=no,status=no"
    );
  };

  return (
    <div style={{ padding: "40px", maxWidth: "800px", margin: "0 auto" }}>
      <div style={{ 
        backgroundColor: "white", 
        padding: "30px", 
        borderRadius: "10px", 
        boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
        textAlign: "center"
      }}>
        <Mic size={64} color="#003366" style={{ marginBottom: "20px" }} />
        <h2 style={{ color: "#003366", marginBottom: "10px" }}>
          Automatyczne zapowiedzi głosowe
        </h2>
        <h3 style={{ color: "#666", marginBottom: "30px", fontWeight: "normal" }}>
          Stacja: <b>{stationName || "Ładowanie..."}</b>
        </h3>

        <div style={{ marginBottom: "30px", fontSize: "14px", color: "#555", textAlign: "left", lineHeight: "1.6" }}>
          <p>Ten moduł pozwala na automatyczne generowanie komunikatów dworcowych w oparciu o Eleven Labs.</p>
          <p><strong>Zasada działania:</strong></p>
          <ul>
            <li>Kliknij przycisk poniżej, aby otworzyć <strong>Kontroler Głosowy</strong> w nowym oknie.</li>
            <li>Kontroler musi pozostać otwarty, aby komunikaty były generowane.</li>
            <li>System automatycznie wygłosi zapowiedzi wjazdu, postoju i odjazdu.</li>
          </ul>
        </div>

        <button
          onClick={openController}
          style={{
            backgroundColor: "#0055aa",
            color: "white",
            border: "none",
            padding: "15px 30px",
            borderRadius: "8px",
            fontSize: "18px",
            cursor: "pointer",
            display: "inline-flex",
            alignItems: "center",
            gap: "10px",
            boxShadow: "0 4px 6px rgba(0,85,170,0.3)"
          }}
        >
          <ExternalLink size={20} />
          Aktywuj komunikaty na stacji
        </button>
        {sessionStorage.getItem("role_id") !== "3" && (
        <div style={{ marginTop: "20px" }}>
            <button
              onClick = {() => navigate(`/voice-settings/${stationId}`)}
              style={{ background: "none", border: "none", color: "#888", display: "inline-flex", alignItems: "center", gap: "5px" }}>
                <Settings size={16} /> Ustawienia parametrów
            </button>
        </div>
        )}
      </div>
    </div>
  );
}