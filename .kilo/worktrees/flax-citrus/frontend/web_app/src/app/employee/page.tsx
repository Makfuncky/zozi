import Link from "next/link";

export default function EmployeeIndexPage() {
  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <h1 className="text-2xl font-semibold text-gray-900">Employee Workspace</h1>
      <p className="mt-2 text-sm text-gray-600">
        Internal employee self-service and oversight surface (diagram §3 route tree).
      </p>
      <nav className="mt-6 flex flex-wrap gap-3">
        <Link
          href="/employee/dashboard"
          className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white"
        >
          Dashboard
        </Link>
        <Link
          href="/employee/profile"
          className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700"
        >
          My Profile
        </Link>
      </nav>
    </main>
  );
}
