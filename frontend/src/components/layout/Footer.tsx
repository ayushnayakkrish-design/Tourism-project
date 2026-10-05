import { Link } from "react-router-dom";

export function Footer() {
  return (
    <footer className="mt-24 border-t border-slate-200/60 dark:border-slate-700/60">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 py-12">
        <div className="grid gap-8 md:grid-cols-4">
          <div className="md:col-span-2">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 rounded-2xl bg-black text-white flex items-center justify-center font-wandor text-xl">
                W
              </div>
              <span className="font-wandor text-2xl">Wandor</span>
            </div>
            <p className="mt-4 text-slate-600 dark:text-slate-400 max-w-md">
              Cinematic travel intelligence — discover places, plan itineraries, verify visits,
              earn rewards and share your journey with the community.
            </p>
          </div>
          <nav aria-label="Product">
            <h4 className="font-semibold text-sm uppercase tracking-wide text-slate-500">Product</h4>
            <ul className="mt-3 space-y-2 text-sm">
              <li><Link to="/discover" className="text-slate-600 dark:text-slate-400 hover:text-slate-900">Discover</Link></li>
              <li><Link to="/itinerary" className="text-slate-600 dark:text-slate-400 hover:text-slate-900">Plan a Trip</Link></li>
              <li><Link to="/rewards" className="text-slate-600 dark:text-slate-400 hover:text-slate-900">Rewards</Link></li>
              <li><Link to="/community" className="text-slate-600 dark:text-slate-400 hover:text-slate-900">Community</Link></li>
            </ul>
          </nav>
          <nav aria-label="Account">
            <h4 className="font-semibold text-sm uppercase tracking-wide text-slate-500">Account</h4>
            <ul className="mt-3 space-y-2 text-sm">
              <li><Link to="/login" className="text-slate-600 dark:text-slate-400 hover:text-slate-900">Log in</Link></li>
              <li><Link to="/register" className="text-slate-600 dark:text-slate-400 hover:text-slate-900">Sign up</Link></li>
              <li><Link to="/profile" className="text-slate-600 dark:text-slate-400 hover:text-slate-900">Profile</Link></li>
              <li><Link to="/wallet" className="text-slate-600 dark:text-slate-400 hover:text-slate-900">Wallet</Link></li>
            </ul>
          </nav>
        </div>
        <div className="mt-8 pt-8 border-t border-slate-200/60 dark:border-slate-700/60 text-sm text-slate-500 text-center">
          Built for travelers. Powered by the Tourism Intelligence Backend.
        </div>
      </div>
    </footer>
  );
}
