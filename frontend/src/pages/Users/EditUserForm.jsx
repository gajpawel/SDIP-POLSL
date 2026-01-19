import { useState, useEffect, useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import "./EditUserForm.css"; // Import stylów

export default function EditUserForm() {
  const [roles, setRoles] = useState([]);
  const [stations, setStations] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { id } = useParams();

  // Stan formularza
  const [user, setUser] = useState({
    login: "",
    name: "",
    surname: "",
    password: "",
    password_repeat: "",
    role_id: "",
    station_id: "", // ID stacji (dla backendu)
  });

  // Stan walidacji
  const [errors, setErrors] = useState({});

  // Stan dla wyszukiwarki stacji
  const [stationSearch, setStationSearch] = useState("");
  const [showStationList, setShowStationList] = useState(false);

  // 🔹 1. Pobieranie danych
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [rolesRes, stationsRes] = await Promise.all([
          fetch("/api/admin/roles"),
          fetch("/api/admin/stations"),
        ]);

        const rolesData = await rolesRes.json();
        const stationsData = await stationsRes.json();
        setRoles(rolesData);
        setStations(stationsData);

        // Jeśli tryb edycji -> pobierz usera
        if (id) {
          const res = await fetch(`/api/admin/admin/${id}`);
          if (res.ok) {
            const data = await res.json();
            setUser({
              ...data,
              password: "", // Nie pokazujemy hasła
              password_repeat: "",
              role_id: String(data.role_id),
              station_id: data.station_id || "",
            });

            // Ustaw nazwę stacji w wyszukiwarce na podstawie ID
            if (data.station_id) {
              const st = stationsData.find((s) => s.id === data.station_id);
              if (st) setStationSearch(st.name);
            }
          }
        }
      } catch (err) {
        console.error("Błąd danych:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  // 🔹 2. Logika Wielkich Liter (Imię/Nazwisko)
  const handleNameChange = (field, value) => {
    // Zamień pierwszą literę na wielką, resztę zostaw
    const capitalized = value.charAt(0).toUpperCase() + value.slice(1);
    setUser((prev) => ({ ...prev, [field]: capitalized }));
    
    // Wyczyść błąd w trakcie pisania
    if (errors[field]) setErrors((prev) => ({ ...prev, [field]: null }));
  };

  // Obsługa zwykłych pól
  const handleChange = (field, value) => {
    setUser((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) setErrors((prev) => ({ ...prev, [field]: null }));
  };

  // 🔹 3. Wybór Stacji (Autocomplete)
  const filteredStations = useMemo(() => {
    if (!stationSearch) return stations;
    return stations.filter((s) =>
      s.name.toLowerCase().includes(stationSearch.toLowerCase())
    );
  }, [stations, stationSearch]);

  const handleStationSelect = (station) => {
    setUser((prev) => ({ ...prev, station_id: station.id }));
    setStationSearch(station.name);
    setShowStationList(false);
    setErrors((prev) => ({ ...prev, station_id: null }));
  };

  const handleStationSearchChange = (e) => {
    setStationSearch(e.target.value);
    setShowStationList(true);
    // Jeśli użytkownik czyści pole, usuwamy ID stacji
    if (e.target.value === "") {
        setUser((prev) => ({ ...prev, station_id: "" }));
    }
  };

  // 🔹 4. Walidacja
  const validate = () => {
    const newErrors = {};
    const isAdmin = user.role_id === "1"; // ID roli Global Admina

    if (!user.login) newErrors.login = "Login jest wymagany.";
    if (!user.name) newErrors.name = "Imię jest wymagane.";
    if (!user.surname) newErrors.surname = "Nazwisko jest wymagane.";
    if (!user.role_id) newErrors.role_id = "Rola jest wymagana.";

    // Walidacja stacji: Wymagana, chyba że to Admin Globalny
    if (!isAdmin && !user.station_id) {
      newErrors.station_id = "Użytkownik z tą rolą musi mieć przypisaną stację.";
    }

    // Walidacja hasła (tylko jeśli jest wpisywane - przy edycji może być puste)
    if (!id || user.password) {
      if (user.password.length < 6) {
        newErrors.password = "Hasło musi mieć min. 6 znaków.";
      } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(user.password)) {
        newErrors.password = "Hasło musi zawierać małą literę, dużą literę i cyfrę.";
      }

      if (user.password !== user.password_repeat) {
        newErrors.password_repeat = "Hasła nie są identyczne.";
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // 🔹 5. Zapis
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    const url = id ? `/api/admin/edit/${id}` : "/api/admin/add";
    const method = id ? "PUT" : "POST";

    try {
      // Przygotowanie danych (usuń puste hasło przy edycji, żeby nie nadpisać)
      const payload = { ...user };
      if (id && !payload.password) {
        delete payload.password;
        delete payload.password_repeat;
      }

      if (payload.station_id === "") {
        delete payload.station_id; // Usuń, jeśli puste
      }

      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        alert(id ? "Zaktualizowano pomyślnie!" : "Dodano użytkownika!");
        navigate("/users");
      } else {
        const err = await res.json();
        alert(err.detail || "Błąd zapisu");
      }
    } catch (error) {
      console.error(error);
      alert("Błąd połączenia.");
    }
  };

  const handleDelete = async () => {
    if (!window.confirm("Na pewno usunąć użytkownika?")) return;
    try {
        await fetch(`/api/admin/delete/${id}`, { method: "DELETE" });
        navigate("/users");
    } catch(e) { alert("Błąd usuwania"); }
  };

  if (loading) return <p style={{textAlign:"center", marginTop:"20px"}}>Ładowanie...</p>;

  return (
    <div className="form-container">
      <h3 className="form-header">{id ? "Edycja Użytkownika" : "Nowy Użytkownik"}</h3>
      
      <form onSubmit={handleSubmit}>
        
        {/* LOGIN */}
        <div className="form-group">
          <label className="form-label">Login</label>
          <input
            className={`form-input ${errors.login ? "error" : ""}`}
            type="text"
            value={user.login}
            onChange={(e) => handleChange("login", e.target.value)}
          />
          {errors.login && <div className="error-message">{errors.login}</div>}
        </div>

        {/* IMIĘ I NAZWISKO */}
        <div style={{ display: "flex", gap: "15px" }}>
          <div className="form-group" style={{ flex: 1 }}>
            <label className="form-label">Imię</label>
            <input
              className={`form-input ${errors.name ? "error" : ""}`}
              type="text"
              value={user.name}
              onChange={(e) => handleNameChange("name", e.target.value)}
            />
            {errors.name && <div className="error-message">{errors.name}</div>}
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label className="form-label">Nazwisko</label>
            <input
              className={`form-input ${errors.surname ? "error" : ""}`}
              type="text"
              value={user.surname}
              onChange={(e) => handleNameChange("surname", e.target.value)}
            />
            {errors.surname && <div className="error-message">{errors.surname}</div>}
          </div>
        </div>

        {/* HASŁA */}
        <div className="form-group">
          <label className="form-label">Hasło {id && "(pozostaw puste, aby nie zmieniać)"}</label>
          <input
            className={`form-input ${errors.password ? "error" : ""}`}
            type="password"
            value={user.password}
            onChange={(e) => handleChange("password", e.target.value)}
          />
          {errors.password && <div className="error-message">{errors.password}</div>}
        </div>

        {user.password && (
          <div className="form-group">
            <label className="form-label">Powtórz hasło</label>
            <input
              className={`form-input ${errors.password_repeat ? "error" : ""}`}
              type="password"
              value={user.password_repeat}
              onChange={(e) => handleChange("password_repeat", e.target.value)}
            />
            {errors.password_repeat && <div className="error-message">{errors.password_repeat}</div>}
          </div>
        )}

        {/* ROLA */}
        <div className="form-group">
          <label className="form-label">Rola w systemie</label>
          <select
            className={`form-select ${errors.role_id ? "error" : ""}`}
            value={user.role_id}
            onChange={(e) => handleChange("role_id", e.target.value)}
          >
            <option value="">-- Wybierz rolę --</option>
            {roles.map((r) => (
              <option key={r.id} value={r.id}>{r.name}</option>
            ))}
          </select>
          {errors.role_id && <div className="error-message">{errors.role_id}</div>}
        </div>

        {/* STACJA (AUTOCOMPLETE) */}
        <div className="form-group">
          <label className="form-label">
            Przypisana stacja {user.role_id === "1" ? "(opcjonalne)" : "(wymagane)"}
          </label>
          <input
            className={`form-input ${errors.station_id ? "error" : ""}`}
            type="text"
            placeholder="Wpisz nazwę stacji..."
            value={stationSearch}
            onChange={handleStationSearchChange}
            onFocus={() => setShowStationList(true)}
            // Opóźnienie blura, żeby kliknięcie w listę zdążyło zadziałać
            onBlur={() => setTimeout(() => setShowStationList(false), 200)}
          />
          
          {showStationList && stationSearch && (
            <div className="suggestions-list">
              {filteredStations.length > 0 ? (
                filteredStations.map((s) => (
                  <div
                    key={s.id}
                    className="suggestion-item"
                    onClick={() => handleStationSelect(s)}
                  >
                    {s.name}
                  </div>
                ))
              ) : (
                <div className="suggestion-item" style={{ cursor: "default", color: "#888" }}>
                  Brak wyników
                </div>
              )}
            </div>
          )}
          {errors.station_id && <div className="error-message">{errors.station_id}</div>}
        </div>

        {/* PRZYCISKI */}
        <div className="form-actions">
          <button type="button" onClick={() => navigate(`/users`)} className="btn-back">
              Powrót
            </button>
          <button type="submit" className="btn-submit">
            Zapisz
          </button>
          {id && (
            <button type="button" onClick={handleDelete} className="btn-delete">
              Usuń
            </button>
          )}
        </div>

      </form>
    </div>
  );
}