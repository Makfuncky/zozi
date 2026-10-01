import Link from "next/link";
import { Home, Search } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-surface-0 flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <h1 className="text-8xl font-display font-black text-primary/20 mb-4">404</h1>
        <h2 className="text-2xl font-display font-bold text-text-primary mb-3">
          Page Not Found
        </h2>
        <p className="text-text-secondary mb-8">
          The page you are looking for does not exist or has been moved.
        </p>
        <div className="flex items-center justify-center gap-3">
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-primary text-white font-medium hover:bg-primary-dark transition-colors"
          >
            <Home className="w-4 h-4" />
            Go Home
          </Link>
          <Link
            href="/products"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg border border-border text-text-primary font-medium hover:bg-surface-1 transition-colors"
          >
            <Search className="w-4 h-4" />
            Browse Products
          </Link>
        </div>
      </div>
    </div>
  );
}
