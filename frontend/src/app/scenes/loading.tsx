export default function Loading() {
  return (
    <div className="flex flex-1 flex-col" data-scene="cafe">
      <div className="bg-scene px-5 pt-14 pb-5">
        <div className="h-3 w-20 rounded-full bg-ink/15" />
        <div className="mt-2 h-8 w-32 rounded-md bg-ink/15" />
      </div>
      <div className="space-y-4 px-5 pt-4">
        {Array.from({ length: 6 }, (_, i) => (
          <div key={i} className="h-10 rounded-2xl bg-ink/8" />
        ))}
      </div>
    </div>
  );
}
