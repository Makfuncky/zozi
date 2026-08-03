import { Redirect } from "expo-router";
import ErrorBoundary from "@/components/ui/ErrorBoundary";

export default function ProductsIndexRedirect() {
  return (
    <ErrorBoundary>
      <Redirect href="/(tabs)/products" />
    </ErrorBoundary>
  );
}
