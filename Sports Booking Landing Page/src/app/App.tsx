import { useState } from "react";
import {
  MapPin,
  Star,
  ArrowLeft,
  Clock,
  Users,
  Calendar,
  CheckCircle2,
  Phone,
  User,
  Search,
  ChevronRight,
  Mail,
  Lock,
  Eye,
  EyeOff,
  LogOut,
  Ticket,
  ChevronDown,
  X,
} from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────

type Page =
  | "landing"
  | "login"
  | "signup"
  | "detail"
  | "confirmed"
  | "my-bookings";

interface AuthUser {
  name: string;
  email: string;
  avatar: string;
}

interface BookingData {
  center: Center;
  sport: string;
  date: Date;
  slot: string;
  name: string;
  phone: string;
  ref: string;
}

// ─── Centers data ─────────────────────────────────────────────────────────────

const CENTERS = [
  {
    id: 1,
    name: "Downtown Athletic Hub",
    location: "123 Main St, Downtown",
    rating: 4.8,
    reviews: 312,
    sports: ["Basketball", "Tennis", "Badminton"],
    priceFrom: 25,
    image:
      "https://images.unsplash.com/photo-1546519638405-a9d1273b5c28?w=800&h=520&fit=crop&auto=format",
    tag: "Popular" as const,
    courts: 8,
    hours: "06:00 – 23:00",
    description:
      "State-of-the-art courts in the heart of downtown. Premium hardwood floors, climate control, and professional lighting across 8 multi-sport courts. Changing rooms, equipment rental, and a café on-site.",
  },
  {
    id: 2,
    name: "Westside Sport Complex",
    location: "88 Harbor Blvd, West End",
    rating: 4.6,
    reviews: 189,
    sports: ["Football", "Swimming", "Squash"],
    priceFrom: 30,
    image:
      "https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=800&h=520&fit=crop&auto=format",
    tag: "New" as const,
    courts: 12,
    hours: "07:00 – 22:00",
    description:
      "The city's newest and largest facility. Features Olympic-standard pitches, a 25m indoor swimming pool, and 4 glass-back squash courts with spectator seating. Fully accessible.",
  },
  {
    id: 3,
    name: "Greenfield Arena",
    location: "45 Park Ave, Greenfield",
    rating: 4.7,
    reviews: 254,
    sports: ["Cricket", "Football", "Athletics"],
    priceFrom: 20,
    image:
      "https://images.unsplash.com/photo-1529900748604-07564a03e7a6?w=800&h=520&fit=crop&auto=format",
    tag: null,
    courts: 6,
    hours: "06:00 – 21:00",
    description:
      "Sprawling outdoor arena surrounded by Greenfield Park. Full-size cricket pitches, five-a-side cages, and a 400m synthetic athletics track with all jump and throw facilities included.",
  },
  {
    id: 4,
    name: "Metro Courts",
    location: "200 Central Park, Midtown",
    rating: 4.9,
    reviews: 421,
    sports: ["Tennis", "Padel", "Volleyball"],
    priceFrom: 35,
    image:
      "https://images.unsplash.com/photo-1622279457486-62dcc4a431d6?w=800&h=520&fit=crop&auto=format",
    tag: "Top Rated" as const,
    courts: 10,
    hours: "06:00 – 23:00",
    description:
      "Award-winning racket sports complex with 6 floodlit tennis courts, 3 padel courts, and a dedicated beach volleyball court. Official home of the city open championships.",
  },
  {
    id: 5,
    name: "Harbor Sports Club",
    location: "12 Waterfront Dr, Harbor",
    rating: 4.5,
    reviews: 98,
    sports: ["Swimming", "Water Polo", "Rowing"],
    priceFrom: 40,
    image:
      "https://images.unsplash.com/photo-1530549387789-4c1017266635?w=800&h=520&fit=crop&auto=format",
    tag: null,
    courts: 4,
    hours: "07:00 – 21:00",
    description:
      "An exclusive waterfront club with panoramic harbor views. Competition-grade 50m outdoor pool, heated indoor training pool, and direct water access for rowing and sculling.",
  },
  {
    id: 6,
    name: "Northgate Stadium",
    location: "77 North Ring Rd, Northgate",
    rating: 4.6,
    reviews: 163,
    sports: ["Football", "Rugby", "Athletics"],
    priceFrom: 28,
    image:
      "https://images.unsplash.com/photo-1540497077202-7c8a3999166f?w=800&h=520&fit=crop&auto=format",
    tag: null,
    courts: 5,
    hours: "08:00 – 22:00",
    description:
      "A classic stadium venue with full-size grass and 3G artificial pitches, a dedicated rugby ground with electronic scoreboard, and a synthetic athletics track with full facilities.",
  },
];

type Center = (typeof CENTERS)[0];

// ─── Constants ────────────────────────────────────────────────────────────────

const DAY_SHORT = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTH_SHORT = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

const ALL_SLOTS = [
  "06:00", "07:00", "08:00", "09:00", "10:00", "11:00",
  "12:00", "13:00", "14:00", "15:00", "16:00", "17:00",
  "18:00", "19:00", "20:00", "21:00",
];

const TAKEN_SLOTS = new Set(["09:00", "10:00", "14:00", "15:00", "19:00"]);

const ALL_SPORTS = [
  "All", "Basketball", "Football", "Tennis",
  "Swimming", "Cricket", "Rugby", "Padel",
];

