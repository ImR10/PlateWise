import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useReducer,
  type ReactNode,
} from "react";

import { initialMenus } from "../data/menus";
import type {
  AvailabilityStatus,
  Menu,
  MenuItem,
  MenuStatus,
} from "../data/menuTypes";
import * as ops from "./menuOps";
import type { CreateMenuInput, CustomItemInput } from "./menuOps";

type EditableMeta = Partial<
  Pick<Menu, "locationId" | "date" | "mealPeriod" | "title" | "internalNotes">
>;

interface MenusContextValue {
  menus: Menu[];
  getMenu: (id: string) => Menu | undefined;
  createMenu: (input: CreateMenuInput) => Menu;
  duplicateMenu: (id: string) => Menu | undefined;
  deleteMenu: (id: string) => void;
  setStatus: (id: string, status: MenuStatus) => void;
  updateMeta: (id: string, patch: EditableMeta) => void;
  addStation: (id: string, name?: string) => void;
  renameStation: (id: string, stationId: string, name: string) => void;
  deleteStation: (id: string, stationId: string) => void;
  moveStation: (id: string, stationId: string, direction: -1 | 1) => void;
  addItems: (id: string, stationId: string, items: MenuItem[]) => void;
  addCustomItem: (
    id: string,
    stationId: string,
    input: CustomItemInput,
  ) => void;
  removeItem: (id: string, stationId: string, itemId: string) => void;
  updateItem: (
    id: string,
    stationId: string,
    itemId: string,
    patch: Partial<MenuItem>,
  ) => void;
  setItemAvailability: (
    id: string,
    stationId: string,
    itemId: string,
    availability: AvailabilityStatus,
  ) => void;
  moveItem: (
    id: string,
    stationId: string,
    itemId: string,
    direction: -1 | 1,
  ) => void;
  moveItemToStation: (
    id: string,
    fromStationId: string,
    itemId: string,
    toStationId: string,
  ) => void;
}

type Action =
  | { type: "ADD"; menu: Menu }
  | { type: "DELETE"; id: string }
  | { type: "MUTATE"; id: string; fn: (menu: Menu) => Menu };

function reducer(state: Menu[], action: Action): Menu[] {
  switch (action.type) {
    case "ADD":
      return [...state, action.menu];
    case "DELETE":
      return state.filter((menu) => menu.id !== action.id);
    case "MUTATE":
      return state.map((menu) =>
        menu.id === action.id ? action.fn(menu) : menu,
      );
    default:
      return state;
  }
}

const MenusContext = createContext<MenusContextValue | null>(null);

export function MenusProvider({
  children,
  seed = initialMenus,
}: {
  children: ReactNode;
  /** Override the seed data (used by tests). */
  seed?: Menu[];
}) {
  const [menus, dispatch] = useReducer(reducer, seed);

  // Apply a pure transform, then stamp the menu as edited this session.
  const mutate = useCallback((id: string, fn: (menu: Menu) => Menu) => {
    dispatch({ type: "MUTATE", id, fn: (menu) => ops.touchMenu(fn(menu)) });
  }, []);

  const value = useMemo<MenusContextValue>(() => {
    return {
      menus,
      getMenu: (id) => menus.find((menu) => menu.id === id),
      createMenu: (input) => {
        const menu = ops.buildMenu(input);
        dispatch({ type: "ADD", menu });
        return menu;
      },
      duplicateMenu: (id) => {
        const source = menus.find((menu) => menu.id === id);
        if (!source) return undefined;
        const copy = ops.cloneMenu(source);
        dispatch({ type: "ADD", menu: copy });
        return copy;
      },
      deleteMenu: (id) => dispatch({ type: "DELETE", id }),
      setStatus: (id, status) => mutate(id, (menu) => ({ ...menu, status })),
      updateMeta: (id, patch) => mutate(id, (menu) => ({ ...menu, ...patch })),
      addStation: (id, name) =>
        mutate(id, (menu) => ops.addStation(menu, name)),
      renameStation: (id, stationId, name) =>
        mutate(id, (menu) => ops.renameStation(menu, stationId, name)),
      deleteStation: (id, stationId) =>
        mutate(id, (menu) => ops.deleteStation(menu, stationId)),
      moveStation: (id, stationId, direction) =>
        mutate(id, (menu) => ops.moveStation(menu, stationId, direction)),
      addItems: (id, stationId, items) =>
        mutate(id, (menu) => ops.addItems(menu, stationId, items)),
      addCustomItem: (id, stationId, input) =>
        mutate(id, (menu) =>
          ops.addItems(menu, stationId, [ops.menuItemFromCustom(input)]),
        ),
      removeItem: (id, stationId, itemId) =>
        mutate(id, (menu) => ops.removeItem(menu, stationId, itemId)),
      updateItem: (id, stationId, itemId, patch) =>
        mutate(id, (menu) => ops.updateItem(menu, stationId, itemId, patch)),
      setItemAvailability: (id, stationId, itemId, availability) =>
        mutate(id, (menu) =>
          ops.setItemAvailability(menu, stationId, itemId, availability),
        ),
      moveItem: (id, stationId, itemId, direction) =>
        mutate(id, (menu) => ops.moveItem(menu, stationId, itemId, direction)),
      moveItemToStation: (id, fromStationId, itemId, toStationId) =>
        mutate(id, (menu) =>
          ops.moveItemToStation(menu, fromStationId, itemId, toStationId),
        ),
    };
  }, [menus, mutate]);

  return (
    <MenusContext.Provider value={value}>{children}</MenusContext.Provider>
  );
}

export function useMenus(): MenusContextValue {
  const context = useContext(MenusContext);
  if (!context) {
    throw new Error("useMenus must be used within a MenusProvider");
  }
  return context;
}
