export default function Loading() {
  return (
    <div className="flex flex-1 flex-col bg-paper">
      <div className="px-5 pt-14 pb-5">
        <div className="h-3 w-20 rounded-full bg-ink/15" />
        <div className="mt-3 h-8 w-3/4 rounded-md bg-ink/15" />
        <div className="mt-2 h-3 w-1/2 rounded-full bg-ink/15" />
      </div>
      <div className="space-y-3 px-5 pt-4">
        <div className="h-9 rounded-xl bg-ink/8" />
        <div className="h-9 rounded-xl bg-ink/8" />
      </div>
    </div>
  );
}
