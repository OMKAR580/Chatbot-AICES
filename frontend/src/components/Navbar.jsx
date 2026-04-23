import { NavLink } from "react-router-dom";

const navItems = [
  { to: "/chat", label: "Chat" },
  { to: "/dashboard", label: "Dashboard" },
];

function navClassName({ isActive }) {
  return [
    "neon-button rounded-full px-4 py-2 text-sm font-medium",
    isActive
      ? "border border-ocean/28 bg-ocean/92 text-ink"
      : "border border-transparent text-slate-300 hover:bg-ocean/10 hover:text-white",
  ].join(" ");
}

export default function Navbar() {
  return (
    <header className="flex flex-col gap-4 border-b border-ocean/10 pb-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-ocean/70">AICES</p>
        <h1 className="mt-1 text-2xl font-semibold text-white">Adaptive Concept Studio</h1>
      </div>

      <nav className="flex items-center gap-2 rounded-full border border-ocean/15 bg-canvas/68 p-1.5 shadow-soft backdrop-blur-xl">
        {navItems.map((item) => (
          <NavLink key={item.to} className={navClassName} to={item.to}>
            {item.label}
          </NavLink>
        ))}
      </nav>
    </header>
  );
}
