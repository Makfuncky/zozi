import { redirect } from "next/navigation";

export default function OffersPage() {
  redirect("/products?sort=deals");
}
