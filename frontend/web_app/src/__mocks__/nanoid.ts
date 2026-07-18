/** Manual mock for nanoid — avoids ESM incompatibility in Jest. */
let _counter = 0;
export const nanoid = (_size?: number) => `mock-id-${++_counter}`;
