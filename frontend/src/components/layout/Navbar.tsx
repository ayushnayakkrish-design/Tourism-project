import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  Plane,
  MapPin,
  Route,
  Sparkles,
  Users,
  Wallet,
  Gift,
  Settings,
  Globe,
  Mic,
  Menu,
  X,
  LogOut,
  User,
  ChevronDown,
  ShieldCheck,
} from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { isAdmin, isModerator } from "@/api/types";
import { cn } from "@/lib/utils";

const TOURIST_LINKS = [
  { to: "/discover", label: "Discover", icon: MapPin },
  { to: "/routes", label: "Routes", icon: Route },
  { to: "/itinerary", label: "Planner", icon: Sparkles },
  { to: "/visits", label: "Visits", icon: Plane },
  { to: "/wallet", label: "Wallet", icon: Wallet },
  { to: "/rewards", label: "Rewards", icon: Gift },
  { to: "/community", label: "Community", icon: Users },
];

const MORE_LINKS = [
  { to: "/crowd", label: "Crowd Intel", icon: Users },
  { to: "/season", label: "Seasons", icon: Globe },
  { to: "/localization", label: "Translate", icon: Globe },
  { to: "/voice", label: "Voice", icon: Mic },
];

export function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const { user, role, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const isActive = (path: string) => location.pathname === path || location.pathname.startsWith(path + "/");

  const modLinks = isModerator(role)
    ? [{ to: "/moderation", label: "Moderation", icon: ShieldCheck }]
    : [];
  const adminLinks = isAdmin(role)
    ? [{ to: "/admin", label: "Admin", icon: Settings }]
    : [];

  const handleLogout = () => {
    logout();
    navigate("/");
    setUserMenuOpen(false);
    setMobileOpen(false);
  };

  return (
    <header className="fixed top-0 inset-x-0 z-40">
      <nav className="mx-auto max-w-7xl px-3 sm:px-6" aria-label="Main navigation">
        <div className="mt-3 rounded-3xl border-2 border-white/35 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl shadow-glass">
          <div className="flex h-16 items-center justify-between px-4 sm:px-6">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2 group" aria-label="Wandor home">
              <div className="w-10 h-10 rounded-2xl bg-black text-white flex items-center justify-center font-wandor text-xl group-hover:scale-105 transition-transform">
                W
              </div>
              <span className="font-wandor text-2xl tracking-tight">Wandor</span>
            </Link>

            {/* Desktop links */}
            <div className="hidden lg:flex items-center gap-1">
              {user &&
                TOURIST_LINKS.map(({ to, label, icon: Icon }) => (
                  <Link
                    key={to}
                    to={to}
                    className={cn(
                      "flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium transition-all",
                      isActive(to)
                        ? "bg-black text-white"
                        : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                    )}
                  >
                    <Icon className="w-4 h-4" aria-hidden="true" />
                    {label}
                  </Link>
                ))}
              {user &&
                modLinks.concat(adminLinks).map(({ to, label, icon: Icon }) => (
                  <Link
                    key={to}
                    to={to}
                    className={cn(
                      "flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium transition-all",
                      isActive(to)
                        ? "bg-terracotta-600 text-white"
                        : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                    )}
                  >
                    <Icon className="w-4 h-4" aria-hidden="true" />
                    {label}
                  </Link>
                ))}
            </div>

            {/* Right side */}
            <div className="flex items-center gap-2">
              {!user ? (
                <>
                  <Link
                    to="/login"
                    className="hidden sm:inline-flex px-4 py-2 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                  >
                    Log in
                  </Link>
                  <Link
                    to="/register"
                    className="inline-flex px-4 py-2 rounded-xl text-sm font-medium bg-black text-white hover:bg-black/90 active:scale-95 transition"
                  >
                    Plan My Trip
                  </Link>
                </>
              ) : (
                <div className="relative">
                  <button
                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                    className="flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                    aria-expanded={userMenuOpen}
                    aria-haspopup="menu"
                  >
                    <div className="w-8 h-8 rounded-xl bg-terracotta-600 text-white flex items-center justify-center text-sm font-bold">
                      {(user.display_name || user.email || "U").charAt(0).toUpperCase()}
                    </div>
                    <span className="hidden sm:block text-sm font-medium max-w-[120px] truncate">
                      {user.display_name || user.email}
                    </span>
                    <ChevronDown className="w-4 h-4" aria-hidden="true" />
                  </button>
                  {userMenuOpen && (
                    <>
                      <div
                        className="fixed inset-0 z-40"
                        onClick={() => setUserMenuOpen(false)}
                        aria-hidden="true"
                      />
                      <div
                        className="absolute right-0 mt-2 w-56 rounded-2xl border-2 border-white/35 bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl shadow-glass-hover z-50 py-2"
                        role="menu"
                      >
                        <div className="px-4 py-2 border-b border-slate-200/60">
                          <p className="text-sm font-medium truncate">{user.display_name}</p>
                          <p className="text-xs text-slate-500 truncate">{user.email}</p>
                          <span className="inline-block mt-1 text-xs px-2 py-0.5 rounded-lg bg-terracotta-100 text-terracotta-800 font-medium">
                            {role}
                          </span>
                        </div>
                        <Link
                          to="/profile"
                          className="flex items-center gap-2 px-4 py-2.5 text-sm hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                          onClick={() => setUserMenuOpen(false)}
                          role="menuitem"
                        >
                          <User className="w-4 h-4" /> Profile & Settings
                        </Link>
                        {MORE_LINKS.map(({ to, label, icon: Icon }) => (
                          <Link
                            key={to}
                            to={to}
                            className="flex items-center gap-2 px-4 py-2.5 text-sm hover:bg-slate-100 dark:hover:bg-slate-800 transition lg:hidden"
                            onClick={() => setUserMenuOpen(false)}
                            role="menuitem"
                          >
                            <Icon className="w-4 h-4" /> {label}
                          </Link>
                        ))}
                        <button
                          onClick={handleLogout}
                          className="flex items-center gap-2 w-full px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition"
                          role="menuitem"
                        >
                          <LogOut className="w-4 h-4" /> Log out
                        </button>
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* Mobile toggle */}
              <button
                onClick={() => setMobileOpen(!mobileOpen)}
                className="lg:hidden p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                aria-label={mobileOpen ? "Close menu" : "Open menu"}
                aria-expanded={mobileOpen}
              >
                {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
            </div>
          </div>

          {/* Mobile menu */}
          {mobileOpen && (
            <div className="lg:hidden px-4 pb-4 border-t border-slate-200/60 pt-3 grid grid-cols-2 gap-1.5">
              {!user ? (
                <>
                  <Link
                    to="/login"
                    onClick={() => setMobileOpen(false)}
                    className="col-span-1 text-center px-4 py-2.5 rounded-xl text-sm font-medium bg-slate-100 dark:bg-slate-800"
                  >
                    Log in
                  </Link>
                  <Link
                    to="/register"
                    onClick={() => setMobileOpen(false)}
                    className="col-span-1 text-center px-4 py-2.5 rounded-xl text-sm font-medium bg-black text-white"
                  >
                    Plan My Trip
                  </Link>
                </>
              ) : (
                <>
                  {TOURIST_LINKS.concat(MORE_LINKS, modLinks, adminLinks).map(
                    ({ to, label, icon: Icon }) => (
                      <Link
                        key={to}
                        to={to}
                        onClick={() => setMobileOpen(false)}
                        className={cn(
                          "flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium transition",
                          isActive(to)
                            ? "bg-black text-white"
                            : "bg-slate-100/70 dark:bg-slate-800/70"
                        )}
                      >
                        <Icon className="w-4 h-4" aria-hidden="true" />
                        {label}
                      </Link>
                    )
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </nav>
    </header>
  );
}
