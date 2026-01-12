import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import UserList from "./pages/UserList";
import EditUserForm from "./components/EditUserForm";
import ProtectedRoute from "./components/ProtectedRoute";
import TimeTable from "./pages/Timetable/TimeTable";
import Layout from "./Layout";
import { useState } from "react";
import TrainDetails from "./pages/Timetable/TrainDetails";
import EditTrain from "./pages/Timetable/EditTrain";
import ChooseStationForm from "./components/ChooseStationForm";
import Displays from "./pages/Displays/Displays";
import AddDisplay from "./pages/Displays/AddDisplay";
import EditDisplay from "./pages/Displays/EditDisplay";
import VoiceAnnouncements from "./pages/VoiceAnnouncements";
import Dashboard from "./pages/Dashboard";
import VoiceSettings from "./pages/VoiceSettings";

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(
    !!sessionStorage.getItem("role_id")
  );
  return (
    <BrowserRouter>
      <Layout isLoggedIn={isLoggedIn} setIsLoggedIn={setIsLoggedIn}>
        <Routes>
          <Route path="/" element={<LoginPage setIsLoggedIn={setIsLoggedIn} />} />

          <Route
          path="/dashboard"
          element={
            <ProtectedRoute allowedRoles={[1, 2, 3]}>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/choose-station/:type"
          element={
            <ProtectedRoute allowedRoles={[1]}>
              <ChooseStationForm />
            </ProtectedRoute>
          }
        />
        <Route
          path="/timetable"
          element={
            <ProtectedRoute allowedRoles={[2, 3]}>
              <TimeTable />
            </ProtectedRoute>
          }
        />
        <Route
          path="/timetable/:selectedStationId"
          element={
            <ProtectedRoute allowedRoles={[1]}>
              <TimeTable />
            </ProtectedRoute>
          }
        />
        <Route
          path="/displays/:selectedStationId"
          element={
            <ProtectedRoute allowedRoles={[1]}>
              <Displays />
            </ProtectedRoute>
          }
        />
        <Route
          path="/displays"
          element={
            <ProtectedRoute allowedRoles={[2, 3]}>
              <Displays />
            </ProtectedRoute>
          }
        />
        <Route
          path="/add-display/:station_id"
          element={
            <ProtectedRoute allowedRoles={[1, 2]}>
              <AddDisplay />
            </ProtectedRoute>
          }
        />
        <Route
          path="/train-details/:id"
          element={
            <ProtectedRoute allowedRoles={[1, 2, 3]}>
              <TrainDetails />
            </ProtectedRoute>
          }
        />
        <Route
          path="/edit-train/:id"
          element={
            <ProtectedRoute allowedRoles={[1, 2, 3]}>
              <EditTrain />
            </ProtectedRoute>
          }
        />
        <Route
          path="/edit-display/:displayId"
          element={
            <ProtectedRoute allowedRoles={[1, 2]}>
              <EditDisplay />
            </ProtectedRoute>
          }
        />
        <Route
          path="/users"
          element={
            <ProtectedRoute allowedRoles={[1]}>
              <UserList />
            </ProtectedRoute>
          }
        />
        <Route
          path="/edit-user"
          element={
            <ProtectedRoute allowedRoles={[1]}>
              <EditUserForm />
            </ProtectedRoute>
          }
        />
        <Route
          path="/edit-user/:id"
          element={
            <ProtectedRoute allowedRoles={[1]}>
              <EditUserForm />
            </ProtectedRoute>
          }
        />
        <Route
          path="/voice-announcements/:selectedStationId"
          element={
            <ProtectedRoute allowedRoles={[1]}>
              <VoiceAnnouncements />
            </ProtectedRoute>
          }
        />
        <Route
          path="/voice-announcements"
          element={
            <ProtectedRoute allowedRoles={[2, 3]}>
              <VoiceAnnouncements />
            </ProtectedRoute>
          }
        />
        <Route
          path="/voice-settings/:stationId"
          element={
            <ProtectedRoute allowedRoles={[1, 2]}>
              <VoiceSettings />
            </ProtectedRoute>
          }
        />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
