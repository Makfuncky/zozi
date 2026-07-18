import { redirect } from "next/navigation";

export default function SupplierInvoicesPage() {
  redirect("/supplier/payouts?view=invoices");
}


