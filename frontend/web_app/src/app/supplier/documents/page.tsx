import { redirect } from "next/navigation";

export default function SupplierDocumentsPage() {
  redirect("/supplier/profile?tab=documents");
}


