/**
 * Invoice PDF generation and download service for mobile.
 * Uses expo-print and expo-sharing for PDF creation and sharing.
 */

import { apiFetch } from "@/lib/api";
import * as Print from "expo-print";
import * as Sharing from "expo-sharing";
import { Platform } from "react-native";

export interface InvoiceData {
  id: number;
  invoice_number: string;
  order_id: number;
  created_at: string;
  status: string;
  customer_name: string;
  customer_email: string;
  customer_address: string;
  supplier_name: string;
  supplier_email: string;
  items: Array<{
    product_name: string;
    quantity: number;
    unit_price: number;
    line_total: number;
  }>;
  subtotal: number;
  vat: number;
  shipping: number;
  total: number;
}

/**
 * Fetch invoice data from backend
 */
export async function getInvoiceData(orderId: number): Promise<InvoiceData> {
  return apiFetch<InvoiceData>(`/orders/${orderId}/invoice`);
}

/**
 * Generate PDF HTML from invoice data
 */
const INVOICE_CSS = [
  "body { font-family: 'Helvetica', sans-serif; margin: 0; padding: 20px; }",
  ".header { text-align: center; margin-bottom: 20px; }",
  ".logo { font-size: 24px; font-weight: bold; color: #32CD32; }",
  ".invoice-title { font-size: 18px; margin: 10px 0; }",
  ".section { margin: 20px 0; }",
  ".section-title { font-weight: bold; border-bottom: 1px solid #ccc; padding-bottom: 5px; }",
  "table { width: 100%; border-collapse: collapse; }",
  "th, td { padding: 8px; text-align: left; border-bottom: 1px solid #eee; }",
  "th { background-color: #f5f5f5; }",
  ".total-row { font-weight: bold; }",
  ".footer { margin-top: 30px; padding-top: 10px; border-top: 1px solid #ccc; font-size: 12px; color: #666; }",
].join("\n");

function generateInvoiceHtml(invoice: InvoiceData): string {
  const formatCurrency = (amount: number) =>
    new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(amount);

  const encodedCss = btoa(INVOICE_CSS);

  return `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="UTF-8" />
        <link rel="stylesheet" href="data:text/css;base64,${encodedCss}" />
      </head>
      <body>
        <div class="header">
          <div class="logo">ZOZI</div>
          <div class="invoice-title">INVOICE</div>
          <div>Invoice #${invoice.invoice_number}</div>
          <div>Date: ${new Date(invoice.created_at).toLocaleDateString()}</div>
        </div>

        <div class="section">
          <div class="section-title">Bill To</div>
          <div>${invoice.customer_name || ""}</div>
          <div>${invoice.customer_email || ""}</div>
          <div>${invoice.customer_address || ""}</div>
        </div>

        <div class="section">
          <div class="section-title">Ship To</div>
          <div>${invoice.customer_name || ""}</div>
          <div>${invoice.customer_address || ""}</div>
        </div>

        <div class="section">
          <div class="section-title">Items</div>
          <table>
            <thead>
              <tr>
                <th>Product</th>
                <th>Qty</th>
                <th>Price</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              ${invoice.items.map(item => `
                <tr>
                  <td>${item.product_name}</td>
                  <td>${item.quantity}</td>
                  <td>${formatCurrency(item.unit_price)}</td>
                  <td>${formatCurrency(item.line_total)}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>

        <div class="section">
          <table>
            <tr><td>Subtotal</td><td style="text-align: right;">${formatCurrency(invoice.subtotal)}</td></tr>
            <tr><td>VAT</td><td style="text-align: right;">${formatCurrency(invoice.vat)}</td></tr>
            <tr><td>Shipping</td><td style="text-align: right;">${formatCurrency(invoice.shipping)}</td></tr>
            <tr class="total-row">
              <td>Total</td>
              <td style="text-align: right;">${formatCurrency(invoice.total)}</td>
            </tr>
          </table>
        </div>

        <div class="footer">
          <div>Thank you for your purchase!</div>
          <div>For questions, contact: ${invoice.supplier_email || ""}</div>
        </div>
      </body>
    </html>
  `;
}

/**
 * Generate and download invoice PDF
 */
export async function downloadInvoicePDF(orderId: number): Promise<string> {
  try {
    const invoice = await getInvoiceData(orderId);
    const html = generateInvoiceHtml(invoice);

    // Generate PDF
    const { uri } = await Print.printToFileAsync({
      html,
    });

    // Share or save the PDF
    if (Platform.OS === "web") {
      // Web: trigger download
      const link = document.createElement("a");
      link.href = uri;
      link.download = `invoice-${invoice.invoice_number}.pdf`;
      link.click();
      return uri;
    } else {
      // Mobile: share the PDF
      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(uri, {
          dialogTitle: `Invoice #${invoice.invoice_number}`,
        });
      }
      return uri;
    }
  } catch (error) {
    console.error("Failed to generate invoice PDF:", error);
    throw error;
  }
}

/**
 * Open invoice directly in PDF viewer
 */
export async function openInvoicePDF(orderId: number): Promise<void> {
  const { uri } = await Print.printToFileAsync({
    html: await generateInvoiceHtml(await getInvoiceData(orderId)),
  });
  
  if (Platform.OS !== "web") {
    await Print.printAsync({ uri });
  }
}