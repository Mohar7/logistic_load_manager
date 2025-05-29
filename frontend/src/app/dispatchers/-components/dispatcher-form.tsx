import {z} from "zod";
import {useForm} from "react-hook-form";
import {zodResolver} from "@hookform/resolvers/zod";
import {type DispatcherCreate, DispatcherCreateSchema} from "@/types/models";
import {Button} from "@/components/ui/button";
import {Form, FormControl, FormField, FormItem, FormLabel, FormMessage,} from "@/components/ui/form";
import {Input} from "@/components/ui/input";

interface DispatcherFormProps {
  onSubmit: (data: DispatcherCreate) => void;
  isSubmitting?: boolean;
  defaultValues?: DispatcherCreate;
}

export function DispatcherForm({
  onSubmit,
  isSubmitting = false,
  defaultValues = {
    name: "",
    telegram_id: 0,
  },
}: DispatcherFormProps) {
  const form = useForm<z.infer<typeof DispatcherCreateSchema>>({
    resolver: zodResolver(DispatcherCreateSchema),
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
              <FormLabel>Dispatcher Name</FormLabel>
              <FormControl>
                <Input placeholder="Enter dispatcher name" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="telegram_id"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Telegram ID</FormLabel>
              <FormControl>
                <Input
                  type="number"
                  placeholder="Enter Telegram ID"
                  {...field}
                  value={field.value || ""}
                  onChange={(e) => {
                    const value = e.target.value;
                    field.onChange(value ? parseInt(value) : 0);
                  }}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="flex justify-end">
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Saving..." : "Save Dispatcher"}
          </Button>
        </div>
      </form>
    </Form>
  );
}