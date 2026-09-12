export default function Loading() {
  // No scene colour here: this renders before the segment knows which scene it is, and a wrong
  // colour for a frame is worse than none.
  return (
    <div className="flex flex-1 flex-col bg-paper px-5 pt-12">
      <div className="h-3 w-16 rounded-full bg-ink/10" />
      <div className="mt-6 h-3 w-10 rounded-full bg-ink/10" />
      <div className="mt-2 h-6 w-3/4 rounded-md bg-ink/10" />
      <div className="mt-1 h-6 w-1/2 rounded-md bg-ink/10" />
      <div className="flex-1" />
      <div className="mx-auto mb-14 size-[84px] rounded-pill bg-ink/10" />
    </div>
  );
}
