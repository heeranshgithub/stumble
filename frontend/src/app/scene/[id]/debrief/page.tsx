import { DebriefScreen } from "@/components/screens/DebriefScreen";

export default async function DebriefPage({ params, searchParams }: PageProps<"/scene/[id]/debrief">) {
  const { id } = await params;
  const { session } = await searchParams;
  const sessionId = typeof session === "string" && session ? session : null;
  return <DebriefScreen sceneId={id} sessionId={sessionId} />;
}
