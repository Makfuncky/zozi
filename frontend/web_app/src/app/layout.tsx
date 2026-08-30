import type { Metadata } from "next";
import { Fraunces, Sora, Nunito, Noto_Naskh_Arabic } from "next/font/google";
import { Suspense } from "react";
import "@/styles/tokens.css";
import "@/styles/globals.css";
import "@/styles/glow.css";
import { AuthProvider } from "@/lib/useAuth";
import Header from "@/components/Header";
import AuthRequiredModal from "@/components/AuthRequiredModal";
import Chatbot from "@/components/Chatbot";
import ToastContainer from "@/components/ToastContainer";
import Footer from "@/components/Footer";
import { ThemeProvider } from "@/components/ThemeProvider";
import ErrorBoundary from "@/components/ErrorBoundary";
import CurrencyInit from "@/components/CurrencyInit";
import ErrorHandlerInit from "@/components/ErrorHandlerInit";
import LocaleInit from "@/components/LocaleInit";
import BackgroundEffect from "@/components/BackgroundEffect";
import UserRealtimeBridge from "@/components/UserRealtimeBridge";

const displayFont = Fraunces({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});

const bodyFont = Sora({
  subsets: ["latin"],
  variable: "--font-body",
  display: "swap",
});

const notoArabic = Noto_Naskh_Arabic({
  subsets: ["arabic"],
  variable: "--font-arabic",
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

const nunitoFont = Nunito({
  subsets: ["latin"],
  variable: "--font-nunito",
  weight: ["700", "800", "900"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "ZOZI - Trust Delivered",
  description:
    "Trust delivered through verified suppliers, global dispatch, and secure shopping.",
  icons: {
    icon: "/file.svg",
    shortcut: "/file.svg",
    apple: "/file.svg",
  },
  keywords: ["ecommerce", "online shopping", "products", "shopping", "suppliers"],
  openGraph: {
    title: "ZOZI - Trust Delivered",
    description: "Trust delivered through verified suppliers and global dispatch.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "ZOZI - Trust Delivered",
    description: "Trust delivered through verified suppliers and global dispatch.",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      {/* Anti-flash: apply theme class synchronously before first paint */}
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var s=localStorage.getItem('zozi-theme');var t=s?JSON.parse(s).state.theme:(window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');document.documentElement.classList.add(t);}catch(e){document.documentElement.classList.add('dark');}})();`,
          }}
        />
        {/* Anti-flash locale: apply dir/lang before first paint */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var tags={en:'en-US',ar:'ar-OM',fr:'fr-FR',de:'de-DE',es:'es-ES',hi:'hi-IN',ur:'ur-PK',tr:'tr-TR',fa:'fa-IR'};var aliases={'en-us':'en','en-gb':'en','ar-om':'ar','ar-ae':'ar','ar-sa':'ar','fr-fr':'fr','de-de':'de','es-es':'es','hi-in':'hi','ur-pk':'ur','tr-tr':'tr','fa-ir':'fa'};var raw=localStorage.getItem('zozi_locale');var persisted=raw?JSON.parse(raw)?.state?.locale:'';var source=(persisted||navigator.language||'en').toLowerCase().replace(/_/g,'-');var locale=aliases[source]||aliases[source.split('-')[0]]||source.split('-')[0]||'en';if(!tags[locale])locale='en';document.documentElement.dir=(locale==='ar'||locale==='ur'||locale==='fa')?'rtl':'ltr';document.documentElement.lang=tags[locale];}catch(e){document.documentElement.dir='ltr';document.documentElement.lang='en-US';}})();`,
          }}
        />
      </head>
      <body
        suppressHydrationWarning
        className={`${displayFont.variable} ${bodyFont.variable} ${notoArabic.variable} ${nunitoFont.variable} antialiased font-body min-h-screen bg-surface-base text-text transition-colors duration-300`}
      >
        <ThemeProvider>
          <AuthProvider>
            {/* Fixed full-page background animation — z:0 in root stacking context, renders behind data-app-frame */}
            <BackgroundEffect />
            {/* All page content at z:10 with isolation:isolate — transparent gaps let BackgroundEffect show through */}
            <div className="relative" data-app-frame style={{ isolation: "isolate", zIndex: 10 }}>
              <LocaleInit />
              <CurrencyInit />
              <ErrorHandlerInit />
              <UserRealtimeBridge />
              <div data-app-header>
                <Header />
              </div>
              <div data-app-body>
                <ErrorBoundary>
                  {children}
                </ErrorBoundary>
              </div>
              <div data-app-footer>
                <Footer />
              </div>
              <AuthRequiredModal />
              <Suspense fallback={null}>
                <Chatbot />
              </Suspense>
              <ToastContainer />
            </div>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
