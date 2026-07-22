/**
 * Material Symbols icon. Decorative by default (hidden from assistive tech);
 * icon-only controls must supply their own accessible name on the wrapping
 * button/link.
 */
interface IconProps {
  name: string;
  className?: string;
}

export function Icon({ name, className }: IconProps) {
  return (
    <span
      className={`material-symbols-outlined${className ? ` ${className}` : ""}`}
      aria-hidden="true"
    >
      {name}
    </span>
  );
}
