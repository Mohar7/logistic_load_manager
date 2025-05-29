import {Navigate} from "@tanstack/react-router";
import {useAuthStore} from "@/store/auth";

export function IndexComponent() {
  const { isAuthenticated } = useAuthStore();
  
  if (isAuthenticated) {
    return <Navigate to="/dashboard" />;
  }
  
  return <Navigate to="/login" />;
}