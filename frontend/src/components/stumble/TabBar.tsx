"use client";

import { BarChart3, Home, Layers, Map } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const tabs = [
  { href: "/", label: "Today", Icon: Home },
  { href: "/scenes", label: "Scenes", Icon: Map },
  { href: "/deck", label: "Deck", Icon: Layers },
  { href: "/progress", label: "Progress", Icon: BarChart3 },
] as const;

const hiddenOn = ["/scene/", "/onboarding", "/review"];

export function TabBar() {
  const pathname = usePathname();
  if (hiddenOn.some((p) => pathname.startsWith(p))) return null;

  return (
    <nav aria-label="Primary" className="shrink-0 border-t border-ink/10 bg-paper pb-safe">
      <ul className="flex justify-around px-2 pt-2 pb-2">
        {tabs.map(({ href, label, Icon }) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <li key={href}>
              <Link
                href={href}
                aria-current={active ? "page" : undefined}
                className={`flex flex-col items-center gap-1 px-3 py-1 text-[10px] font-extrabold ${active ? "text-ink" : "text-ink/65"}`}
              >
                <Icon className="size-5" strokeWidth={active ? 2.5 : 2} />
                {label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
