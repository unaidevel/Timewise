import { NavLink } from "react-router";

const links = [
  { to: "/", label: "Inicio", end: true },
  { to: "/employees", label: "Empleados" },
  { to: "/departments", label: "Departamentos" },
  { to: "/roles", label: "Roles" },
  { to: "/periods", label: "Periodos" },
  { to: "/reports", label: "Mis reportes" },
  { to: "/approvals", label: "Aprobaciones" },
  { to: "/costing-rules", label: "Reglas de coste" },
];

export function Sidebar() {
  return (
    <aside className="hidden w-56 flex-col border-r border-slate-200 bg-white md:flex">
      <div className="border-b border-slate-200 px-5 py-4">
        <h1 className="text-lg font-semibold text-slate-900">TimeWise</h1>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.end}
            className={({ isActive }) =>
              `block rounded-md px-3 py-2 text-sm font-medium ${
                isActive ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100"
              }`
            }
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
