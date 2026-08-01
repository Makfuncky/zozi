import React from "react";
import ReactDOM from "react-dom/client";
import { motion } from "motion/react";
import { ZoziWordmark } from "../zozi-logo";
import "./styles.css";

function App() {
  return (
    <main className="app-shell">
      <section className="panel single-page">
        <div className="wordmark-demo">
          <ZoziWordmark size={360} theme="light" />
          <motion.p
            className="tagline"
            initial={{ opacity: 0, x: 80, y: 30, scale: 0.85, letterSpacing: "0.75em" }}
            animate={{
              opacity: 1,
              x: 0,
              y: 0,
              scale: 1,
              letterSpacing: "0.2em",
            }}
            transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1], delay: 1.6 }}
          >
            Trust Delivered
          </motion.p>
        </div>
      </section>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);