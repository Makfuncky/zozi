import type { UserInfo } from "@/lib/useAuth";

export function getPostLoginPath(role: UserInfo["role"]): string {
  switch (role) {
    case "admin":
      return "/admin/dashboard";
    case "supplier":
      return "/supplier/dashboard";
    case "logistics_partner":
      return "/logistics-partner/dashboard";
    default:
      return "/";
  }
}
