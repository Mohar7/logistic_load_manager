import {z} from "zod";
import {useForm} from "react-hook-form";
import {zodResolver} from "@hookform/resolvers/zod";
import {type CompanyCreate, CompanyCreateSchema} from "@/types/models";
import {Button} from "@/components/ui/button";
import {Form, FormControl, FormField, FormItem, FormLabel, FormMessage,} from "@/components/ui/form";
import {Input} from "@/components/ui/input";

interface CompanyFormProps {
	onSubmit: (data: CompanyCreate) => void;
	isSubmitting?: boolean;
	defaultValues?: CompanyCreate;
}

export function CompanyForm({
	                            onSubmit,
	                            isSubmitting = false,
	                            defaultValues = {
		                            name: "",
		                            usdot: 0,
		                            carrier_identifier: "",
		                            mc: 0,
	                            },
                            }: CompanyFormProps) {
	const form = useForm<z.infer<typeof CompanyCreateSchema>>({
		resolver: zodResolver(CompanyCreateSchema),
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
							<FormLabel>Company Name</FormLabel>
							<FormControl>
								<Input placeholder="Enter company name" {...field} />
							</FormControl>
							<FormMessage />
						</FormItem>
					)}
				/>
				
				<FormField
					control={form.control}
					name="usdot"
					render={({ field }) => (
						<FormItem>
							<FormLabel>USDOT Number</FormLabel>
							<FormControl>
								<Input
									type="number"
									placeholder="Enter USDOT number"
									{...field}
									onChange={e => field.onChange(parseInt(e.target.value) || 0)}
								/>
							</FormControl>
							<FormMessage />
						</FormItem>
					)}
				/>
				
				<FormField
					control={form.control}
					name="carrier_identifier"
					render={({ field }) => (
						<FormItem>
							<FormLabel>Carrier Identifier</FormLabel>
							<FormControl>
								<Input placeholder="Enter carrier identifier" {...field} />
							</FormControl>
							<FormMessage />
						</FormItem>
					)}
				/>
				
				<FormField
					control={form.control}
					name="mc"
					render={({ field }) => (
						<FormItem>
							<FormLabel>MC Number</FormLabel>
							<FormControl>
								<Input
									type="number"
									placeholder="Enter MC number"
									{...field}
									onChange={e => field.onChange(parseInt(e.target.value) || 0)}
								/>
							</FormControl>
							<FormMessage />
						</FormItem>
					)}
				/>
				
				<div className="flex justify-end">
					<Button type="submit" disabled={isSubmitting}>
						{isSubmitting ? "Saving..." : "Save Company"}
					</Button>
				</div>
			</form>
		</Form>
	);
}