import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { toast } from "sonner";
import { authAPI } from "@/services/api";
import { useRecaptcha } from "@/hooks/use-recaptcha";
import { Loader2, AlertCircle } from "lucide-react";

const Signup = () => {
  const navigate = useNavigate();
  const siteKey = import.meta.env.VITE_RECAPTCHA_SITE_KEY;
  const { containerRef, isVerified, initRecaptcha, getToken, resetRecaptcha } =
    useRecaptcha(siteKey);

  const [loading, setLoading] = useState(false);
  const [recaptchaError, setRecaptchaError] = useState("");
  const [formData, setFormData] = useState({
    name: "",
    username: "",
    email: "",
    password: "",
  });

  useEffect(() => {
    // Initialize reCAPTCHA when component mounts
    const timer = setTimeout(() => {
      initRecaptcha();
    }, 100);
    return () => clearTimeout(timer);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (
      !formData.name ||
      !formData.username ||
      !formData.email ||
      !formData.password
    ) {
      toast.error("Please fill in all fields");
      return;
    }

    if (!isVerified) {
      setRecaptchaError("Please verify that you are not a robot");
      toast.error("Please complete the reCAPTCHA verification");
      return;
    }

    const token = getToken();
    if (!token) {
      setRecaptchaError("reCAPTCHA verification failed. Please try again.");
      toast.error("reCAPTCHA verification failed. Please try again.");
      return;
    }

    setLoading(true);
    setRecaptchaError("");
    try {
      const response = await authAPI.signup({
        ...formData,
        recaptcha_token: token,
      });
      toast.success(response.message);
      // Show usage limit message if provided
      // if (response.usage_limit_message) {
      //   toast.info(response.usage_limit_message, { duration: 5000 });
      // }
      resetRecaptcha();
      navigate("/login");
    } catch (error: any) {
      toast.error(
        error.response?.data?.detail || "Signup failed. Please try again."
      );
      resetRecaptcha();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold">
            Create an account
          </CardTitle>
          <CardDescription>Enter your details to get started</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                type="text"
                placeholder="John Doe"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                placeholder="johndoe"
                value={formData.username}
                onChange={(e) =>
                  setFormData({ ...formData, username: e.target.value })
                }
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={formData.email}
                onChange={(e) =>
                  setFormData({ ...formData, email: e.target.value })
                }
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={formData.password}
                onChange={(e) =>
                  setFormData({ ...formData, password: e.target.value })
                }
                disabled={loading}
              />
            </div>

            {/* reCAPTCHA Widget */}
            <div className="space-y-2">
              <div ref={containerRef} className="flex justify-center" />
              {recaptchaError && (
                <div className="flex items-center gap-2 text-sm text-destructive">
                  <AlertCircle className="h-4 w-4" />
                  <span>{recaptchaError}</span>
                </div>
              )}
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={loading || !isVerified}
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating account...
                </>
              ) : (
                "Sign up"
              )}
            </Button>
          </form>
          <div className="mt-4 text-center text-sm">
            Already have an account?{" "}
            <Link
              to="/login"
              className="text-primary hover:underline font-medium"
            >
              Login
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Signup;
