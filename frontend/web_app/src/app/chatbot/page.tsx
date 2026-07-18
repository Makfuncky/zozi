export default function ChatbotPage() {
  return (
    <main className="min-h-screen bg-background">
      <section className="mx-auto flex max-w-3xl flex-col items-start gap-4 px-6 py-16 sm:px-10">
        <p className="rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-primary">
          ZOZI Assistant
        </p>
        <h1 className="text-3xl font-extrabold text-text sm:text-4xl">Chat with the shopping assistant</h1>
        <p className="max-w-2xl text-sm leading-7 text-text-muted sm:text-base">
          The assistant panel opens automatically. Ask about supplier products, certifications, delivery details,
          and alternatives. Personal customer information is never shared in this chat.
        </p>
      </section>
    </main>
  );
}


