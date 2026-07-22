/**
 * Session-unique id generator for in-memory entities created during a session
 * (new menus, duplicated menus, stations, custom items). Monotonic counter —
 * stable within a session, reset on refresh. Not for persistence.
 */
let counter = 1000;

export const createId = (prefix: string): string => {
  counter += 1;
  return `${prefix}-${counter}`;
};
