// src/components/ErrorBoundary.tsx
import React, { Component, ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("React 渲染错误:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-900 p-6 flex items-center justify-center">
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-8 max-w-2xl w-full">
            <h2 className="text-xl font-bold text-red-400 mb-4">
              ⚠️ 页面渲染出错
            </h2>
            <p className="text-slate-300 mb-4">
              错误信息：{this.state.error?.message || "未知错误"}
            </p>
            <pre className="bg-slate-950 rounded-lg p-4 text-sm text-red-300 overflow-auto max-h-96">
              {this.state.error?.stack}
            </pre>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors"
            >
              刷新页面
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
