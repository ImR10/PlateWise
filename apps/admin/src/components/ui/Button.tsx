import type { ButtonHTMLAttributes } from "react";

import { Icon } from "./Icon";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  /** Optional leading Material Symbols icon name. */
  icon?: string;
}

const base =
  "inline-flex items-center justify-center gap-2 rounded font-bold transition-all motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed";

const sizeClass: Record<Size, string> = {
  sm: "px-3 py-1.5 text-body-sm min-h-8",
  md: "px-4 py-2 text-body-md min-h-9",
};

const variantClass: Record<Variant, string> = {
  primary:
    "bg-primary text-on-primary hover:opacity-90 active:scale-95 motion-reduce:active:scale-100 disabled:hover:opacity-50",
  secondary:
    "border border-outline-variant bg-surface-container-lowest text-on-surface hover:bg-surface-container-high hover:border-primary",
  ghost: "text-primary hover:bg-primary-fixed",
  danger:
    "bg-error text-on-error hover:opacity-90 active:scale-95 motion-reduce:active:scale-100",
};

/** Shared action button with variants, sizes, and an optional leading icon. */
export function Button({
  variant = "secondary",
  size = "md",
  icon,
  type,
  className,
  children,
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type ?? "button"}
      className={`${base} ${sizeClass[size]} ${variantClass[variant]}${
        className ? ` ${className}` : ""
      }`}
      {...rest}
    >
      {icon ? <Icon name={icon} className="text-[18px]" /> : null}
      {children}
    </button>
  );
}
