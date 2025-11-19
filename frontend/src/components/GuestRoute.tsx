import { Navigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

interface GuestRouteProps {
  children: React.ReactNode;
}

const GuestRoute = ({ children }: GuestRouteProps) => {
  const { isAuthenticated, loading } = useAuth();

  // While loading, don't redirect yet
  if (loading) return null;

  // If already logged in → redirect to /chat
  if (isAuthenticated) {
    return <Navigate to="/chat" replace />;
  }

  // Otherwise allow access
  return <>{children}</>;
};

export default GuestRoute;
