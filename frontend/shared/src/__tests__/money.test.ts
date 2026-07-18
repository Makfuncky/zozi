import {
  roundMoney,
  toMinorUnits,
  fromMinorUnits,
  formatMoney,
  addMoney,
  subtractMoney,
  multiplyMoney,
  applyPercentageDiscount,
  applyFixedDiscount,
  calcTotal,
} from "../money";

describe("roundMoney", () => {
  it("rounds to 2 decimal places", () => {
    expect(roundMoney(10.005)).toBe(10.01);
    expect(roundMoney(10.004)).toBe(10);
    expect(roundMoney(1.555)).toBe(1.56);
  });

  it("handles whole numbers", () => {
    expect(roundMoney(5)).toBe(5);
  });

  it("handles zero", () => {
    expect(roundMoney(0)).toBe(0);
  });
});

describe("toMinorUnits", () => {
  it("converts to cents by default", () => {
    expect(toMinorUnits(9.99)).toBe(999);
    expect(toMinorUnits(1.00)).toBe(100);
    expect(toMinorUnits(0.5)).toBe(50);
  });

  it("uses custom factor", () => {
    expect(toMinorUnits(1.5, 1000)).toBe(1500);
  });
});

describe("fromMinorUnits", () => {
  it("converts back from cents", () => {
    expect(fromMinorUnits(999)).toBeCloseTo(9.99);
    expect(fromMinorUnits(100)).toBe(1);
  });

  it("rounds to 2dp", () => {
    expect(fromMinorUnits(3)).toBeCloseTo(0.03);
  });
});

describe("formatMoney", () => {
  it("returns a string with currency", () => {
    const result = formatMoney(9.99, "USD", "en-US");
    expect(typeof result).toBe("string");
    expect(result).toContain("9.99");
  });

  it("handles zero", () => {
    const result = formatMoney(0, "USD");
    expect(result).toContain("0.00");
  });

  it("uses currency-specific precision for high-fraction currencies", () => {
    const result = formatMoney(4.125, "KWD", "en-US");
    expect(result).toContain("4.125");
  });
});

describe("addMoney", () => {
  it("avoids floating-point drift", () => {
    expect(addMoney(0.1, 0.2)).toBeCloseTo(0.3);
    expect(addMoney(0.1, 0.2)).toBe(0.3);
  });

  it("adds two whole numbers", () => {
    expect(addMoney(5, 3)).toBe(8);
  });
});

describe("subtractMoney", () => {
  it("subtracts b from a safely", () => {
    expect(subtractMoney(10, 3)).toBe(7);
    expect(subtractMoney(0.3, 0.1)).toBeCloseTo(0.2);
  });
});

describe("multiplyMoney", () => {
  it("rounds after multiplication", () => {
    expect(multiplyMoney(9.99, 3)).toBeCloseTo(29.97);
  });

  it("handles fractional quantities", () => {
    expect(multiplyMoney(10, 2.5)).toBeCloseTo(25);
  });
});

describe("applyPercentageDiscount", () => {
  it("applies discount correctly", () => {
    expect(applyPercentageDiscount(100, 20)).toBeCloseTo(80);
    expect(applyPercentageDiscount(50, 10)).toBeCloseTo(45);
  });

  it("does not go below 0", () => {
    expect(applyPercentageDiscount(100, 100)).toBe(0);
  });

  it("returns original for 0% off", () => {
    expect(applyPercentageDiscount(100, 0)).toBe(100);
  });
});

describe("applyFixedDiscount", () => {
  it("subtracts fixed amount", () => {
    expect(applyFixedDiscount(100, 25)).toBeCloseTo(75);
  });

  it("floors at 0 when discount exceeds amount", () => {
    expect(applyFixedDiscount(10, 50)).toBe(0);
  });
});

describe("calcTotal", () => {
  it("returns 0 for empty items", () => {
    expect(calcTotal([])).toBe(0);
  });

  it("multiplies price × quantity and sums", () => {
    expect(calcTotal([{ price: 10, quantity: 3 }])).toBeCloseTo(30);
    expect(calcTotal([{ price: 10, quantity: 2 }, { price: 5, quantity: 4 }])).toBeCloseTo(40);
  });

  it("handles decimal prices", () => {
    expect(calcTotal([{ price: 9.99, quantity: 3 }])).toBeCloseTo(29.97);
  });
});