const MOCK_UPCOMING: BookingData[] = [
  {
    center: CENTERS[3],
    sport: "Tennis",
    date: (() => { const d = new Date(); d.setDate(d.getDate() + 2); return d; })(),
    slot: "10:00",
    name: "Alex Rivera",
    phone: "+1 555 010 2030",
    ref: "BSL-20847",
  },
  {
    center: CENTERS[0],
    sport: "Basketball",
    date: (() => { const d = new Date(); d.setDate(d.getDate() + 5); return d; })(),
    slot: "18:00",
    name: "Alex Rivera",
    phone: "+1 555 010 2030",
    ref: "BSL-20901",
  },
];

const MOCK_PAST: BookingData[] = [
  {
    center: CENTERS[1],
    sport: "Swimming",
    date: (() => { const d = new Date(); d.setDate(d.getDate() - 8); return d; })(),
    slot: "07:00",
    name: "Alex Rivera",
    phone: "+1 555 010 2030",
    ref: "BSL-20611",
  },
  {
    center: CENTERS[2],
    sport: "Football",
    date: (() => { const d = new Date(); d.setDate(d.getDate() - 14); return d; })(),
    slot: "17:00",
    name: "Alex Rivera",
    phone: "+1 555 010 2030",
    ref: "BSL-20559",
  },
  {
    center: CENTERS[4],
    sport: "Rowing",
    date: (() => { const d = new Date(); d.setDate(d.getDate() - 21); return d; })(),
    slot: "06:00",
    name: "Alex Rivera",
    phone: "+1 555 010 2030",
    ref: "BSL-20412",
  },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getNext7Days(): Date[] {
  const today = new Date();
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(today);
    d.setDate(today.getDate() + i);
    return d;
  });
}

function fmtDate(d: Date) {
  return `${DAY_SHORT[d.getDay()]}, ${MONTH_SHORT[d.getMonth()]} ${d.getDate()}`;
}

function fmtSlotEnd(slot: string) {
  return `${String(Number(slot.split(":")[0]) + 1).padStart(2, "0")}:00`;
}

function genRef() {
  return `BSL-${Math.floor(20000 + Math.random() * 9999)}`;
}

