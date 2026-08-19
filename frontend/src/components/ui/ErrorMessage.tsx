import { Card } from "./Card";

export function ErrorMessage({ message }: { message: string }) {
  return (
    <Card className="border-red-200 bg-red-50">
      <p className="text-sm text-red-700">Error: {message}</p>
    </Card>
  );
}