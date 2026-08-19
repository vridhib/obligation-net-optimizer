import { Card } from "./Card";

export function EmptyState({ message }: { message: string }) {
  return (
    <Card className="border-dashed">
      <p className="text-center text-sm text-neutral-500">{message}</p>
    </Card>
  );
}