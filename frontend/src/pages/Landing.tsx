import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  MapPin,
  Sparkles,
  Gift,
  Users,
  ArrowRight,
  Play,
  CheckCircle2,
  Camera,
  ShieldCheck,
  Coins,
  Star,
  ChevronDown,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { aiApi } from "@/api/localization";
import { crowdMeta } from "@/lib/utils";

const HERO_VIDEO =
  "https://cdn.coverr.co/videos/coverr-aerial-shot-of-a-tropical-beach-5244/1080p.mp4";

const DESTINATIONS = [
  {
    name: "Konark Sun Temple",
    place: "Odisha, India",
    crowd: "MODERATE",
    rating: "4.8",
    img: "https://images.unsplash.com/photo-1587474260584-136574528ed5?auto=format&fit=crop&w=900&q=80",
    tag: "UNESCO Heritage",
  },
  {
    name: "Puri Golden Beach",
    place: "Odisha, India",
    crowd: "HIGH",
    rating: "4.6",
    img: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=900&q=80",
    tag: "Beach Escape",
  },
  {
    name: "Chilika Lake",
    place: "Odisha, India",
    crowd: "LOW",
    rating: "4.7",
    img: "https://images.unsplash.com/photo-1439066615861-d1af74d74000?auto=format&fit=crop&w=900&q=80",
    tag: "Nature Retreat",
  },
];

const STEPS = [
  {
    icon: MapPin,
    title: "Discover places",
    text: "Search real places, see crowd forecasts, seasonal scores and accessibility before you go.",
  },
  {
    icon: Sparkles,
    title: "Plan with AI",
    text: "Generate day-by-day itineraries with travel times, opening hours and crowd awareness.",
  },
  {
    icon: Camera,
    title: "Verify visits",
    text: "Check in with GPS, upload photo proof and let anti-cheat verification keep it fair.",
  },
  {
    icon: Gift,
    title: "Earn rewards",
    text: "Collect points in your wallet and redeem catalog rewards with secure codes.",
  },
];

const FAQS = [
  {
    q: "Is Wandor free to use?",
    a: "Yes. Discovery, planning, visit verification and community features are free. Rewards are redeemed with points you earn by visiting places and uploading photo proof.",
  },
  {
    q: "How does visit verification work?",
    a: "When you check in, the backend measures your GPS distance from the place with Haversine math and returns a confidence score. Photo proof is hashed to prevent duplicates. Anything suspicious is flagged for review — never auto-banned.",
  },
  {
    q: "What happens if I am flagged by anti-cheat?",
    a: "FLAGGED means a human or moderator review state, not a ban. You will see a clear reason such as impossible travel or duplicate proof, and you can retry with valid data.",
  },
  {
    q: "Can I contribute places and reviews?",
    a: "Yes. Community submissions go through moderator review before becoming public. Approved places are visible to every traveler.",
  },
];

