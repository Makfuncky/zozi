import ErrorBoundary from "@/components/ui/ErrorBoundary";

const OrdersIndex = require("../../orders").default;

export default function OrdersIndexWrapped() {
  return (
    <ErrorBoundary>
      <OrdersIndex />
    </ErrorBoundary>
  );
}
