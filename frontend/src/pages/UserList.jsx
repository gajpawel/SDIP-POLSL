import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function UserList() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // Pobranie użytkowników z backendu
  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const res = await fetch("/api/admin/admins");
        if (!res.ok) throw new Error("Błąd pobierania danych");
        const data = await res.json();
        setUsers(data);
      } catch (err) {
        console.error("Błąd:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, []);

  if (loading) return <p>Ładowanie danych...</p>;

  return (
    <div style={{ padding: "30px" }}>
      <h2>Lista użytkowników</h2>

      {/* Przycisk dodawania nowego */}
      <div style={{ marginBottom: "20px" }}>
        <button
          onClick={() => navigate("/edit-user")}
          style={{
            backgroundColor: "#0275d8",
            color: "white",
            border: "none",
            padding: "10px 15px",
            borderRadius: "5px",
            cursor: "pointer",
          }}
        >
          Dodaj użytkownika
        </button>
      </div>

      {/* Tabela z użytkownikami */}
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          border: "1px solid #ccc",
        }}
      >
        <thead style={{ backgroundColor: "#d7c7c7ff" }}>
          <tr>
            <th style={thStyle}>ID</th>
            <th style={thStyle}>Login</th>
            <th style={thStyle}>Imię i Nazwisko</th>
            <th style={thStyle}>Rola</th>
            <th style={thStyle}>Stacja</th>
            <th style={thStyle}>Akcje</th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id} style={{ textAlign: "center" }}>
              <td style={tdStyle}>{u.id}</td>
              <td style={tdStyle}>{u.login}</td>
              <td style={tdStyle}>{u.name && u.surname ? `${u.name} ${u.surname}` : "-"}</td>
              <td style={tdStyle}>{u.role || "-"}</td>
              <td style={tdStyle}>{u.station || "-"}</td>
              <td style={tdStyle}>
                <button
                  onClick={() => navigate(`/edit-user/${u.id}`)}
                  style={{
                    backgroundColor: "#5cb85c",
                    color: "white",
                    border: "none",
                    padding: "6px 10px",
                    borderRadius: "5px",
                    cursor: "pointer",
                  }}
                >
                  Edytuj
                </button>
              </td>
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
