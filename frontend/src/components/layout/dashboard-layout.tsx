import React from "react";
import {Link, useNavigate} from "@tanstack/react-router";
import {cn} from "@/lib/utils";
import {Button} from "@/components/ui/button";
import {Building2, Headset, LayoutDashboard, LogOut, Menu, Package, Truck, X,} from "lucide-react";
import {useAuthStore} from "@/store/auth";

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const { logout, user } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate({ to: "/login", search: {} });
  };

  const navItems = [
    {
      icon: <LayoutDashboard className="h-5 w-5 mr-2" />,
      name: "Dashboard",
      href: "/dashboard"
    },
    {
      icon: <Package className="h-5 w-5 mr-2" />,
      name: "Loads",
      href: "/loads"
    },
    {
      icon: <Truck className="h-5 w-5 mr-2" />,
      name: "Drivers",
      href: "/drivers"
    },
    {
      icon: <Building2 className="h-5 w-5 mr-2" />,
      name: "Companies",
      href: "/companies"
    },
    {
      icon: <Headset className="h-5 w-5 mr-2" />,
      name: "Dispatchers",
      href: "/dispatchers"
    },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile sidebar toggle */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setSidebarOpen(!sidebarOpen)}
          aria-label="Toggle Menu"
        >
          {sidebarOpen ? (
            <X className="h-6 w-6" />
          ) : (
            <Menu className="h-6 w-6" />
          )}
        </Button>
      </div>

      {/* Sidebar */}
      <div
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 bg-card shadow-lg transform transition-transform duration-200 ease-in-out lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex flex-col h-full">
          <div className="p-4 border-b">
            <h1 className="text-xl font-bold">Logistics System</h1>
            {user && (
              <p className="text-sm text-muted-foreground mt-1">
                {user.username} ({user.role})
              </p>
            )}
          </div>

          <nav className="flex-1 p-4 space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.href}
                to={item.href}
                search={{}}
                className="flex items-center px-4 py-2 text-foreground hover:bg-muted rounded-md transition-colors"
                onClick={() => setSidebarOpen(false)}
              >
                {item.icon}
                <span>{item.name}</span>
              </Link>
            ))}
          </nav>

          <div className="p-4 border-t">
            <Button
              variant="outline"
              className="w-full justify-start text-destructive"
              onClick={handleLogout}
            >
              <LogOut className="h-5 w-5 mr-2" />
              <span>Logout</span>
            </Button>
          </div>
        </div>
      </div>

      {/* Overlay to close sidebar on mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <div className="lg:pl-64 min-h-screen">
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}