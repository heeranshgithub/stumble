export default function Loading() {
  return (
    <div className="flex flex-1 flex-col" data-scene="review">
      <div className="bg-scene px-5 pt-14 pb-5">
        <div className="h-3 w-16 rounded-full bg-ink/15" />
        <div className="mt-2 h-8 w-3/4 rounded-md bg-ink/15" />
      </div>
      <div className="space-y-3 px-5 pt-5">
        <div className="h-12 rounded-2xl bg-ink/8" />
        <div className="h-12 rounded-pill bg-ink/8" />
      </div>
    </div>
  );
}
