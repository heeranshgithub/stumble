import { QrCode } from "@/components/shell/QrCode";
import { TabBar } from "@/components/stumble/TabBar";

/**
 * On a phone: the app, edge to edge, window scroll.
 * On a wide screen: the same app inside a phone frame on an ink stage, with a brand panel and a QR
 * code of this URL beside it. The product is built for a thumb; the stage says so instead of apologising.
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-dvh bg-paper md:flex md:items-center md:justify-center md:gap-20 md:bg-ink md:px-10 md:py-8">
      <aside className="hidden text-paper md:block md:w-[320px]">
        <p className="text-[44px] font-black leading-none tracking-[-0.03em]">
          Stumble<span className="text-stumble">.</span>
        </p>
        <p className="mt-3 text-lg leading-snug text-paper-2">
          Speak French. The words you can&apos;t find become the words you review.
        </p>
        <p className="mt-10 text-sm font-bold">Built for your phone.</p>
        <p className="mb-4 text-sm text-paper-2">Scan to open it there, or use it right here: click the mic and talk.</p>
        <QrCode />
      </aside>

      <div className="md:h-[min(844px,calc(100dvh-4rem))] md:w-[410px] md:flex-none md:rounded-[54px] md:bg-black md:p-[10px] md:shadow-[0_40px_80px_-30px_rgba(0,0,0,0.8)]">
        <div className="flex min-h-dvh w-full flex-col bg-paper md:h-full md:min-h-0 md:overflow-y-auto md:rounded-[44px] md:[scrollbar-width:none]">
          <main className="flex flex-1 flex-col">{children}</main>
          <TabBar />
        </div>
      </div>
    </div>
  );
}
