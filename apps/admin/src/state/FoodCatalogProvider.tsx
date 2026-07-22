import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useReducer,
  type ReactNode,
} from "react";

import { initialFoodCatalog } from "../data/foods";
import type { FoodCatalogItem, FoodStatus } from "../data/foodTypes";
import * as ops from "./foodOps";

type EditableFields = Partial<
  Omit<FoodCatalogItem, "id" | "updatedAt" | "updatedBy">
>;

interface FoodCatalogContextValue {
  foods: FoodCatalogItem[];
  getFood: (id: string) => FoodCatalogItem | undefined;
  /** Items eligible to be added to menus (not archived). */
  selectableFoods: FoodCatalogItem[];
  create: (food: FoodCatalogItem) => void;
  duplicate: (id: string) => FoodCatalogItem | undefined;
  remove: (id: string) => void;
  setStatus: (id: string, status: FoodStatus) => void;
  update: (id: string, patch: EditableFields) => void;
  updateWith: (
    id: string,
    fn: (food: FoodCatalogItem) => FoodCatalogItem,
  ) => void;
}

type Action =
  | { type: "ADD"; food: FoodCatalogItem }
  | { type: "DELETE"; id: string }
  | {
      type: "MUTATE";
      id: string;
      fn: (food: FoodCatalogItem) => FoodCatalogItem;
    };

function reducer(state: FoodCatalogItem[], action: Action): FoodCatalogItem[] {
  switch (action.type) {
    case "ADD":
      return [...state, action.food];
    case "DELETE":
      return state.filter((food) => food.id !== action.id);
    case "MUTATE":
      return state.map((food) =>
        food.id === action.id ? action.fn(food) : food,
      );
    default:
      return state;
  }
}

const FoodCatalogContext = createContext<FoodCatalogContextValue | null>(null);

export function FoodCatalogProvider({
  children,
  seed = initialFoodCatalog,
}: {
  children: ReactNode;
  seed?: FoodCatalogItem[];
}) {
  const [foods, dispatch] = useReducer(reducer, seed);

  const mutate = useCallback(
    (id: string, fn: (food: FoodCatalogItem) => FoodCatalogItem) => {
      dispatch({ type: "MUTATE", id, fn: (food) => ops.touchFood(fn(food)) });
    },
    [],
  );

  const value = useMemo<FoodCatalogContextValue>(
    () => ({
      foods,
      getFood: (id) => foods.find((f) => f.id === id),
      selectableFoods: foods.filter((f) => f.status !== "archived"),
      create: (food) => dispatch({ type: "ADD", food }),
      duplicate: (id) => {
        const source = foods.find((f) => f.id === id);
        if (!source) return undefined;
        const copy = ops.cloneFood(source);
        dispatch({ type: "ADD", food: copy });
        return copy;
      },
      remove: (id) => dispatch({ type: "DELETE", id }),
      setStatus: (id, status) => mutate(id, (f) => ({ ...f, status })),
      update: (id, patch) => mutate(id, (f) => ({ ...f, ...patch })),
      updateWith: (id, fn) => mutate(id, fn),
    }),
    [foods, mutate],
  );

  return (
    <FoodCatalogContext.Provider value={value}>
      {children}
    </FoodCatalogContext.Provider>
  );
}

export function useFoodCatalog(): FoodCatalogContextValue {
  const context = useContext(FoodCatalogContext);
  if (!context) {
    throw new Error("useFoodCatalog must be used within a FoodCatalogProvider");
  }
  return context;
}
