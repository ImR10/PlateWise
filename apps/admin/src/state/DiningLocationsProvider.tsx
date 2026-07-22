import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useReducer,
  type ReactNode,
} from "react";

import { initialDiningLocations } from "../data/locations";
import type { DiningLocation, LocationStatus } from "../data/locationTypes";
import * as ops from "./locationOps";

type EditableFields = Partial<
  Pick<
    DiningLocation,
    | "name"
    | "description"
    | "longDescription"
    | "status"
    | "studentVisible"
    | "internalNotes"
  >
>;

interface DiningLocationsContextValue {
  locations: DiningLocation[];
  getLocation: (id: string) => DiningLocation | undefined;
  getLocationName: (id: string) => string;
  /** Locations eligible to host new menus (not inactive or archived). */
  selectableLocations: DiningLocation[];
  create: (location: DiningLocation) => void;
  duplicate: (id: string) => DiningLocation | undefined;
  remove: (id: string) => void;
  setStatus: (id: string, status: LocationStatus) => void;
  update: (id: string, patch: EditableFields) => void;
  updateWith: (
    id: string,
    fn: (location: DiningLocation) => DiningLocation,
  ) => void;
}

type Action =
  | { type: "ADD"; location: DiningLocation }
  | { type: "DELETE"; id: string }
  | {
      type: "MUTATE";
      id: string;
      fn: (location: DiningLocation) => DiningLocation;
    };

function reducer(state: DiningLocation[], action: Action): DiningLocation[] {
  switch (action.type) {
    case "ADD":
      return [...state, action.location];
    case "DELETE":
      return state.filter((location) => location.id !== action.id);
    case "MUTATE":
      return state.map((location) =>
        location.id === action.id ? action.fn(location) : location,
      );
    default:
      return state;
  }
}

const DiningLocationsContext =
  createContext<DiningLocationsContextValue | null>(null);

export function DiningLocationsProvider({
  children,
  seed = initialDiningLocations,
}: {
  children: ReactNode;
  seed?: DiningLocation[];
}) {
  const [locations, dispatch] = useReducer(reducer, seed);

  const mutate = useCallback(
    (id: string, fn: (location: DiningLocation) => DiningLocation) => {
      dispatch({
        type: "MUTATE",
        id,
        fn: (location) => ops.touchLocation(fn(location)),
      });
    },
    [],
  );

  const value = useMemo<DiningLocationsContextValue>(
    () => ({
      locations,
      getLocation: (id) => locations.find((l) => l.id === id),
      getLocationName: (id) =>
        locations.find((l) => l.id === id)?.name ?? "Unassigned location",
      selectableLocations: locations.filter(
        (l) => l.status === "active" || l.status === "draft",
      ),
      create: (location) => dispatch({ type: "ADD", location }),
      duplicate: (id) => {
        const source = locations.find((l) => l.id === id);
        if (!source) return undefined;
        const copy = ops.cloneLocation(source);
        dispatch({ type: "ADD", location: copy });
        return copy;
      },
      remove: (id) => dispatch({ type: "DELETE", id }),
      setStatus: (id, status) => mutate(id, (l) => ({ ...l, status })),
      update: (id, patch) => mutate(id, (l) => ({ ...l, ...patch })),
      updateWith: (id, fn) => mutate(id, fn),
    }),
    [locations, mutate],
  );

  return (
    <DiningLocationsContext.Provider value={value}>
      {children}
    </DiningLocationsContext.Provider>
  );
}

export function useDiningLocations(): DiningLocationsContextValue {
  const context = useContext(DiningLocationsContext);
  if (!context) {
    throw new Error(
      "useDiningLocations must be used within a DiningLocationsProvider",
    );
  }
  return context;
}
