export default function Loading() {
  return (
    <div className="flex flex-1 items-center justify-center">
      <div className="text-center space-y-4">
        <div className="h-8 w-8 rounded-full border-2 border-emerald-400 border-t-transparent animate-spin mx-auto" />
        <p className="text-sm text-muted-foreground">加载中...</p>
      </div>
    </div>
  );
}
