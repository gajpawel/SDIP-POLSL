import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";

export const useStationData = () => {
  // Pobieramy parametry z URL (jeśli hook jest używany na stronie ze ścieżką :selectedStationId)
  const { selectedStationId } = useParams();

  const [stationId, setStationId] = useState(null);
  const [stationName, setStationName] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Pobranie danych z sessionStorage (można to zrobić też wewnątrz useEffect, ale tu jest ok)
  const roleId = parseInt(sessionStorage.getItem("role_id"));
  const adminId = sessionStorage.getItem("admin_id");

  useEffect(() => {
    // Reset stanów przy zmianie zależności
    setError("");
    setLoading(true);

    const fetchData = async () => {
      try {
        if (roleId === 2 || roleId === 3) {
          // Logika dla Admina/Pracownika
          const res = await fetch(`/api/admin/admin/${adminId}`);
          if (!res.ok) throw new Error("Nie udało się pobrać danych administratora");
          
          const data = await res.json();
          if (data.station_id) {
            setStationId(data.station_id);
            setStationName(data.station);
          } else {
            setError("Brak przypisanej stacji dla tego użytkownika.");
          }

        } else if (roleId === 1 && selectedStationId) {
          // Logika dla zwykłego usera lub wyboru konkretnej stacji
          setStationId(selectedStationId);
          
          const stationsRes = await fetch(`/api/timetable/station/${selectedStationId}`);
          if (!stationsRes.ok) throw new Error("Nie udało się pobrać nazwy stacji.");
          
          const data = await stationsRes.json();
          setStationName(data.name);
        }
      } catch (err) {
        console.error("Błąd pobierania danych:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();

  }, [roleId, adminId, selectedStationId]);

  // Zwracamy wszystko, czego potrzebują Twoje komponenty
  return { stationId, stationName, loading, setLoading, error, setError, roleId };
};