export function Landing() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [aiPrompt, setAiPrompt] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiResult, setAiResult] = useState<string | null>(null);
  const [aiError, setAiError] = useState<string | null>(null);
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  const handleAiPrompt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!aiPrompt.trim()) return;
    setAiLoading(true);
    setAiError(null);
    setAiResult(null);
    try {
      const res = await aiApi.intent({ query: aiPrompt.trim() });
      setAiResult(`Intent: ${res.intent} · ${res.parameters.query.slice(0, 160)}`);
    } catch (err) {
      setAiError(err instanceof Error ? err.message : "AI unavailable right now.");
    } finally {
      setAiLoading(false);
    }
  };

  return (
    <div className="-mt-24">
      {/* ================= HERO ================= */}
      <section className="relative min-h-[96vh] flex items-end overflow-hidden" aria-label="Wandor hero">
        <div className="absolute inset-0" aria-hidden="true">
          <img
            src="https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=2000&q=80"
            alt=""
            className="w-full h-full object-cover animate-ken-burns"
          />
          <video
            className="absolute inset-0 w-full h-full object-cover hidden"
            autoPlay
            muted
            loop
            playsInline
            poster="https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=2000&q=80"
            onError={(e) => ((e.target as HTMLVideoElement).style.display = "none")}
          >
            <source src={HERO_VIDEO} type="video/mp4" />
          </video>
          <div className="absolute inset-0 hero-gradient" />
        </div>

        <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 pb-16 pt-40 w-full">
          <div className="max-w-3xl animate-fade-up">
            <div className="inline-flex items-center gap-2 rounded-full border-2 border-white/40 bg-white/20 backdrop-blur-xl px-4 py-1.5 text-sm font-medium text-slate-900">
              <Sparkles className="w-4 h-4" aria-hidden="true" />
              Travel intelligence · Gamified journeys
            </div>
            <h1 className="mt-5 text-5xl sm:text-7xl font-extrabold leading-[1.02] tracking-tight text-slate-950">
              Travel beyond
              <br />
              the <span className="font-wandor font-normal text-terracotta-700">ordinary</span>
            </h1>
            <p className="mt-5 text-lg sm:text-xl text-slate-700 max-w-2xl">
              Discover places with live crowd intelligence, plan cinematic multi-day itineraries,
              verify your visits and earn rewards — all in one glass-polished experience.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button size="lg" onClick={() => navigate(user ? "/dashboard" : "/register")}>
                {user ? "Open Dashboard" : "Plan My Trip"}
                <ArrowRight className="w-5 h-5" aria-hidden="true" />
              </Button>
              <Button size="lg" variant="outline" onClick={() => navigate("/discover")}>
                <Play className="w-5 h-5" aria-hidden="true" />
                Discover places
              </Button>
            </div>

            {/* AI prompt bar */}
            <form
              onSubmit={handleAiPrompt}
              className="mt-8 rounded-3xl border-2 border-white/40 bg-white/80 backdrop-blur-xl shadow-glass p-2 flex flex-col sm:flex-row gap-2"
              aria-label="Ask Wandor AI"
            >
              <label htmlFor="ai-prompt" className="sr-only">
                Ask Wandor AI where to go
              </label>
              <input
                id="ai-prompt"
                value={aiPrompt}
                onChange={(e) => setAiPrompt(e.target.value)}
                placeholder="Ask Wandor: “quiet beaches near Puri this weekend…”"
                className="flex-1 px-4 py-3 rounded-2xl bg-transparent text-slate-900 placeholder-slate-500 focus:outline-none"
              />
              <Button type="submit" loading={aiLoading} className="sm:w-auto w-full">
                <Sparkles className="w-4 h-4" aria-hidden="true" />
                Ask AI
              </Button>
            </form>
            {aiResult && (
              <p className="mt-3 text-sm rounded-2xl bg-white/80 backdrop-blur px-4 py-2.5 border border-white/40" role="status">
                <CheckCircle2 className="inline w-4 h-4 mr-1 text-emerald-600" aria-hidden="true" />
                {aiResult}
              </p>
            )}
            {aiError && (
              <p className="mt-3 text-sm rounded-2xl bg-red-50/90 px-4 py-2.5 border border-red-200 text-red-700" role="alert">
                {aiError}
              </p>
            )}
          </div>
        </div>
      </section>

      {/* ================= STATS STRIP ================= */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 -mt-2">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 stagger">
          {[
            { icon: MapPin, v: "57", l: "Live API routes" },
            { icon: Users, v: "9", l: "Verified travel flows" },
            { icon: Coins, v: "60+", l: "Points per journey" },
            { icon: ShieldCheck, v: "100%", l: "Fair-play verified" },
          ].map(({ icon: Icon, v, l }) => (
            <Card key={l} variant="glass" interactive>
              <CardContent className="flex items-center gap-3">
                <div className="w-11 h-11 rounded-2xl bg-black text-white flex items-center justify-center">
                  <Icon className="w-5 h-5" aria-hidden="true" />
                </div>
                <div>
                  <p className="text-2xl font-extrabold">{v}</p>
                  <p className="text-sm text-slate-600">{l}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* ================= DESTINATIONS ================= */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 mt-16" aria-label="Featured destinations">
        <div className="flex items-end justify-between gap-4 flex-wrap">
          <div>
            <p className="text-sm font-semibold uppercase tracking-widest text-terracotta-600">Curated for you</p>
            <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight mt-2">
              Destinations worth the journey
            </h2>
          </div>
          <Button variant="outline" onClick={() => navigate("/discover")}>
            Explore all <ArrowRight className="w-4 h-4" aria-hidden="true" />
          </Button>
        </div>
        <div className="mt-8 grid gap-5 md:grid-cols-3 stagger">
          {DESTINATIONS.map((d) => {
            const cm = crowdMeta(d.crowd);
            return (
              <Card key={d.name} variant="glass" interactive className="group">
                <div className="relative h-64 overflow-hidden">
                  <img
                    src={d.img}
                    alt={d.name}
                    loading="lazy"
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/10 to-transparent" />
                  <span className="absolute top-3 left-3 text-xs font-semibold px-3 py-1 rounded-full bg-white/85 backdrop-blur">
                    {d.tag}
                  </span>
                  <span className={`absolute top-3 right-3 text-xs font-semibold px-3 py-1 rounded-full backdrop-blur ${cm.bg} ${cm.color}`}>
                    {cm.label} crowds
                  </span>
                  <div className="absolute bottom-3 left-4 right-4 text-white">
                    <h3 className="text-xl font-bold">{d.name}</h3>
                    <p className="text-sm opacity-90 flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5" aria-hidden="true" /> {d.place}
                    </p>
                  </div>
                </div>
                <CardContent className="flex items-center justify-between">
                  <span className="flex items-center gap-1 text-sm font-medium">
                    <Star className="w-4 h-4 fill-amber-400 text-amber-400" aria-hidden="true" />
                    {d.rating} traveler rating
                  </span>
                  <Button size="sm" variant="ghost" onClick={() => navigate("/discover")}>
                    View <ArrowRight className="w-4 h-4" aria-hidden="true" />
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      {/* ================= HOW IT WORKS ================= */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 mt-20" aria-label="How Wandor works">
        <p className="text-sm font-semibold uppercase tracking-widest text-terracotta-600 text-center">How it works</p>
        <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight mt-2 text-center">
          From discovery to rewards
        </h2>
        <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4 stagger">
          {STEPS.map(({ icon: Icon, title, text }, i) => (
            <Card key={title} variant="glass" interactive>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div className="w-12 h-12 rounded-2xl bg-terracotta-600 text-white flex items-center justify-center">
                    <Icon className="w-6 h-6" aria-hidden="true" />
                  </div>
                  <span className="font-wandor text-3xl text-slate-300">0{i + 1}</span>
                </div>
                <h3 className="mt-4 text-lg font-bold">{title}</h3>
                <p className="mt-1.5 text-sm text-slate-600">{text}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* ================= CTA ================= */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 mt-20" aria-label="Get started">
        <div className="relative overflow-hidden rounded-[2.5rem] bg-black text-white">
          <img
            src="https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?auto=format&fit=crop&w=1800&q=80"
            alt=""
            aria-hidden="true"
            className="absolute inset-0 w-full h-full object-cover opacity-40"
          />
          <div className="relative px-8 py-16 sm:px-16 text-center">
            <h2 className="font-wandor text-4xl sm:text-6xl">Your journey starts here</h2>
            <p className="mt-4 text-white/80 max-w-xl mx-auto">
              Join Wandor to plan smarter trips, verify every adventure and turn your travels into rewards.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <Link
                to={user ? "/dashboard" : "/register"}
                className="inline-flex items-center gap-2 px-8 py-4 rounded-2xl bg-white text-black font-semibold hover:bg-white/90 active:scale-95 transition"
              >
                {user ? "Go to Dashboard" : "Create free account"}
                <ArrowRight className="w-5 h-5" aria-hidden="true" />
              </Link>
              <Link
                to="/itinerary"
                className="inline-flex items-center gap-2 px-8 py-4 rounded-2xl border-2 border-white/40 font-semibold hover:bg-white/10 active:scale-95 transition"
              >
                <Sparkles className="w-5 h-5" aria-hidden="true" />
                Try the planner
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ================= FAQ ================= */}
      <section className="mx-auto max-w-4xl px-4 sm:px-6 mt-20" aria-label="Frequently asked questions">
        <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-center">Questions, answered</h2>
        <div className="mt-6 space-y-3">
          {FAQS.map((f, i) => (
            <div key={f.q} className="rounded-2xl border-2 border-white/35 bg-white/80 backdrop-blur-xl overflow-hidden">
              <button
                onClick={() => setOpenFaq(openFaq === i ? null : i)}
                className="w-full flex items-center justify-between px-5 py-4 text-left font-semibold"
                aria-expanded={openFaq === i}
              >
                {f.q}
                <ChevronDown
                  className={`w-5 h-5 transition-transform ${openFaq === i ? "rotate-180" : ""}`}
                  aria-hidden="true"
                />
              </button>
              {openFaq === i && <p className="px-5 pb-5 text-slate-600">{f.a}</p>}
            </div>
          ))}
        </div>
        <div className="mt-8 text-center">
          <Input id="newsletter" placeholder="you@example.com" className="hidden" aria-hidden="true" tabIndex={-1} />
        </div>
      </section>
    </div>
  );
}
