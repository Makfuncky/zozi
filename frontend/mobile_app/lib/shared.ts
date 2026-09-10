/**
 * lib/shared.ts — typed re-exports from @zozi/shared.
 *
 * F-1 parity fix: the mobile app declared `@zozi/shared` as a dependency
 * but never imported from it. This module wires up the shared money + utils
 * helpers so mobile screens can use the same canonical currency / math code
 * as the web app (Law #4: single source of truth for cross-platform types).
 */
import {
  formatMoney as _formatMoney,
  roundMoney as _roundMoney,
  addMoney as _addMoney,
  subtractMoney as _subtractMoney,
  multiplyMoney as _multiplyMoney,
  applyPercentageDiscount as _applyPercentageDiscount,
  applyFixedDiscount as _applyFixedDiscount,
  calcTotal as _calcTotal,
} from "@zozi/shared";

export const formatMoney = _formatMoney;
export const roundMoney = _roundMoney;
export const addMoney = _addMoney;
export const subtractMoney = _subtractMoney;
export const multiplyMoney = _multiplyMoney;
export const applyPercentageDiscount = _applyPercentageDiscount;
export const applyFixedDiscount = _applyFixedDiscount;
export const calcTotal = _calcTotal;
