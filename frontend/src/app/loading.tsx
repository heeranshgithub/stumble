export default function Loading() {
  return (
    <div className="flex flex-1 flex-col">
      <div className="flex-[1.3] bg-scene px-5 pt-14">
        <div className="h-3 w-24 rounded-full bg-ink/15" />
        <div className="mt-4 h-9 w-48 rounded-md bg-ink/15" />
        <div className="mt-2 h-9 w-40 rounded-md bg-ink/15" />
        <div className="mt-6 h-12 w-full rounded-pill bg-ink/15" />
      </div>
      <div className="flex-[0.9] bg-ink/5" />
      <div className="flex-[0.8]" />
    </div>
  );
}
