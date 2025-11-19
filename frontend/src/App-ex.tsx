import { useEffect } from "react";
import api from "./services/api";

function App() {

  useEffect(() => {
    const testBackend = async () => {
      try {
        const res = await api.post("/auth/login", {
          login: "hebahassan",
          password: "password123"
        });
        console.log("Backend Response:", res.data);
      } catch (error) {
        console.error("Error connecting to backend:", error);
      }
    };

    testBackend();
  }, []);

  return <div>Testing backend connection...</div>;
}

export default App;
