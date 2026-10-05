import { Routes, Route } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { ProtectedRoute, ModeratorGate, AdminGate } from "./components/layout/ProtectedRoute";
import { Landing } from "./pages/Landing";
import { LoginPage } from "./pages/Auth/Login";
import { RegisterPage } from "./pages/Auth/Register";
import { Dashboard } from "./pages/Dashboard";
import { ProfilePage } from "./pages/Profile";
import { DiscoverPage } from "./pages/Discover";
import { PlaceDetailPage } from "./pages/PlaceDetail";
import { RoutesPage } from "./pages/RoutesPage";
import { CrowdPage } from "./pages/Crowd";
import { SeasonPage } from "./pages/Season";
import { ItineraryPage } from "./pages/Itinerary";
import { VisitsPage } from "./pages/Visits";
import { WalletPage } from "./pages/Wallet";
import { RewardsPage } from "./pages/Rewards";
import { CommunityPage } from "./pages/Community";
import { ModerationPage } from "./pages/Moderation";
import { LocalizationPage } from "./pages/Localization";
import { VoicePage } from "./pages/Voice";
import { AdminPage } from "./pages/Admin";
import { NotFoundPage, ForbiddenPage } from "./pages/NotFound";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Landing />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
        <Route path="403" element={<ForbiddenPage />} />

        <Route path="dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="discover" element={<ProtectedRoute><DiscoverPage /></ProtectedRoute>} />
        <Route path="places/:placeId" element={<ProtectedRoute><PlaceDetailPage /></ProtectedRoute>} />
        <Route path="routes" element={<ProtectedRoute><RoutesPage /></ProtectedRoute>} />
        <Route path="crowd" element={<ProtectedRoute><CrowdPage /></ProtectedRoute>} />
        <Route path="season" element={<ProtectedRoute><SeasonPage /></ProtectedRoute>} />
        <Route path="season/:placeId" element={<ProtectedRoute><SeasonPage /></ProtectedRoute>} />
        <Route path="itinerary" element={<ProtectedRoute><ItineraryPage /></ProtectedRoute>} />

        <Route path="visits" element={<ProtectedRoute><VisitsPage /></ProtectedRoute>} />
        <Route path="wallet" element={<ProtectedRoute><WalletPage /></ProtectedRoute>} />
        <Route path="rewards" element={<ProtectedRoute><RewardsPage /></ProtectedRoute>} />

        <Route path="community" element={<ProtectedRoute><CommunityPage /></ProtectedRoute>} />
        <Route path="localization" element={<ProtectedRoute><LocalizationPage /></ProtectedRoute>} />
        <Route path="voice" element={<ProtectedRoute><VoicePage /></ProtectedRoute>} />
        <Route path="profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />

        <Route path="moderation" element={<ModeratorGate><ModerationPage /></ModeratorGate>} />
        <Route path="admin/*" element={<AdminGate><AdminPage /></AdminGate>} />

        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
