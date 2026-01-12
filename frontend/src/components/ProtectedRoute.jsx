import { Navigate } from "react-router-dom";

export default function ProtectedRoute({ children, allowedRoles }) {
  const roleId = sessionStorage.getItem("role_id");

  // Jeśli brak sesji — przekieruj na stronę logowania
  if (!roleId) {
    return <Navigate to="/" replace />;
  }

  // Jeśli są dozwolone role, ale obecna nie pasuje
  if (allowedRoles && !allowedRoles.includes(parseInt(roleId))) {
    return <Navigate to="/" replace />;
  }

  // Jeśli wszystko OK — pokaż stronę
  return children;
}
