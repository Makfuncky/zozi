"use client";

import { useMemo } from "react";
import {
  Chart as ChartJS,
  ArcElement,
  BarElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  type ChartData,
  type ChartOptions,
} from "chart.js";
import { Pie, Bar } from "react-chartjs-2";

// Register Chart.js components
ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

// Data sensitivity formatting
export function formatNumber(value: number, sensitivity: "public" | "internal" | "admin" = "public"): string {
  switch (sensitivity) {
    case "admin":
      // Full precision for admin
      return value.toLocaleString("en-US", { 
        maximumFractionDigits: 2,
        minimumFractionDigits: 0 
      });
    case "internal":
      // K notation for internal
      if (Math.abs(value) >= 1e6) return `${(value / 1e6).toFixed(1)}M`;
      if (Math.abs(value) >= 1e3) return `${(value / 1e3).toFixed(1)}K`;
      return value.toLocaleString();
    case "public":
    default:
      // Rounded for public display
      if (Math.abs(value) >= 1e6) return `${Math.round(value / 1e6)}M`;
      if (Math.abs(value) >= 1e3) return `${Math.round(value / 1e3)}K`;
      return Math.round(value).toString();
  }
}

// Pie Chart Component
export function PieChartComponent({ 
  data, 
  title,
  dataKey = "value",
  nameKey = "label",
  colors = ["#22c55e", "#6366f1", "#f59e0b", "#ef4444", "#8b5cf6"]
}: {
  data: Array<Record<string, unknown>>;
  title?: string;
  dataKey?: string;
  nameKey?: string;
  colors?: string[];
}) {
  const chartData: ChartData<"pie"> = {
    labels: data.map(d => String(d[nameKey] ?? "")),
    datasets: [{
      data: data.map(d => Number(d[dataKey] ?? 0)),
      backgroundColor: colors,
      borderColor: "white",
      borderWidth: 2,
    }]
  };

  const options: ChartOptions<"pie"> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "bottom",
        labels: {
          padding: 20,
          usePointStyle: true,
        }
      },
      title: title ? { display: true, text: title } : undefined,
    }
  };

  return <Pie data={chartData} options={options} />;
}

// Bar Chart Component - supports multiple data series
export function BarChartComponent({ 
  data, 
  title,
  dataKey = "value",
  nameKey = "label",
  color = "#3b82f6",
  yKeys,
}: {
  data: Array<Record<string, unknown>>;
  title?: string;
  dataKey?: string;
  nameKey?: string;
  color?: string | string[];
  yKeys?: string[];
}) {
  // Handle both single series and multi-series data
  const isMultiSeries = yKeys && yKeys.length > 0;
  const chartColors = Array.isArray(color) ? color : [color];
  
  const chartData: ChartData<"bar"> = {
    labels: data.map(d => String(d[nameKey] ?? "")),
    datasets: isMultiSeries 
      ? yKeys!.map((key, i) => ({
          label: key.charAt(0).toUpperCase() + key.slice(1),
          data: data.map(d => Number(d[key] ?? 0)),
          backgroundColor: chartColors[i % chartColors.length],
          borderColor: chartColors[i % chartColors.length],
          borderRadius: 4,
        }))
      : [{
          label: "Value",
          data: data.map(d => Number(d[dataKey] ?? 0)),
          backgroundColor: chartColors[0],
          borderColor: chartColors[0],
          borderRadius: 4,
        }]
  };

  const options: ChartOptions<"bar"> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: isMultiSeries ? { display: true, position: "bottom" as const } : { display: false },
      title: title ? { display: true, text: title } : undefined,
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: (value) => formatNumber(Number(value), "internal")
        }
      }
    }
  };

  return <Bar data={chartData} options={options} />;
}