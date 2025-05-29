import {createFileRoute, useNavigate} from "@tanstack/react-router";
import {useState} from "react";
import {useAuthStore} from "@/store/auth";
import {Button} from "@/components/ui/button";
import {Input} from "@/components/ui/input";
import {Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle} from "@/components/ui/card";
import {Label} from "@/components/ui/label";
import {toast} from "sonner";


export const Route = createFileRoute('/login')({
	component: LoginPage,
});

export function LoginPage() {
	const [username, setUsername] = useState("");
	const [password, setPassword] = useState("");
	const [isLoading, setIsLoading] = useState(false);
	const { login } = useAuthStore();
	const navigate = useNavigate();
	
	const handleLogin = async (e: React.FormEvent) => {
		e.preventDefault();
		
		if (!username || !password) {
			toast.error("Please enter both username and password");
			return;
		}
		
		setIsLoading(true);
		
		try {
			// For demonstration, we're not actually calling an API
			// In a real app, you would verify credentials with your backend
			
			// Simulate API call
			await new Promise(resolve => setTimeout(resolve, 1000));
			
			// Mock user data
			login("fake-jwt-token", {
				id: 1,
				username,
				role: "dispatcher",
			});
			
			toast.success("Login successful!");
			navigate({ to: "/dashboard" });
		} catch (error) {
			console.error("Login failed:", error);
			toast.error("Login failed. Please check your credentials.");
		} finally {
			setIsLoading(false);
		}
	};
	
	return (
		<div className="flex items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900">
			<div className="w-full max-w-md">
				<Card>
					<CardHeader className="space-y-1">
						<CardTitle className="text-2xl font-bold text-center">Logistics System</CardTitle>
						<CardDescription className="text-center">Enter your credentials to login</CardDescription>
					</CardHeader>
					<CardContent>
						<form onSubmit={handleLogin} className="space-y-4">
							<div className="space-y-2">
								<Label htmlFor="username">Username</Label>
								<Input
									id="username"
									placeholder="Enter your username"
									value={username}
									onChange={(e) => setUsername(e.target.value)}
									required
								/>
							</div>
							<div className="space-y-2">
								<Label htmlFor="password">Password</Label>
								<Input
									id="password"
									type="password"
									placeholder="Enter your password"
									value={password}
									onChange={(e) => setPassword(e.target.value)}
									required
								/>
							</div>
							<Button type="submit" className="w-full" disabled={isLoading}>
								{isLoading ? "Logging in..." : "Login"}
							</Button>
						</form>
					</CardContent>
					<CardFooter className="text-center text-sm text-muted-foreground">
						<p className="mx-auto">
							For demo purposes, enter any username and password.
						</p>
					</CardFooter>
				</Card>
			</div>
		</div>
	);
}