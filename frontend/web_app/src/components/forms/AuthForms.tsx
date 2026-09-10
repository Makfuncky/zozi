/**
 * Example form migrated to React Hook Form + Zod
 * This demonstrates the pattern for migrating existing forms
 */

"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/Button";

// Define Zod schema for form validation
const loginSchema = z.object({
  email: z
    .string()
    .min(1, "Email is required")
    .email("Invalid email address"),
  password: z
    .string()
    .min(1, "Password is required")
    .min(8, "Password must be at least 8 characters"),
  rememberMe: z.boolean().default(false),
});

// Infer TypeScript type from schema
type LoginFormData = z.infer<typeof loginSchema>;

interface LoginFormProps {
  onSubmit: (data: LoginFormData) => Promise<void>;
  isLoading?: boolean;
  error?: string;
}

export function LoginForm({ onSubmit, isLoading, error }: LoginFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
      rememberMe: false,
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {error && (
        <div className="rounded-lg bg-danger/10 p-3 text-sm text-danger">
          {error}
        </div>
      )}

      <div>
        <label htmlFor="email" className="block text-sm font-medium text-text">
          Email
        </label>
        <input
          id="email"
          type="email"
          {...register("email")}
          className="mt-1 h-10 w-full rounded-lg border border-border bg-surface-1 px-3 text-sm text-text placeholder:text-text-faint focus:border-primary focus:outline-none"
          placeholder="you@example.com"
        />
        {errors.email && (
          <p className="mt-1 text-xs text-danger">{errors.email.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium text-text">
          Password
        </label>
        <input
          id="password"
          type="password"
          {...register("password")}
          className="mt-1 h-10 w-full rounded-lg border border-border bg-surface-1 px-3 text-sm text-text placeholder:text-text-faint focus:border-primary focus:outline-none"
          placeholder="••••••••"
        />
        {errors.password && (
          <p className="mt-1 text-xs text-danger">{errors.password.message}</p>
        )}
      </div>

      <div className="flex items-center gap-2">
        <input
          id="rememberMe"
          type="checkbox"
          {...register("rememberMe")}
          className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
        />
        <label htmlFor="rememberMe" className="text-sm text-text">
          Remember me
        </label>
      </div>

      <Button
        type="submit"
        variant="primary"
        className="w-full"
        disabled={isLoading}
      >
        {isLoading ? "Signing in..." : "Sign in"}
      </Button>
    </form>
  );
}

// Example registration schema
const registerSchema = z
  .object({
    name: z.string().min(1, "Name is required"),
    email: z.string().email("Invalid email address"),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
      .regex(/[a-z]/, "Password must contain at least one lowercase letter")
      .regex(/[0-9]/, "Password must contain at least one number"),
    confirmPassword: z.string(),
    role: z.enum(["customer", "supplier"]),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
  });

type RegisterFormData = z.infer<typeof registerSchema>;

interface RegisterFormProps {
  onSubmit: (data: RegisterFormData) => Promise<void>;
  isLoading?: boolean;
  error?: string;
}

export function RegisterForm({ onSubmit, isLoading, error }: RegisterFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      name: "",
      email: "",
      password: "",
      confirmPassword: "",
      role: "customer",
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {error && (
        <div className="rounded-lg bg-danger/10 p-3 text-sm text-danger">
          {error}
        </div>
      )}

      <div>
        <label htmlFor="name" className="block text-sm font-medium text-text">
          Full Name
        </label>
        <input
          id="name"
          type="text"
          {...register("name")}
          className="mt-1 h-10 w-full rounded-lg border border-border bg-surface-1 px-3 text-sm text-text placeholder:text-text-faint focus:border-primary focus:outline-none"
          placeholder="John Doe"
        />
        {errors.name && (
          <p className="mt-1 text-xs text-danger">{errors.name.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="reg-email" className="block text-sm font-medium text-text">
          Email
        </label>
        <input
          id="reg-email"
          type="email"
          {...register("email")}
          className="mt-1 h-10 w-full rounded-lg border border-border bg-surface-1 px-3 text-sm text-text placeholder:text-text-faint focus:border-primary focus:outline-none"
          placeholder="you@example.com"
        />
        {errors.email && (
          <p className="mt-1 text-xs text-danger">{errors.email.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="reg-password" className="block text-sm font-medium text-text">
          Password
        </label>
        <input
          id="reg-password"
          type="password"
          {...register("password")}
          className="mt-1 h-10 w-full rounded-lg border border-border bg-surface-1 px-3 text-sm text-text placeholder:text-text-faint focus:border-primary focus:outline-none"
          placeholder="••••••••"
        />
        {errors.password && (
          <p className="mt-1 text-xs text-danger">{errors.password.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="confirmPassword" className="block text-sm font-medium text-text">
          Confirm Password
        </label>
        <input
          id="confirmPassword"
          type="password"
          {...register("confirmPassword")}
          className="mt-1 h-10 w-full rounded-lg border border-border bg-surface-1 px-3 text-sm text-text placeholder:text-text-faint focus:border-primary focus:outline-none"
          placeholder="••••••••"
        />
        {errors.confirmPassword && (
          <p className="mt-1 text-xs text-danger">{errors.confirmPassword.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="role" className="block text-sm font-medium text-text">
          I want to
        </label>
        <select
          id="role"
          {...register("role")}
          className="mt-1 h-10 w-full rounded-lg border border-border bg-surface-1 px-3 text-sm text-text focus:border-primary focus:outline-none"
        >
          <option value="customer">Shop on ZOZI</option>
          <option value="supplier">Sell on ZOZI</option>
        </select>
        {errors.role && (
          <p className="mt-1 text-xs text-danger">{errors.role.message}</p>
        )}
      </div>

      <Button
        type="submit"
        variant="primary"
        className="w-full"
        disabled={isLoading}
      >
        {isLoading ? "Creating account..." : "Create account"}
      </Button>
    </form>
  );
}
