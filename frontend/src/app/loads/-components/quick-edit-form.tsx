import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { DialogFooter } from "@/components/ui/dialog";
import type { Load } from "@/types/models";

interface QuickEditFormProps {
  load: Load;
  onSubmit: (data: Partial<Load>) => void;
  isSubmitting: boolean;
}

export function QuickEditForm({
  load,
  onSubmit,
  isSubmitting
}: QuickEditFormProps): React.ReactElement {
  const [formData, setFormData] = useState({
    trip_id: load.trip_id || '',
    pickup_address: load.pickup_address || '',
    dropoff_address: load.dropoff_address || '',
    rate: load.rate || 0,
    rate_per_mile: load.rate_per_mile || 0,
    distance: load.distance || 0,
    assigned_driver: load.assigned_driver || '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const resetForm = () => {
    setFormData({
      trip_id: load.trip_id || '',
      pickup_address: load.pickup_address || '',
      dropoff_address: load.dropoff_address || '',
      rate: load.rate || 0,
      rate_per_mile: load.rate_per_mile || 0,
      distance: load.distance || 0,
      assigned_driver: load.assigned_driver || '',
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="trip_id">Trip ID</Label>
          <Input
            id="trip_id"
            value={formData.trip_id}
            onChange={(e) => handleChange('trip_id', e.target.value)}
            placeholder="Enter trip ID"
          />
        </div>
        
        <div>
          <Label htmlFor="assigned_driver">Assigned Driver</Label>
          <Input
            id="assigned_driver"
            value={formData.assigned_driver}
            onChange={(e) => handleChange('assigned_driver', e.target.value)}
            placeholder="Enter driver name"
          />
        </div>

        <div>
          <Label htmlFor="pickup_address">Pickup Address</Label>
          <Input
            id="pickup_address"
            value={formData.pickup_address}
            onChange={(e) => handleChange('pickup_address', e.target.value)}
            placeholder="Enter pickup address"
          />
        </div>

        <div>
          <Label htmlFor="dropoff_address">Dropoff Address</Label>
          <Input
            id="dropoff_address"
            value={formData.dropoff_address}
            onChange={(e) => handleChange('dropoff_address', e.target.value)}
            placeholder="Enter dropoff address"
          />
        </div>

        <div>
          <Label htmlFor="rate">Rate ($)</Label>
          <Input
            id="rate"
            type="number"
            step="0.01"
            value={formData.rate}
            onChange={(e) => handleChange('rate', parseFloat(e.target.value) || 0)}
            placeholder="Enter rate"
          />
        </div>

        <div>
          <Label htmlFor="rate_per_mile">Rate per Mile ($)</Label>
          <Input
            id="rate_per_mile"
            type="number"
            step="0.01"
            value={formData.rate_per_mile}
            onChange={(e) => handleChange('rate_per_mile', parseFloat(e.target.value) || 0)}
            placeholder="Enter rate per mile"
          />
        </div>

        <div className="md:col-span-2">
          <Label htmlFor="distance">Distance (miles)</Label>
          <Input
            id="distance"
            type="number"
            step="0.1"
            value={formData.distance}
            onChange={(e) => handleChange('distance', parseFloat(e.target.value) || 0)}
            placeholder="Enter distance"
          />
        </div>
      </div>

      <DialogFooter>
        <Button
          type="button"
          variant="outline"
          onClick={resetForm}
          disabled={isSubmitting}
        >
          Reset
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Updating..." : "Update Load"}
        </Button>
      </DialogFooter>
    </form>
  );
}