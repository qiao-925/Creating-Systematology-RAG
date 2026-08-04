import Link from "next/link";
import { FileQuestion } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex flex-1 items-center justify-center">
      <div className="text-center space-y-4 animate-in fade-in duration-300">
        <div className="flex justify-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-muted">
            <FileQuestion className="h-7 w-7 text-muted-foreground" />
          </div>
        </div>
        <h1 className="text-2xl font-semibold text-foreground">页面未找到</h1>
        <p className="text-sm text-muted-foreground max-w-sm">
          你访问的页面不存在或已被移除。请检查 URL 是否正确。
        </p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
        >
          返回首页
        </Link>
      </div>
    </div>
  );
}
