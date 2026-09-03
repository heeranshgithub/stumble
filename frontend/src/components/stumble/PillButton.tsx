import Link from "next/link";
import type { ComponentProps } from "react";

type Variant = "ink" | "paper" | "stumble";

const styles: Record<Variant, string> = {
  ink: "bg-ink text-paper",
  paper: "bg-paper text-ink",
  stumble: "bg-stumble text-paper",
};

const base =
  "inline-flex w-full items-center justify-center gap-2 rounded-pill px-5 py-3.5 text-[15px] font-extrabold " +
  "transition-transform duration-150 ease-out-expo active:scale-[0.98] disabled:opacity-50";

type ButtonProps = ComponentProps<"button"> & { variant?: Variant; href?: undefined };
type LinkProps = ComponentProps<typeof Link> & { variant?: Variant; href: string };

/** The primary action. One per screen, full width, pill. */
export function PillButton(props: ButtonProps | LinkProps) {
  const { variant = "ink", className = "", children, ...rest } = props;
  const cls = `${base} ${styles[variant]} ${className}`;
  if ("href" in rest && typeof rest.href === "string") {
    return (
      <Link {...(rest as ComponentProps<typeof Link>)} className={cls}>
        {children}
      </Link>
    );
  }
  return (
    <button type="button" {...(rest as ComponentProps<"button">)} className={cls}>
      {children}
    </button>
  );
}
