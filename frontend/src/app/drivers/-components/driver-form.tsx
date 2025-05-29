import {z} from "zod";
import {useForm} from "react-hook-form";
import {zodResolver} from "@hookform/resolvers/zod";
import {type Company, type DriverCreate, DriverCreateSchema} from "@/types/models";
import {Button} from "@/components/ui/button";
import {Form, FormControl, FormField, FormItem, FormLabel, FormMessage,} from "@/components/ui/form";
import {Input} from "@/components/ui/input";
import {Select, SelectContent, SelectItem, SelectTrigger, SelectValue,} from "@/components/ui/select";

interface DriverFormProps {
	onSubmit: (data: DriverCreate) => void;
	isSubmitting?: boolean;
	defaultValues?: DriverCreate;
	companies: Company[];
}

export function DriverForm({
	                           onSubmit,
	                           isSubmitting = false,
	                           defaultValues = {
		                           name: "",
		                           company_id: 0,
		                           chat_id: null,
	                           },
	                           companies = [],
                           }: DriverFormProps) {
	const form = useForm<z.infer<typeof DriverCreateSchema>>({
		resolver: zodResolver(DriverCreateSchema),
		defaultValues,
	});
	
	return (
		<Form {...form}>
			<form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
				<FormField
					control={form.control}
					name="name"
					render={({ field }) => (
						<FormItem>
							<FormLabel>Driver Name</FormLabel>
							<FormControl>
								<Input placeholder="Enter driver name" {...field} />
							</FormControl>
							<FormMessage />
						</FormItem>
					)}
				/>
				
				<FormField
					control={form.control}
					name="company_id"
					render={({ field }) => (
						<FormItem>
							<FormLabel>Company</FormLabel>
							<Select
								onValueChange={(value) => field.onChange(parseInt(value))}
								defaultValue={field.value ? field.value.toString() : undefined}
							>
								<FormControl>
									<SelectTrigger>
										<SelectValue placeholder="Select company" />
									</SelectTrigger>
								</FormControl>
								<SelectContent>
									{companies.map((company) => (
										<SelectItem key={company.id} value={company.id.toString()}>
											{company.name}
										</SelectItem>
									))}
								</SelectContent>
							</Select>
							<FormMessage />
						</FormItem>
					)}
				/>
				
				<FormField
					control={form.control}
					name="chat_id"
					render={({ field }) => (
						<FormItem>
							<FormLabel>Telegram Chat ID (Optional)</FormLabel>
							<FormControl>
								<Input
									type="number"
									placeholder="Enter chat ID"
									{...field}
									value={field.value || ""}
									onChange={(e) => {
										const value = e.target.value;
										field.onChange(value ? parseInt(value) : null);
									}}
								/>
							</FormControl>
							<FormMessage />
						</FormItem>
					)}
				/>
				
				<div className="flex justify-end">
					<Button type="submit" disabled={isSubmitting}>
						{isSubmitting ? "Saving..." : "Save Driver"}
					</Button>
				</div>
			</form>
		</Form>
	);
}