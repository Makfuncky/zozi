import React, { Component, ErrorInfo, ReactNode } from "react";
import { View, Text, TouchableOpacity, ScrollView } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useThemeStore } from "@/lib/themeStore";
import { getFrontendErrorLogs, logFrontendError, type FrontendErrorLogEntry } from "@shared/errorLogging";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  message: string;
  showLogs: boolean;
  recentLogs: FrontendErrorLogEntry[];
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, message: "", showLogs: false, recentLogs: [] };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      message: error.message || "Unexpected error",
      showLogs: false,
      recentLogs: getFrontendErrorLogs().slice(0, 5),
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    logFrontendError(error, "mobile-error-boundary", {
      componentStack: errorInfo.componentStack,
    });
    console.error("[mobile-error-boundary]", error, errorInfo);
    this.setState({ recentLogs: getFrontendErrorLogs().slice(0, 5) });
  }

  private reset = () => {
    this.setState({ hasError: false, message: "", showLogs: false, recentLogs: [] });
  };

  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }

    const { theme } = useThemeStore.getState();
    const c = theme.colors;

    return (
      <View style={{ flex: 1, alignItems: "center", justifyContent: "center", padding: 20, backgroundColor: c.surface0 }}>
        <Ionicons name="alert-circle-outline" size={40} color={c.danger} style={{ marginBottom: 12 }} />
        <Text style={{ fontSize: 20, fontWeight: "800", marginBottom: 8, color: c.text }}>
          Something went wrong
        </Text>
        <Text style={{ fontSize: 14, color: c.textMuted, textAlign: "center", marginBottom: 16 }}>
          {this.state.message}
        </Text>
        <TouchableOpacity
          onPress={() => this.setState((state) => ({ showLogs: !state.showLogs }))}
          style={{ borderRadius: 10, borderWidth: 1, borderColor: c.border, paddingHorizontal: 16, paddingVertical: 10, marginBottom: 12 }}
        >
          <Text style={{ color: c.text, fontWeight: "700" }}>
            {this.state.showLogs ? "Hide Error Logs" : "Show Error Logs"}
          </Text>
        </TouchableOpacity>
        {this.state.showLogs && (
          <View style={{ width: "100%", maxHeight: 200, borderWidth: 1, borderColor: c.border, borderRadius: 12, backgroundColor: c.surface1, marginBottom: 12 }}>
            <ScrollView contentContainerStyle={{ padding: 12 }}>
              {this.state.recentLogs.length === 0 ? (
                <Text style={{ color: c.textMuted }}>No frontend error logs captured yet.</Text>
              ) : (
                this.state.recentLogs.map((entry) => (
                  <View key={entry.id} style={{ marginBottom: 10, paddingBottom: 10, borderBottomWidth: 1, borderBottomColor: c.border }}>
                    <Text style={{ fontWeight: "700", color: c.text }}>{entry.source}</Text>
                    <Text style={{ color: c.textMuted, fontSize: 12 }}>{entry.timestamp}</Text>
                    <Text style={{ color: c.textMuted }}>{entry.message}</Text>
                  </View>
                ))
              )}
            </ScrollView>
          </View>
        )}
        <TouchableOpacity
          onPress={this.reset}
          style={{ borderRadius: 10, backgroundColor: c.brand, paddingHorizontal: 16, paddingVertical: 10 }}
        >
          <Text style={{ color: c.onBrand, fontWeight: "700" }}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }
}