function initials(name: string) {
  return name
    .split(" ")
    .map((w) => w[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

// ─── Shared components ────────────────────────────────────────────────────────

function Navbar({
  user,
  onNavigate,
  onLogout,
}: {
  user: AuthUser | null;
  onNavigate: (p: Page) => void;
  onLogout: () => void;
}) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-border bg-background/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <button
          onClick={() => onNavigate("landing")}
          className="text-2xl font-black tracking-tight"
          style={{ fontFamily: "'Barlow Condensed', sans-serif" }}
        >
          BOOKS<span className="text-[#c9ff47]">ALL</span>
        </button>

        <nav className="hidden md:flex items-center gap-6 text-sm text-muted-foreground">
          <button
            onClick={() => onNavigate("landing")}
            className="hover:text-foreground transition-colors"
          >
            Centers
          </button>
          {user && (
            <button
              onClick={() => onNavigate("my-bookings")}
              className="hover:text-foreground transition-colors"
            >
              My Bookings
            </button>
          )}
        </nav>

        {user ? (
          <div className="relative">
            <button
              onClick={() => setMenuOpen((v) => !v)}
              className="flex items-center gap-2 bg-card border border-border rounded-full pl-1 pr-3 py-1 hover:border-foreground/30 transition-colors"
            >
              <span className="w-7 h-7 rounded-full bg-[#c9ff47] text-black text-xs font-black flex items-center justify-center">
                {initials(user.name)}
              </span>
              <span className="text-sm font-semibold hidden sm:block">{user.name.split(" ")[0]}</span>
              <ChevronDown size={14} className="text-muted-foreground" />
            </button>
            {menuOpen && (
              <div className="absolute right-0 top-12 bg-card border border-border rounded-2xl shadow-xl shadow-black/40 w-52 overflow-hidden">
                <div className="px-4 py-3 border-b border-border">
                  <p className="text-sm font-semibold">{user.name}</p>
                  <p className="text-xs text-muted-foreground">{user.email}</p>
                </div>
                <button
                  onClick={() => { setMenuOpen(false); onNavigate("my-bookings"); }}
                  className="w-full flex items-center gap-2 px-4 py-3 text-sm text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                >
                  <Ticket size={14} />
                  My Bookings
                </button>
                <button
                  onClick={() => { setMenuOpen(false); onLogout(); }}
                  className="w-full flex items-center gap-2 px-4 py-3 text-sm text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                >
                  <LogOut size={14} />
                  Sign out
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <button
              onClick={() => onNavigate("login")}
              className="text-sm font-semibold text-muted-foreground hover:text-foreground transition-colors px-3 py-2"
            >
              Log in
            </button>
            <button
              onClick={() => onNavigate("signup")}
              className="bg-[#c9ff47] text-black text-sm font-bold px-4 py-2 rounded-full hover:bg-[#d9ff6b] transition-colors"
            >
              Sign up
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

function TagPill({ tag }: { tag: "Popular" | "New" | "Top Rated" }) {
  const classes =
    tag === "Top Rated"
      ? "bg-[#c9ff47] text-black"
      : tag === "New"
      ? "bg-blue-500 text-white"
      : "bg-black/60 text-white backdrop-blur-sm";
  return (
    <span
      className={`absolute top-3 left-3 text-xs font-bold px-2.5 py-1 rounded-full ${classes}`}
    >
      {tag}
    </span>
  );
}

// ─── Landing Page ─────────────────────────────────────────────────────────────

function LandingPage({
  user,
  onSelect,
  onNavigate,
}: {
  user: AuthUser | null;
  onSelect: (c: Center) => void;
  onNavigate: (p: Page) => void;
}) {
  const [filter, setFilter] = useState("All");
  const [query, setQuery] = useState("");

  const filtered = CENTERS.filter((c) => {
    const matchesSport = filter === "All" || c.sports.includes(filter);
    const matchesQuery =
      !query ||
      c.name.toLowerCase().includes(query.toLowerCase()) ||
      c.location.toLowerCase().includes(query.toLowerCase());
    return matchesSport && matchesQuery;
  });

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Hero */}
      <section className="pt-32 pb-12 px-6 max-w-7xl mx-auto">
        <div className="inline-flex items-center gap-2 bg-[#c9ff47]/10 border border-[#c9ff47]/30 rounded-full px-3 py-1 mb-6">
          <span className="w-2 h-2 rounded-full bg-[#c9ff47] animate-pulse" />
          <span className="text-xs font-semibold text-[#c9ff47] tracking-widest uppercase">
            Live availability
          </span>
        </div>
        <h1
          className="text-7xl md:text-8xl font-black leading-none tracking-tighter mb-4 uppercase"
          style={{ fontFamily: "'Barlow Condensed', sans-serif" }}
        >
          Book Your<br />
          <span className="text-[#c9ff47]">Next Game.</span>
        </h1>
        <p className="text-lg text-muted-foreground max-w-lg mb-10">
          Discover and instantly reserve the best sports facilities near you —
          courts, pitches, pools, and more.
        </p>

        <div className="flex flex-col sm:flex-row gap-3 max-w-lg">
          <div className="relative flex-1">
            <Search
              size={16}
              className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground"
            />
            <input
              type="text"
              placeholder="Search by name or location…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full bg-card border border-border rounded-2xl pl-11 pr-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-[#c9ff47]/50 transition-colors"
            />
          </div>
          {!user && (
            <button
              onClick={() => onNavigate("signup")}
              className="bg-[#c9ff47] text-black font-bold px-6 py-3 rounded-2xl hover:bg-[#d9ff6b] transition-colors shrink-0 text-sm"
            >
              Get started free
            </button>
          )}
        </div>
      </section>

      {/* Sport filters */}
      <section className="px-6 mb-8">
        <div className="max-w-7xl mx-auto flex gap-2 flex-wrap">
          {ALL_SPORTS.map((s) => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`px-4 py-1.5 rounded-full text-sm font-semibold transition-all ${
                filter === s
                  ? "bg-[#c9ff47] text-black"
                  : "bg-card border border-border text-muted-foreground hover:border-foreground/40 hover:text-foreground"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </section>

      {/* Grid */}
      <section className="px-6 pb-24 max-w-7xl mx-auto">
        {filtered.length === 0 && (
          <div className="text-center py-20 text-muted-foreground">
            <p className="text-lg font-semibold">No centers found</p>
            <p className="text-sm mt-1">Try a different sport or search term</p>
          </div>
        )}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((center) => (
            <button
              key={center.id}
              onClick={() => onSelect(center)}
              className="group text-left bg-card border border-border rounded-2xl overflow-hidden hover:border-[#c9ff47]/50 transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl hover:shadow-black/60"
            >
              <div className="relative h-48 bg-muted overflow-hidden">
                <img
                  src={center.image}
                  alt={center.name}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                />
                {center.tag && <TagPill tag={center.tag} />}
                <div className="absolute bottom-3 right-3 bg-black/70 backdrop-blur-sm text-white text-xs font-bold px-2.5 py-1 rounded-lg">
                  from ${center.priceFrom}/hr
                </div>
              </div>
              <div className="p-4">
                <div className="flex items-start justify-between mb-1">
                  <h3 className="font-bold text-base leading-tight">{center.name}</h3>
                  <div className="flex items-center gap-1 shrink-0 ml-2">
                    <Star size={12} className="fill-[#c9ff47] text-[#c9ff47]" />
                    <span className="text-sm font-semibold">{center.rating}</span>
                    <span className="text-xs text-muted-foreground">({center.reviews})</span>
                  </div>
                </div>
                <div className="flex items-center gap-1 text-muted-foreground text-xs mb-3">
                  <MapPin size={11} />
                  <span>{center.location}</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex gap-1.5 flex-wrap">
                    {center.sports.map((s) => (
                      <span
                        key={s}
                        className="text-xs px-2 py-0.5 rounded-md bg-muted text-muted-foreground"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                  <ChevronRight
                    size={14}
                    className="text-muted-foreground group-hover:text-[#c9ff47] transition-colors shrink-0 ml-2"
                  />
                </div>
              </div>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}

// ─── Auth split layout ────────────────────────────────────────────────────────

function AuthLayout({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-background grid md:grid-cols-2">
      {/* Left panel */}
      <div className="hidden md:flex flex-col relative overflow-hidden bg-[#0d0d0d]">
        <img
          src="https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=900&h=1200&fit=crop&auto=format"
          alt="Athletes on track"
          className="absolute inset-0 w-full h-full object-cover opacity-50"
        />
        <div className="absolute inset-0 bg-gradient-to-br from-black/60 via-transparent to-[#c9ff47]/10" />
        <div className="relative z-10 flex flex-col h-full p-12">
          <span
            className="text-2xl font-black tracking-tight text-white"
            style={{ fontFamily: "'Barlow Condensed', sans-serif" }}
          >
            BOOKS<span className="text-[#c9ff47]">ALL</span>
          </span>
          <div className="mt-auto">
            <blockquote className="text-white/80 text-lg leading-relaxed max-w-sm italic">
              "The easiest way to find a court, pick a time, and just play."
            </blockquote>
            <div className="flex items-center gap-3 mt-4">
              <div className="flex -space-x-2">
                {["#e63946", "#457b9d", "#2a9d8f"].map((c) => (
                  <span
                    key={c}
                    className="w-8 h-8 rounded-full border-2 border-black flex items-center justify-center text-xs font-bold text-white"
                    style={{ background: c }}
                  />
                ))}
              </div>
              <span className="text-white/60 text-sm">12,000+ bookings made</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right panel */}
      <div className="flex items-center justify-center px-6 py-16 md:py-0">
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <span
            className="block md:hidden text-2xl font-black tracking-tight mb-8"
            style={{ fontFamily: "'Barlow Condensed', sans-serif" }}
          >
            BOOKS<span className="text-[#c9ff47]">ALL</span>
          </span>
          <h2
            className="text-4xl font-black uppercase tracking-tight mb-1"
            style={{ fontFamily: "'Barlow Condensed', sans-serif" }}
          >
            {title}
          </h2>
          <p className="text-muted-foreground text-sm mb-8">{subtitle}</p>
          {children}
        </div>
      </div>
    </div>
  );
}

// ─── Login Page ───────────────────────────────────────────────────────────────

function LoginPage({
  onLogin,
  onNavigate,
}: {
  onLogin: (user: AuthUser) => void;
  onNavigate: (p: Page) => void;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!email || !password) {
      setError("Please fill in all fields.");
      return;
    }
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      onLogin({
        name: "Alex Rivera",
        email,
        avatar: "",
      });
    }, 800);
  }

  return (
    <AuthLayout
      title="Welcome back."
      subtitle="Log in to manage your bookings and reserve your next court."
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="text-xs font-bold uppercase tracking-widest text-muted-foreground block mb-1.5">
            Email
          </label>
          <div className="relative">
            <Mail size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full bg-input-background border border-border rounded-xl pl-9 pr-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:border-[#c9ff47]/50 transition-colors"
            />
          </div>
        </div>

        <div>
          <label className="text-xs font-bold uppercase tracking-widest text-muted-foreground block mb-1.5">
            Password
          </label>
          <div className="relative">
            <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              type={showPw ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-input-background border border-border rounded-xl pl-9 pr-10 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:border-[#c9ff47]/50 transition-colors"
            />
            <button
              type="button"
              onClick={() => setShowPw((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
            >
              {showPw ? <EyeOff size={14} /> : <Eye size={14} />}
            </button>
          </div>
        </div>

        <div className="flex justify-end">
          <button type="button" className="text-xs text-[#c9ff47] hover:underline">
            Forgot password?
          </button>
        </div>

        {error && (
          <div className="flex items-center gap-2 bg-destructive/10 border border-destructive/30 rounded-xl px-3 py-2.5 text-sm text-destructive">
            <X size={14} />
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 rounded-xl font-bold text-sm bg-[#c9ff47] text-black hover:bg-[#d9ff6b] transition-all disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98]"
        >
          {loading ? "Signing in…" : "Log in"}
        </button>

        <div className="relative flex items-center gap-3 py-2">
          <div className="flex-1 h-px bg-border" />
          <span className="text-xs text-muted-foreground">or</span>
          <div className="flex-1 h-px bg-border" />
        </div>

        <button
          type="button"
          className="w-full py-2.5 rounded-xl text-sm font-semibold border border-border text-foreground hover:border-foreground/30 transition-colors flex items-center justify-center gap-2"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
          </svg>
          Continue with Google
        </button>

        <p className="text-center text-sm text-muted-foreground pt-2">
          {"Don't have an account? "}
          <button
            type="button"
            onClick={() => onNavigate("signup")}
            className="text-[#c9ff47] font-semibold hover:underline"
          >
            Sign up
          </button>
        </p>
      </form>
    </AuthLayout>
  );
}

// ─── Signup Page ──────────────────────────────────────────────────────────────

function SignupPage({
  onLogin,
  onNavigate,
}: {
  onLogin: (user: AuthUser) => void;
  onNavigate: (p: Page) => void;
}) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [agree, setAgree] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!name || !email || !password) {
      setError("Please fill in all fields.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (!agree) {
      setError("Please accept the terms to continue.");
      return;
    }
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      onLogin({ name, email, avatar: "" });
    }, 900);
  }

  const strength =
    password.length === 0
      ? 0
      : password.length < 6
      ? 1
      : password.length < 10
      ? 2
      : 3;

  const strengthLabel = ["", "Weak", "Fair", "Strong"][strength];
  const strengthColor = ["", "#ef4444", "#f59e0b", "#c9ff47"][strength];

  return (
    <AuthLayout
      title="Create account."
      subtitle="Join thousands of players booking courts across the city."
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="text-xs font-bold uppercase tracking-widest text-muted-foreground block mb-1.5">
            Full Name
          </label>
          <div className="relative">
            <User size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Jordan Smith"
              className="w-full bg-input-background border border-border rounded-xl pl-9 pr-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:border-[#c9ff47]/50 transition-colors"
            />
          </div>
        </div>

        <div>
          <label className="text-xs font-bold uppercase tracking-widest text-muted-foreground block mb-1.5">
            Email
          </label>
          <div className="relative">
            <Mail size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full bg-input-background border border-border rounded-xl pl-9 pr-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:border-[#c9ff47]/50 transition-colors"
            />
          </div>
        </div>

        <div>
          <label className="text-xs font-bold uppercase tracking-widest text-muted-foreground block mb-1.5">
            Password
          </label>
          <div className="relative">
            <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              type={showPw ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Min. 8 characters"
              className="w-full bg-input-background border border-border rounded-xl pl-9 pr-10 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:border-[#c9ff47]/50 transition-colors"
            />
            <button
              type="button"
              onClick={() => setShowPw((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
            >
              {showPw ? <EyeOff size={14} /> : <Eye size={14} />}
            </button>
          </div>
          {password.length > 0 && (
            <div className="mt-2 flex items-center gap-2">
              <div className="flex gap-1 flex-1">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="h-1 flex-1 rounded-full transition-all"
                    style={{
                      background: i <= strength ? strengthColor : "rgba(255,255,255,0.1)",
                    }}
                  />
                ))}
              </div>
              <span className="text-xs font-semibold" style={{ color: strengthColor }}>
                {strengthLabel}
              </span>
            </div>
          )}
        </div>

        <label className="flex items-start gap-2.5 cursor-pointer">
          <div
            onClick={() => setAgree((v) => !v)}
            className={`mt-0.5 w-4 h-4 rounded border flex items-center justify-center transition-all shrink-0 ${
              agree ? "bg-[#c9ff47] border-[#c9ff47]" : "border-border"
            }`}
          >
            {agree && (
              <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                <path d="M1 4l3 3 5-6" stroke="black" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            )}
          </div>
          <span className="text-sm text-muted-foreground leading-relaxed">
            I agree to the{" "}
            <button type="button" className="text-[#c9ff47] hover:underline">
              Terms of Service
            </button>{" "}
            and{" "}
            <button type="button" className="text-[#c9ff47] hover:underline">
              Privacy Policy
            </button>
          </span>
        </label>

        {error && (
          <div className="flex items-center gap-2 bg-destructive/10 border border-destructive/30 rounded-xl px-3 py-2.5 text-sm text-destructive">
            <X size={14} />
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 rounded-xl font-bold text-sm bg-[#c9ff47] text-black hover:bg-[#d9ff6b] transition-all disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98]"
        >
          {loading ? "Creating account…" : "Create account"}
        </button>

        <p className="text-center text-sm text-muted-foreground pt-2">
          Already have an account?{" "}
          <button
            type="button"
            onClick={() => onNavigate("login")}
            className="text-[#c9ff47] font-semibold hover:underline"
          >
            Log in
          </button>
        </p>
      </form>
    </AuthLayout>
  );
}

// ─── Detail Page ──────────────────────────────────────────────────────────────

function DetailPage({
  center,
  user,
  onBack,
  onBooked,
  onNavigate,
}: {
  center: Center;
  user: AuthUser | null;
  onBack: () => void;
  onBooked: (b: BookingData) => void;
  onNavigate: (p: Page) => void;
}) {
  const days = getNext7Days();
  const [selectedDay, setSelectedDay] = useState(0);
  const [selectedSport, setSelectedSport] = useState(center.sports[0]);
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null);
  const [name, setName] = useState(user?.name ?? "");
  const [phone, setPhone] = useState("");

  function handleBook() {
    if (!selectedSlot || !name.trim() || !phone.trim()) return;
    if (!user) {
      onNavigate("login");
      return;
    }
    onBooked({
      center,
      sport: selectedSport,
      date: days[selectedDay],
      slot: selectedSlot,
      name,
      phone,
      ref: genRef(),
    });
  }

  const canBook = !!selectedSlot && name.trim().length > 0 && phone.trim().length > 0;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-40 bg-background/90 backdrop-blur-md border-b border-border">
        <div className="max-w-5xl mx-auto px-6 h-16 flex items-center gap-3">
          <button
            onClick={onBack}
            className="flex items-center gap-1.5 text-muted-foreground hover:text-foreground transition-colors text-sm"
          >
            <ArrowLeft size={15} />
            <span>Centers</span>
          </button>
          <span className="text-muted-foreground text-sm">/</span>
          <span className="text-sm font-semibold truncate">{center.name}</span>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-6 py-8">
        {/* Hero */}
        <div className="relative h-64 md:h-80 rounded-2xl overflow-hidden bg-muted mb-8">
          <img src={center.image} alt={center.name} className="w-full h-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/25 to-transparent" />
          <div className="absolute bottom-6 left-6 right-6 flex items-end justify-between gap-4">
            <div>
              <h1
                className="text-4xl font-black text-white uppercase tracking-tight leading-none mb-2"
                style={{ fontFamily: "'Barlow Condensed', sans-serif" }}
              >
                {center.name}
              </h1>
              <div className="flex items-center gap-4 flex-wrap">
                <div className="flex items-center gap-1 text-white/80 text-sm">
                  <MapPin size={13} />
                  <span>{center.location}</span>
                </div>
                <div className="flex items-center gap-1">
                  <Star size={13} className="fill-[#c9ff47] text-[#c9ff47]" />
                  <span className="text-white font-semibold text-sm">{center.rating}</span>
                  <span className="text-white/60 text-sm">({center.reviews})</span>
                </div>
              </div>
            </div>
            <div className="bg-[#c9ff47] text-black text-sm font-black px-3 py-1.5 rounded-xl shrink-0">
              from ${center.priceFrom}/hr
            </div>
          </div>
        </div>

        {/* Info strip */}
        <div className="grid grid-cols-3 gap-3 mb-8">
          {(
            [
              { icon: Clock, label: "Hours", value: center.hours },
              { icon: Users, label: "Courts", value: `${center.courts} courts` },
              { icon: Calendar, label: "Booking", value: "Instant confirm" },
            ] as const
          ).map(({ icon: Icon, label, value }) => (
            <div key={label} className="bg-card border border-border rounded-xl px-4 py-3 flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-[#c9ff47]/10 flex items-center justify-center shrink-0">
                <Icon size={16} className="text-[#c9ff47]" />
              </div>
              <div>
                <p className="text-muted-foreground text-xs">{label}</p>
                <p className="font-semibold text-sm">{value}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="grid md:grid-cols-5 gap-8">
          {/* Booking controls */}
          <div className="md:col-span-3 space-y-8">
            {/* Sport */}
            <div>
              <h3 className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-3">
                Select Sport
              </h3>
              <div className="flex gap-2 flex-wrap">
                {center.sports.map((s) => (
                  <button
                    key={s}
                    onClick={() => setSelectedSport(s)}
                    className={`px-4 py-2 rounded-full text-sm font-semibold border transition-all ${
                      selectedSport === s
                        ? "bg-[#c9ff47] border-[#c9ff47] text-black"
                        : "border-border text-muted-foreground hover:border-foreground/40 hover:text-foreground"
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {/* Date */}
            <div>
              <h3 className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-3">
                Select Date
              </h3>
              <div className="grid grid-cols-7 gap-1.5">
                {days.map((day, i) => (
                  <button
                    key={i}
                    onClick={() => { setSelectedDay(i); setSelectedSlot(null); }}
                    className={`flex flex-col items-center py-2.5 rounded-xl border transition-all ${
                      selectedDay === i
                        ? "bg-[#c9ff47] border-[#c9ff47] text-black"
                        : "border-border text-muted-foreground hover:border-foreground/40 hover:text-foreground"
                    }`}
                  >
                    <span className="text-xs font-semibold">{DAY_SHORT[day.getDay()]}</span>
                    <span className={`text-lg font-black leading-tight ${selectedDay === i ? "text-black" : "text-foreground"}`}>
                      {day.getDate()}
                    </span>
                    <span className="text-xs">{MONTH_SHORT[day.getMonth()]}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Time slots */}
            <div>
              <h3 className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-3">
                Select Time Slot
              </h3>
              <div className="grid grid-cols-4 gap-2">
                {ALL_SLOTS.map((slot) => {
                  const taken = TAKEN_SLOTS.has(slot);
                  const active = selectedSlot === slot;
                  return (
                    <button
                      key={slot}
                      disabled={taken}
                      onClick={() => setSelectedSlot(active ? null : slot)}
                      className={`py-2.5 rounded-xl text-sm font-semibold border transition-all ${
                        taken
                          ? "border-border/30 text-muted-foreground/30 cursor-not-allowed line-through"
                          : active
                          ? "bg-[#c9ff47] border-[#c9ff47] text-black"
                          : "border-border text-muted-foreground hover:border-foreground/40 hover:text-foreground"
                      }`}
                    >
                      {slot}
                    </button>
                  );
                })}
              </div>
              <div className="flex gap-5 mt-3 text-xs text-muted-foreground">
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-sm bg-[#c9ff47]" /> Selected
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-sm border border-border" /> Available
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-sm bg-muted/40" /> Taken
                </span>
              </div>
            </div>

            {/* About */}
            <div className="pt-6 border-t border-border">
              <h3 className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-3">
                About This Venue
              </h3>
              <p className="text-muted-foreground text-sm leading-relaxed">{center.description}</p>
            </div>
          </div>

          {/* Booking form */}
          <div className="md:col-span-2">
            <div className="bg-card border border-border rounded-2xl p-5 sticky top-24">
              <h3
                className="font-black text-xl uppercase tracking-tight mb-5"
                style={{ fontFamily: "'Barlow Condensed', sans-serif" }}
              >
                Your Booking
              </h3>

              <div className="space-y-3 pb-5 border-b border-border mb-5 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Sport</span>
                  <span className="font-semibold">{selectedSport}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Date</span>
                  <span className="font-semibold">{fmtDate(days[selectedDay])}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Time</span>
                  <span className={`font-semibold ${selectedSlot ? "text-[#c9ff47]" : "text-muted-foreground/40"}`}>
                    {selectedSlot
                      ? `${selectedSlot} – ${fmtSlotEnd(selectedSlot)}`
                      : "Not selected"}
                  </span>
                </div>
                <div className="flex justify-between font-bold">
                  <span className="text-muted-foreground">Total</span>
                  <span>${center.priceFrom}</span>
                </div>
              </div>

              {!user && (
                <div className="bg-[#c9ff47]/10 border border-[#c9ff47]/30 rounded-xl p-3 mb-4 text-sm text-[#c9ff47]">
                  <span className="font-semibold">Log in</span> to complete your booking.
                </div>
              )}

              <div className="space-y-3 mb-5">
                <div>
                  <label className="text-xs font-bold uppercase tracking-widest text-muted-foreground block mb-1.5">
                    Full Name
                  </label>
                  <div className="relative">
                    <User size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="Jordan Smith"
                      className="w-full bg-input-background border border-border rounded-xl pl-9 pr-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:border-[#c9ff47]/50 transition-colors"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-xs font-bold uppercase tracking-widest text-muted-foreground block mb-1.5">
                    Phone Number
                  </label>
                  <div className="relative">
                    <Phone size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                    <input
                      type="tel"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="+1 555 000 0000"
                      className="w-full bg-input-background border border-border rounded-xl pl-9 pr-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:border-[#c9ff47]/50 transition-colors"
                    />
                  </div>
                </div>
              </div>

              <button
                onClick={handleBook}
                disabled={!canBook}
                className="w-full py-3 rounded-xl font-bold text-sm transition-all disabled:opacity-30 disabled:cursor-not-allowed bg-[#c9ff47] text-black hover:bg-[#d9ff6b] active:scale-[0.98]"
              >
                {!user
                  ? "Log in to book"
                  : canBook
                  ? "Confirm Booking"
                  : "Complete the form"}
              </button>
              <p className="text-xs text-muted-foreground text-center mt-3">
                Free cancellation up to 2 hours before
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Booking Confirmed Page ───────────────────────────────────────────────────

function BookingConfirmedPage({
  booking,
  onNavigate,
}: {
  booking: BookingData;
  onNavigate: (p: Page) => void;
}) {
  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Slim header */}
      <header className="border-b border-border px-6 h-16 flex items-center">
        <span
          className="text-2xl font-black tracking-tight"
          style={{ fontFamily: "'Barlow Condensed', sans-serif" }}
        >
          BOOKS<span className="text-[#c9ff47]">ALL</span>
        </span>
      </header>

      <div className="flex-1 flex items-center justify-center px-6 py-16">
        <div className="w-full max-w-lg">
          {/* Icon */}
          <div className="flex justify-center mb-8">
            <div className="relative">
              <div className="w-24 h-24 rounded-full bg-[#c9ff47]/15 border border-[#c9ff47]/30 flex items-center justify-center">
                <CheckCircle2 size={44} className="text-[#c9ff47]" />
              </div>
              {/* Decorative rings */}
              <div className="absolute -inset-3 rounded-full border border-[#c9ff47]/10" />
              <div className="absolute -inset-6 rounded-full border border-[#c9ff47]/05" />
            </div>
          </div>

          <div className="text-center mb-8">
            <h1
              className="text-5xl font-black uppercase tracking-tight mb-2"
              style={{ fontFamily: "'Barlow Condensed', sans-serif" }}
            >
              You&apos;re booked!
            </h1>
            <p className="text-muted-foreground">
              Your reservation is confirmed. A summary has been sent to your email.
            </p>
          </div>

          {/* Receipt card */}
          <div className="bg-card border border-border rounded-2xl overflow-hidden mb-6">
            {/* Center image strip */}
            <div className="relative h-32 overflow-hidden bg-muted">
              <img
                src={booking.center.image}
                alt={booking.center.name}
                className="w-full h-full object-cover opacity-60"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-card/80 to-transparent" />
              <div className="absolute bottom-3 left-4">
                <p className="font-bold text-sm">{booking.center.name}</p>
                <p className="text-xs text-muted-foreground">{booking.center.location}</p>
              </div>
              {/* Booking ref badge */}
              <div className="absolute top-3 right-3 bg-[#c9ff47] text-black text-xs font-black px-2.5 py-1 rounded-lg">
                {booking.ref}
              </div>
            </div>

            {/* Details */}
            <div className="p-5 space-y-3 text-sm">
              {[
                ["Sport", booking.sport],
                ["Date", fmtDate(booking.date)],
                ["Time", `${booking.slot} – ${fmtSlotEnd(booking.slot)}`],
                ["Duration", "1 hour"],
                ["Name", booking.name],
                ["Contact", booking.phone],
              ].map(([label, value]) => (
                <div key={label} className="flex justify-between items-center">
                  <span className="text-muted-foreground">{label}</span>
                  <span className="font-semibold">{value}</span>
                </div>
              ))}
              <div className="border-t border-border pt-3 flex justify-between items-center font-bold">
                <span className="text-muted-foreground">Total Paid</span>
                <span className="text-[#c9ff47] text-base">${booking.center.priceFrom}</span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => onNavigate("my-bookings")}
              className="py-3 rounded-xl font-bold text-sm border border-border text-foreground hover:border-foreground/40 transition-colors"
            >
              View my bookings
            </button>
            <button
              onClick={() => onNavigate("landing")}
              className="py-3 rounded-xl font-bold text-sm bg-[#c9ff47] text-black hover:bg-[#d9ff6b] transition-colors"
            >
              Book another
            </button>
          </div>

          <p className="text-xs text-muted-foreground text-center mt-5">
            Need to cancel?{" "}
            <button className="text-[#c9ff47] hover:underline">Contact support</button>
            {" "}up to 2 hours before your slot.
          </p>
        </div>
      </div>
    </div>
  );
}

// ─── My Bookings Page ─────────────────────────────────────────────────────────

function MyBookingsPage({
  user,
  latestBooking,
  onNavigate,
}: {
  user: AuthUser;
  latestBooking: BookingData | null;
  onNavigate: (p: Page) => void;
}) {
  const [tab, setTab] = useState<"upcoming" | "past">("upcoming");

  const upcoming = latestBooking
    ? [latestBooking, ...MOCK_UPCOMING]
    : MOCK_UPCOMING;

  const past = MOCK_PAST;

  const items = tab === "upcoming" ? upcoming : past;

  return (
    <div className="min-h-screen bg-background text-foreground pt-16">
      <div className="max-w-3xl mx-auto px-6 py-10">
        <div className="flex items-start justify-between mb-8">
          <div>
            <h1
              className="text-5xl font-black uppercase tracking-tight leading-none mb-1"
              style={{ fontFamily: "'Barlow Condensed', sans-serif" }}
            >
              My Bookings
            </h1>
            <p className="text-muted-foreground text-sm">{user.name} · {user.email}</p>
          </div>
          <button
            onClick={() => onNavigate("landing")}
            className="bg-[#c9ff47] text-black font-bold text-sm px-4 py-2 rounded-full hover:bg-[#d9ff6b] transition-colors shrink-0"
          >
            + New booking
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-card border border-border rounded-xl p-1 mb-6 w-fit">
          {(["upcoming", "past"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all capitalize ${
                tab === t
                  ? "bg-[#c9ff47] text-black"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {t}
              <span
                className={`ml-2 text-xs font-black ${
                  tab === t ? "text-black/60" : "text-muted-foreground/60"
                }`}
              >
                {t === "upcoming" ? upcoming.length : past.length}
              </span>
            </button>
          ))}
        </div>

        {/* Booking cards */}
        {items.length === 0 ? (
          <div className="text-center py-20 border border-border rounded-2xl">
            <Ticket size={32} className="text-muted-foreground mx-auto mb-3 opacity-40" />
            <p className="font-semibold text-muted-foreground">No {tab} bookings</p>
            {tab === "upcoming" && (
              <button
                onClick={() => onNavigate("landing")}
                className="mt-4 text-sm text-[#c9ff47] hover:underline font-semibold"
              >
                Browse centers →
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {items.map((b, i) => (
              <BookingCard
                key={b.ref + i}
                booking={b}
                upcoming={tab === "upcoming"}
                isNew={i === 0 && tab === "upcoming" && !!latestBooking}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function BookingCard({
  booking,
  upcoming,
  isNew,
}: {
  booking: BookingData;
  upcoming: boolean;
  isNew: boolean;
}) {
  return (
    <div
      className={`bg-card border rounded-2xl overflow-hidden flex flex-col sm:flex-row transition-all ${
        isNew ? "border-[#c9ff47]/50 shadow-lg shadow-[#c9ff47]/5" : "border-border"
      }`}
    >
      {/* Image */}
      <div className="relative h-36 sm:h-auto sm:w-40 bg-muted shrink-0 overflow-hidden">
        <img
          src={booking.center.image}
          alt={booking.center.name}
          className="w-full h-full object-cover"
        />
        {isNew && (
          <div className="absolute top-2 left-2 bg-[#c9ff47] text-black text-xs font-black px-2 py-0.5 rounded-full">
            New
          </div>
        )}
      </div>

      {/* Info */}
      <div className="flex-1 p-4 flex flex-col justify-between gap-3">
        <div>
          <div className="flex items-start justify-between gap-2 mb-1">
            <h3 className="font-bold text-base leading-tight">{booking.center.name}</h3>
            <span
              className={`shrink-0 text-xs font-bold px-2.5 py-1 rounded-full ${
                upcoming
                  ? "bg-[#c9ff47]/15 text-[#c9ff47]"
                  : "bg-muted text-muted-foreground"
              }`}
            >
              {upcoming ? "Upcoming" : "Completed"}
            </span>
          </div>
          <p className="text-xs text-muted-foreground flex items-center gap-1">
            <MapPin size={11} />
            {booking.center.location}
          </p>
        </div>

        <div className="grid grid-cols-3 gap-3 text-sm">
          <div>
            <p className="text-xs text-muted-foreground mb-0.5">Sport</p>
            <p className="font-semibold">{booking.sport}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground mb-0.5">Date</p>
            <p className="font-semibold">{fmtDate(booking.date)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground mb-0.5">Time</p>
            <p className="font-semibold">{booking.slot}</p>
          </div>
        </div>

        <div className="flex items-center justify-between pt-2 border-t border-border">
          <span className="text-xs text-muted-foreground font-mono">{booking.ref}</span>
          {upcoming && (
            <button className="text-xs text-destructive hover:underline font-semibold">
              Cancel
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Root ─────────────────────────────────────────────────────────────────────

export default function App() {
  const [page, setPage] = useState<Page>("landing");
  const [user, setUser] = useState<AuthUser | null>(null);
  const [selectedCenter, setSelectedCenter] = useState<Center | null>(null);
  const [lastBooking, setLastBooking] = useState<BookingData | null>(null);

  function handleLogin(u: AuthUser) {
    setUser(u);
    setPage("landing");
  }

  function handleLogout() {
    setUser(null);
    setPage("landing");
  }

  function handleSelectCenter(c: Center) {
    setSelectedCenter(c);
    setPage("detail");
  }

  function handleBooked(b: BookingData) {
    setLastBooking(b);
    setPage("confirmed");
  }

  function navigate(p: Page) {
    setPage(p);
  }

  // Pages that don't use the global Navbar
  const standalonePages: Page[] = ["login", "signup", "confirmed"];

  return (
    <>
      {!standalonePages.includes(page) && (
        <Navbar user={user} onNavigate={navigate} onLogout={handleLogout} />
      )}

      {page === "landing" && (
        <LandingPage user={user} onSelect={handleSelectCenter} onNavigate={navigate} />
      )}

      {page === "login" && (
        <LoginPage onLogin={handleLogin} onNavigate={navigate} />
      )}

      {page === "signup" && (
        <SignupPage onLogin={handleLogin} onNavigate={navigate} />
      )}

      {page === "detail" && selectedCenter && (
        <DetailPage
          center={selectedCenter}
          user={user}
          onBack={() => setPage("landing")}
          onBooked={handleBooked}
          onNavigate={navigate}
        />
      )}

      {page === "confirmed" && lastBooking && (
        <BookingConfirmedPage booking={lastBooking} onNavigate={navigate} />
      )}

      {page === "my-bookings" && user && (
        <MyBookingsPage
          user={user}
          latestBooking={lastBooking}
          onNavigate={navigate}
        />
      )}
    </>
  );
}
