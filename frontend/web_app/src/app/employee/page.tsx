import Link from "next/link";

interface PortalSection {
  title: string;
  description: string;
  href: string;
  icon: string;
  status: "active" | "coming-soon";
}

const PORTAL_SECTIONS: PortalSection[] = [
  {
    title: "Dashboard",
    description: "Overview of your tasks, schedule, and key metrics",
    href: "/employee/dashboard",
    icon: "📊",
    status: "active",
  },
  {
    title: "My Profile",
    description: "View and update your personal information and preferences",
    href: "/employee/profile",
    icon: "👤",
    status: "active",
  },
  {
    title: "Employee Management (EMS)",
    description: "Manage employee records, roles, and organizational hierarchy",
    href: "/employee/ems",
    icon: "👥",
    status: "active",
  },
  {
    title: "Payroll",
    description: "View salary history, payslips, and compensation details",
    href: "/employee/payroll",
    icon: "💰",
    status: "active",
  },
  {
    title: "HR Services",
    description: "Submit leave requests, benefits enrollment, and HR tickets",
    href: "/employee/hr",
    icon: "🏢",
    status: "active",
  },
  {
    title: "Time & Attendance",
    description: "Clock in/out, view timesheets, and attendance history",
    href: "/employee/attendance",
    icon: "⏰",
    status: "active",
  },
  {
    title: "Performance",
    description: "Track goals, reviews, and performance evaluations",
    href: "/employee/performance",
    icon: "📈",
    status: "active",
  },
  {
    title: "Training",
    description: "Access learning modules, certifications, and development plans",
    href: "/employee/training",
    icon: "🎓",
    status: "coming-soon",
  },
  {
    title: "Documents",
    description: "Access contracts, policies, and personal document vault",
    href: "/employee/documents",
    icon: "📁",
    status: "coming-soon",
  },
];

export default function EmployeeIndexPage() {
  const activeSections = PORTAL_SECTIONS.filter((s) => s.status === "active");
  const comingSoonSections = PORTAL_SECTIONS.filter((s) => s.status === "coming-soon");

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900">Employee Workspace</h1>
        <p className="mt-2 text-sm text-gray-600">
          Internal employee self-service and oversight surface. Access HR services,
          payroll, and workforce management tools.
        </p>
      </div>

      <section className="mb-8">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-gray-500">
          Quick Access
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {activeSections.map((section) => (
            <Link
              key={section.href}
              href={section.href}
              className="group flex flex-col rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition-all hover:border-blue-300 hover:shadow-md"
            >
              <div className="mb-3 flex items-center gap-3">
                <span className="text-2xl" role="img" aria-label={section.title}>
                  {section.icon}
                </span>
                <h3 className="text-sm font-semibold text-gray-900 group-hover:text-blue-600">
                  {section.title}
                </h3>
              </div>
              <p className="text-xs leading-relaxed text-gray-500">
                {section.description}
              </p>
              <span className="mt-3 text-xs font-medium text-blue-600 group-hover:underline">
                Open →
              </span>
            </Link>
          ))}
        </div>
      </section>

      {comingSoonSections.length > 0 && (
        <section>
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-gray-500">
            Coming Soon
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {comingSoonSections.map((section) => (
              <div
                key={section.href}
                className="flex flex-col rounded-xl border border-dashed border-gray-200 bg-gray-50 p-5 opacity-60"
              >
                <div className="mb-3 flex items-center gap-3">
                  <span className="text-2xl" role="img" aria-label={section.title}>
                    {section.icon}
                  </span>
                  <h3 className="text-sm font-semibold text-gray-600">
                    {section.title}
                  </h3>
                </div>
                <p className="text-xs leading-relaxed text-gray-400">
                  {section.description}
                </p>
                <span className="mt-3 text-xs font-medium text-gray-400">
                  Coming soon
                </span>
              </div>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
