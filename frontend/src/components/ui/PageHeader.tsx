import type { ReactNode } from "react";


interface PageHeaderProps {
  title: string;
  description?: string;
  action?: ReactNode;
}

export function PageHeader({ title, description, action }: PageHeaderProps) {
  return (
    <header className="flex items-center justify-between pb-12">
      <div className="space-y-1">
        <h1 className="text-3xl font-semibold tracking-tight text-slate-100">
          {title}
        </h1>
        {description && (
          <p className="text-sm tracking-wide text-slate-500">{description}</p>
        )}
      </div>
      {action && <div>{action}</div>}
    </header>
  );
}