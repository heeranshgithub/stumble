import { SceneScreen } from "@/components/screens/SceneScreen";

export default async function ScenePage({ params, searchParams }: PageProps<"/scene/[id]">) {
  const { id } = await params;
  const { session } = await searchParams;
  const sessionId = typeof session === "string" && session ? session : null;
  return <SceneScreen sceneId={id} resumeId={sessionId} />;
}
