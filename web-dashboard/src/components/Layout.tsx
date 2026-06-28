// src/components/Layout.tsx
import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Menu, X, PiggyBank } from "lucide-react";

const navItems = [
  { path: "/", label: "监控大屏" },
  { path: "/backtest", label: "策略回测" },
  { path: "/explore", label: "数据探索" },
  { path: "/simulation", label: "模拟盘" },
  { path: "/l1", label: "L1观察" },
];

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const handleNav = (path: string) => {
    navigate(path);
    setMobileMenuOpen(false);
  };

  return (
    <div className="min-h-screen bg-slate-900">
      {/* 顶部导航栏 */}
      <nav className="bg-slate-800 border-b border-slate-700/50 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-2">
              <PiggyBank className="w-7 h-7 text-pink-500" />
              <span className="text-lg font-bold text-slate-50">猪周期量化</span>
            </div>

            {/* 桌面端导航 */}
            <div className="hidden md:flex items-center gap-1">
              {navItems.map((item) => (
                <button
                  key={item.path}
                  onClick={() => handleNav(item.path)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    location.pathname === item.path
                      ? "bg-slate-700 text-slate-50"
                      : "text-slate-400 hover:text-slate-50 hover:bg-slate-700/50"
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>

            {/* 移动端菜单按钮 */}
            <button
              className="md:hidden p-2 rounded-lg text-slate-400 hover:text-slate-50 hover:bg-slate-700"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* 移动端导航菜单 */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-slate-800 border-t border-slate-700/50">
            <div className="px-4 py-2 space-y-1">
              {navItems.map((item) => (
                <button
                  key={item.path}
                  onClick={() => handleNav(item.path)}
                  className={`block w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    location.pathname === item.path
                      ? "bg-slate-700 text-slate-50"
                      : "text-slate-400 hover:text-slate-50 hover:bg-slate-700/50"
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
        )}
      </nav>

      {/* 主内容区 */}
      <main className="max-w-7xl mx-auto p-4 sm:p-6">
        {children}
      </main>
    </div>
  );
}
