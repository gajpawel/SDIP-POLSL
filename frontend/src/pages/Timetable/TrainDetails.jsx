import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";

export default function TrainDetails() {
    const { id } = useParams();
    const [trainDetails, setTrainDetails] = useState(null);
    const [error, setError] = useState("");
    const navigate = useNavigate();

    useEffect(() => {
        const fetchTrainDetails = async () => {
            try {
                const res = await fetch(`/api/timetable/train/${id}`);
                if (!res.ok) throw new Error("Nie udało się pobrać szczegółów pociągu.");
                const data = await res.json();
                setTrainDetails(data);
            } catch (err) {
                setError(err.message);
            }
        };

        fetchTrainDetails();
    }, [id]);

    useEffect(() => {
        const role = sessionStorage.getItem("role_id");
        if (role === null) navigate("/");
    }, [navigate]);

    if (error) return <p style={{ color: "red" }}>{error}</p>;
    if (!trainDetails) return <p>Ładowanie szczegółów pociągu...</p>;
    return (
        <div style={{ padding: 20 }}>
            <h2>Szczegóły pociągu {trainDetails.train_type} {trainDetails.train_number}</h2>
            <p><strong>Przewoźnik:</strong> {trainDetails.carrier}</p>
            <p><strong>Stacja docelowa:</strong> {trainDetails.final_station}</p>
            <p><strong>Trasa:</strong></p>
            <table style={{ borderCollapse: "collapse", width: "100%" }}>
                <thead>
                    <tr>
                        <th style={thStyle}>Stacja</th>
                        <th style={thStyle}>Przyjazd</th>
                        <th style={thStyle}>Odjazd</th>
                        <th style={thStyle}>Peron/Tor</th>
                    </tr>
                </thead>
                <tbody>
                    {trainDetails.stops.map((stop) => (
                        <tr key={stop.id} style={{ textAlign: "center" }}>
                            <td style={tdStyle}>{stop.station} <b>{stop.is_cancelled ? "POSTÓJ ODWOŁANY" : ""}</b></td>
                            <td style={tdStyle}>
                                {stop.arrival_time || "-"}{" "}
                                <b>{typeof stop.arrival_delay === "number" && stop.arrival_delay > 0 ? `+${stop.arrival_delay}` : ""}</b>
                            </td>

                            <td style={tdStyle}>
                                {stop.departure_time || "-"}{" "}
                                <b>{typeof stop.departure_delay === "number" && stop.departure_delay > 0 ? `+${stop.departure_delay}` : ""}</b>
                            </td>
                            {stop.bus===true ? <td style={tdStyle}><b>BUS</b></td> : stop.original===false ? 
                            <td style={tdStyle}><b>{stop.platform || "-"}/{stop.track || "-"}</b></td> :
                            <td style={tdStyle}>{stop.platform || "-"}/{stop.track || "-"}</td>}
                        </tr>
                    ))}
                </tbody>
            </table>

        </div>
    );
}

const thStyle = {
  padding: "10px",
  border: "1px solid #ccc",
  textAlign: "center",
};

const tdStyle = {
  padding: "8px",
  border: "1px solid #ccc",
};