import { redirect } from "next/navigation";

export default function SupplierReturnsPage() {
  redirect("/supplier/orders?section=returns");
}


