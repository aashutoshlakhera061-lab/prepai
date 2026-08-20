export default function ErrorBanner({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <div className="bg-red-950 border border-red-800 text-red-300 rounded-lg px-4 py-3 mb-4 max-w-lg">
      {message}
    </div>
  );
}
