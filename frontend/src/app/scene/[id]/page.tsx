import { SceneScreen } from "@/components/screens/SceneScreen";

export default async function ScenePage({ params }: PageProps<"/scene/[id]">) {
  const { id } = await params;
  return <SceneScreen sceneId={id} />;
}
