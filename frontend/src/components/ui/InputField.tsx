interface InputFieldProps {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
}

export function InputField({
  label,
  value,
  onChange,
  type = "text"
}: InputFieldProps
) {
  return (
    <label className="block">
      <span className="text-sm text-slate-400">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 w-full rounded-md bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
      />
    </label>
  );
}