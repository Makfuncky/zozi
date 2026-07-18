import {
  extractChatbotSearchResults,
  getChatbotReplyKey,
  hasProductIntent,
} from "./chatbot";

describe("chatbot helpers", () => {
  it("detects product intent queries", () => {
    expect(hasProductIntent("show me laptops under 500")).toBe(true);
    expect(hasProductIntent("recommend new phones")).toBe(true);
    expect(hasProductIntent("how can I return an order")).toBe(false);
  });

  it("maps support intents to reply keys", () => {
    expect(getChatbotReplyKey("hey there")).toBe("chatbotGreeting");
    expect(getChatbotReplyKey("I need shipping details")).toBe("chatbotShippingReply");
    expect(getChatbotReplyKey("how do refunds work")).toBe("chatbotReturnReply");
    expect(getChatbotReplyKey("random unrelated message")).toBe("chatbotUnknownReply");
  });

  it("extracts results from either products or results payload keys", () => {
    expect(extractChatbotSearchResults({ products: [{ id: 1, name: "A", price: 10 }] })).toHaveLength(1);
    expect(extractChatbotSearchResults({ results: [{ id: 2, name: "B", price: 20 }] })).toHaveLength(1);
    expect(extractChatbotSearchResults({ nope: [] })).toHaveLength(0);
  });
});
