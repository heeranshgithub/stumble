import { QrCode } from "@/components/shell/QrCode";
import { TabBar } from "@/components/stumble/TabBar";

/**
 * The app shell is exactly one viewport tall and never scrolls itself: `main` is the only scroller,
 * so the tab bar stays put however long a screen gets.
 *
 * On a phone: edge to edge. On a wide screen: the same shell inside a phone frame on an ink stage,
 * with a brand panel and a QR code of this URL beside it.
 *
 * The `min-h-full` wrapper is what lets both kinds of screen work: a short screen's `flex-1` still
 * fills the viewport (Today's blobs divide the height), and a long one grows past it and scrolls.
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="h-dvh bg-paper md:flex md:items-center md:justify-center md:gap-20 md:bg-ink md:px-10 md:py-8">
      <aside className="hidden text-paper md:block md:w-[320px]">
        <p className="text-[44px] font-black leading-none tracking-[-0.03em]">
          Stumble<span className="text-stumble">.</span>
        </p>
        <p className="mt-3 text-lg leading-snug text-paper-2">
          Speak French. The words you can&apos;t find become the words you review.
        </p>
        <p className="mt-10 text-sm font-bold">Built for your phone.</p>
        <p className="mb-4 text-sm text-paper-2">
          Scan to open it there, or use it right here: click the mic and talk.
        </p>
        <QrCode />
      </aside>

      <div className="h-full md:h-[min(844px,calc(100dvh-4rem))] md:w-[410px] md:flex-none md:rounded-[54px] md:bg-black md:p-[10px] md:shadow-[0_40px_80px_-30px_rgba(0,0,0,0.8)]">
        <div className="flex h-full w-full flex-col overflow-hidden bg-paper md:rounded-[44px]">
          <main className="min-h-0 flex-1 overflow-y-auto overscroll-contain md:[scrollbar-width:none]">
            <div className="flex min-h-full flex-col">{children}</div>
          </main>
          <TabBar />
        </div>
      </div>
    </div>
  );
}
