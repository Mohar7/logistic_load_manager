import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Save,
  Plus,
  X,
  RouteIcon,
  Truck,
  User,
  Calendar,
  DollarSign,
  MapPin,
  Loader2,
  RotateCcw
} from "lucide-react";
import { toast } from "sonner";
import type { Load, Dispatcher } from "@/types/models";

interface LoadEditFormProps {
  load: Load;
  onSubmit: (updateData: Partial<Load>) => void;
  isSubmitting: boolean;
  dispatchers?: Dispatcher[];
}

interface LegFormData {
  id?: number;
  leg_id: string;
  pickup_facility_id: string;
  dropoff_facility_id: string;
  pickup_address: string;
  dropoff_address: string;
  pickup_time: string;
  dropoff_time: string;
  fuel_sur_charge: number;
  distance: number;
  assigned_driver: string;
}

export function LoadEditForm({
  load,
  onSubmit,
  isSubmitting,
  dispatchers = [],
}: LoadEditFormProps): React.ReactElement {
  // Main load data state
  const [formData, setFormData] = useState({
    trip_id: load.trip_id || '',
    pickup_facility: load.pickup_facility || '',
    dropoff_facility: load.dropoff_facility || '',
    pickup_address: load.pickup_address || '',
    dropoff_address: load.dropoff_address || '',
    start_time: load.start_time ? formatDateForInput(load.start_time) : '',
    end_time: load.end_time ? formatDateForInput(load.end_time) : '',
    rate: load.rate || 0,
    rate_per_mile: load.rate_per_mile || 0,
    distance: load.distance || 0,
    assigned_driver: load.assigned_driver || '',
  });

  // Legs state
  const [legs, setLegs] = useState<LegFormData[]>([]);
  const [dispatcherId, setDispatcherId] = useState<number | undefined>(undefined);

  // Initialize legs from load data
  useEffect(() => {
    if (load.legs && load.legs.length > 0) {
      const initialLegs: LegFormData[] = load.legs.map(leg => ({
        id: leg.id,
        leg_id: leg.leg_id || '',
        pickup_facility_id: leg.pickup_facility_id || '',
        dropoff_facility_id: leg.dropoff_facility_id || '',
        pickup_address: leg.pickup_address || '',
        dropoff_address: leg.dropoff_address || '',
        pickup_time: leg.pickup_time ? formatDateForInput(leg.pickup_time) : '',
        dropoff_time: leg.dropoff_time ? formatDateForInput(leg.dropoff_time) : '',
        fuel_sur_charge: leg.fuel_sur_charge || 0,
        distance: leg.distance || 0,
        assigned_driver: leg.assigned_driver || '',
      }));
      setLegs(initialLegs);
    } else {
      // Initialize with one empty leg if none exist
      setLegs([createEmptyLeg()]);
    }
  }, [load]);

  // Helper functions
  function formatDateForInput(dateValue: string | Date): string {
    try {
      const date = new Date(dateValue);
      if (isNaN(date.getTime())) return '';
      return date.toISOString().slice(0, 16);
    } catch {
      return '';
    }
  }

  function createEmptyLeg(): LegFormData {
    return {
      leg_id: `LEG-${Date.now()}`,
      pickup_facility_id: formData.pickup_facility,
      dropoff_facility_id: formData.dropoff_facility,
      pickup_address: formData.pickup_address,
      dropoff_address: formData.dropoff_address,
      pickup_time: formData.start_time,
      dropoff_time: formData.end_time,
      fuel_sur_charge: 0,
      distance: formData.distance / Math.max(legs.length, 1),
      assigned_driver: formData.assigned_driver,
    };
  }

  // Event handlers
  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleLegChange = (legIndex: number, field: string, value: any) => {
    const updatedLegs = [...legs];
    updatedLegs[legIndex] = {
      ...updatedLegs[legIndex],
      [field]: value
    };
    setLegs(updatedLegs);
  };

  const addLeg = () => {
    setLegs([...legs, createEmptyLeg()]);
  };

  const removeLeg = (legIndex: number) => {
    if (legs.length <= 1) {
      toast.error("At least one leg is required");
      return;
    }
    const updatedLegs = legs.filter((_, index) => index !== legIndex);
    setLegs(updatedLegs);
  };

  const fillLegFromTripData = (legIndex: number) => {
    const updatedLegs = [...legs];
    updatedLegs[legIndex] = {
      ...updatedLegs[legIndex],
      pickup_facility_id: formData.pickup_facility,
      dropoff_facility_id: formData.dropoff_facility,
      pickup_address: formData.pickup_address,
      dropoff_address: formData.dropoff_address,
      pickup_time: formData.start_time,
      dropoff_time: formData.end_time,
      assigned_driver: formData.assigned_driver,
    };
    setLegs(updatedLegs);
    toast.success("Leg updated with trip data");
  };

  const resetForm = () => {
    setFormData({
      trip_id: load.trip_id || '',
      pickup_facility: load.pickup_facility || '',
      dropoff_facility: load.dropoff_facility || '',
      pickup_address: load.pickup_address || '',
      dropoff_address: load.dropoff_address || '',
      start_time: load.start_time ? formatDateForInput(load.start_time) : '',
      end_time: load.end_time ? formatDateForInput(load.end_time) : '',
      rate: load.rate || 0,
      rate_per_mile: load.rate_per_mile || 0,
      distance: load.distance || 0,
      assigned_driver: load.assigned_driver || '',
    });

    if (load.legs && load.legs.length > 0) {
      const resetLegs: LegFormData[] = load.legs.map(leg => ({
        id: leg.id,
        leg_id: leg.leg_id || '',
        pickup_facility_id: leg.pickup_facility_id || '',
        dropoff_facility_id: leg.dropoff_facility_id || '',
        pickup_address: leg.pickup_address || '',
        dropoff_address: leg.dropoff_address || '',
        pickup_time: leg.pickup_time ? formatDateForInput(leg.pickup_time) : '',
        dropoff_time: leg.dropoff_time ? formatDateForInput(leg.dropoff_time) : '',
        fuel_sur_charge: leg.fuel_sur_charge || 0,
        distance: leg.distance || 0,
        assigned_driver: leg.assigned_driver || '',
      }));
      setLegs(resetLegs);
    }

    setDispatcherId(undefined);
    toast.success("Form reset to original values");
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Validate required fields
    if (!formData.trip_id.trim()) {
      toast.error("Trip ID is required");
      return;
    }

    if (formData.rate <= 0) {
      toast.error("Rate must be greater than 0");
      return;
    }

    // Prepare the update data
    const updateData: Partial<Load> = {
      trip_id: formData.trip_id,
      pickup_facility: formData.pickup_facility,
      dropoff_facility: formData.dropoff_facility,
      pickup_address: formData.pickup_address,
      dropoff_address: formData.dropoff_address,
      start_time: formData.start_time,
      end_time: formData.end_time,
      rate: formData.rate,
      rate_per_mile: formData.rate_per_mile,
      distance: formData.distance,
      assigned_driver: formData.assigned_driver,
      legs: legs.map(leg => ({
        id: leg.id,
        leg_id: leg.leg_id,
        pickup_facility_id: leg.pickup_facility_id,
        dropoff_facility_id: leg.dropoff_facility_id,
        pickup_address: leg.pickup_address,
        dropoff_address: leg.dropoff_address,
        pickup_time: leg.pickup_time,
        dropoff_time: leg.dropoff_time,
        fuel_sur_charge: leg.fuel_sur_charge,
        distance: leg.distance,
        assigned_driver: leg.assigned_driver,
      }))
    };

    onSubmit(updateData);
  };

  return (
    <div className="max-h-[80vh] overflow-y-auto pr-2">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Header Info */}
        <Alert>
          <AlertDescription>
            <div className="flex items-center justify-between">
              <span>Editing Load: <strong>#{load.trip_id}</strong></span>
              <Badge variant="outline">Direct Form Editor</Badge>
            </div>
          </AlertDescription>
        </Alert>

        {/* Dispatcher Selection */}
        {dispatchers.length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center space-x-2">
                <User className="h-4 w-4" />
                <span>Dispatcher Assignment</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Select
                onValueChange={(value) => setDispatcherId(value ? parseInt(value) : undefined)}
                value={dispatcherId?.toString()}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a dispatcher (optional)" />
                </SelectTrigger>
                <SelectContent>
                  {dispatchers.map((dispatcher) => (
                    <SelectItem key={dispatcher.id} value={dispatcher.id.toString()}>
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                        <span>{dispatcher.name}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </CardContent>
          </Card>
        )}

        {/* Trip Information */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center space-x-2">
              <Truck className="h-5 w-5" />
              <span>Trip Information</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Basic Info */}
              <div>
                <Label htmlFor="trip_id">Trip ID *</Label>
                <Input
                  id="trip_id"
                  value={formData.trip_id}
                  onChange={(e) => handleInputChange('trip_id', e.target.value)}
                  placeholder="Enter trip ID"
                  required
                />
              </div>
              
              <div>
                <Label htmlFor="assigned_driver">Assigned Driver</Label>
                <Input
                  id="assigned_driver"
                  value={formData.assigned_driver}
                  onChange={(e) => handleInputChange('assigned_driver', e.target.value)}
                  placeholder="Enter driver name"
                />
              </div>

              {/* Location Info */}
              <div>
                <Label htmlFor="pickup_facility">Pickup Facility</Label>
                <Input
                  id="pickup_facility"
                  value={formData.pickup_facility}
                  onChange={(e) => handleInputChange('pickup_facility', e.target.value)}
                  placeholder="Enter pickup facility code"
                />
              </div>

              <div>
                <Label htmlFor="dropoff_facility">Dropoff Facility</Label>
                <Input
                  id="dropoff_facility"
                  value={formData.dropoff_facility}
                  onChange={(e) => handleInputChange('dropoff_facility', e.target.value)}
                  placeholder="Enter dropoff facility code"
                />
              </div>

              <div>
                <Label htmlFor="pickup_address">Pickup Address</Label>
                <Input
                  id="pickup_address"
                  value={formData.pickup_address}
                  onChange={(e) => handleInputChange('pickup_address', e.target.value)}
                  placeholder="Enter pickup address"
                />
              </div>

              <div>
                <Label htmlFor="dropoff_address">Dropoff Address</Label>
                <Input
                  id="dropoff_address"
                  value={formData.dropoff_address}
                  onChange={(e) => handleInputChange('dropoff_address', e.target.value)}
                  placeholder="Enter dropoff address"
                />
              </div>

              {/* Time Info */}
              <div>
                <Label htmlFor="start_time">Start Time</Label>
                <Input
                  id="start_time"
                  type="datetime-local"
                  value={formData.start_time}
                  onChange={(e) => handleInputChange('start_time', e.target.value)}
                />
              </div>

              <div>
                <Label htmlFor="end_time">End Time</Label>
                <Input
                  id="end_time"
                  type="datetime-local"
                  value={formData.end_time}
                  onChange={(e) => handleInputChange('end_time', e.target.value)}
                />
              </div>

              {/* Financial Info */}
              <div>
                <Label htmlFor="rate">Rate ($) *</Label>
                <Input
                  id="rate"
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.rate}
                  onChange={(e) => handleInputChange('rate', parseFloat(e.target.value) || 0)}
                  placeholder="Enter total rate"
                  required
                />
              </div>

              <div>
                <Label htmlFor="rate_per_mile">Rate per Mile ($)</Label>
                <Input
                  id="rate_per_mile"
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.rate_per_mile}
                  onChange={(e) => handleInputChange('rate_per_mile', parseFloat(e.target.value) || 0)}
                  placeholder="Enter rate per mile"
                />
              </div>

              <div className="md:col-span-2">
                <Label htmlFor="distance">Distance (miles)</Label>
                <Input
                  id="distance"
                  type="number"
                  step="0.1"
                  min="0"
                  value={formData.distance}
                  onChange={(e) => handleInputChange('distance', parseFloat(e.target.value) || 0)}
                  placeholder="Enter total distance"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Load Legs */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center space-x-2">
                <RouteIcon className="h-5 w-5" />
                <span>Load Legs</span>
                <Badge variant="outline">{legs.length} legs</Badge>
              </CardTitle>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={addLeg}
              >
                <Plus className="h-4 w-4 mr-1" />
                Add Leg
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 max-h-[50vh] overflow-y-auto pr-2">
              {legs.map((leg, index) => (
                <Card key={index} className="bg-gray-50">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium">Leg {index + 1}</h4>
                      <div className="flex items-center space-x-2">
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => fillLegFromTripData(index)}
                          title="Fill with trip data"
                        >
                          <RotateCcw className="h-4 w-4" />
                        </Button>
                        {legs.length > 1 && (
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => removeLeg(index)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Leg Basic Info */}
                      <div>
                        <Label>Leg ID</Label>
                        <Input
                          value={leg.leg_id}
                          onChange={(e) => handleLegChange(index, 'leg_id', e.target.value)}
                          placeholder="Enter leg ID"
                        />
                      </div>

                      <div>
                        <Label>Assigned Driver</Label>
                        <Input
                          value={leg.assigned_driver}
                          onChange={(e) => handleLegChange(index, 'assigned_driver', e.target.value)}
                          placeholder="Enter driver name"
                        />
                      </div>

                      {/* Facility IDs */}
                      <div>
                        <Label>Pickup Facility ID</Label>
                        <Input
                          value={leg.pickup_facility_id}
                          onChange={(e) => handleLegChange(index, 'pickup_facility_id', e.target.value)}
                          placeholder="Enter pickup facility ID"
                        />
                      </div>

                      <div>
                        <Label>Dropoff Facility ID</Label>
                        <Input
                          value={leg.dropoff_facility_id}
                          onChange={(e) => handleLegChange(index, 'dropoff_facility_id', e.target.value)}
                          placeholder="Enter dropoff facility ID"
                        />
                      </div>

                      {/* Addresses */}
                      <div>
                        <Label>Pickup Address</Label>
                        <Input
                          value={leg.pickup_address}
                          onChange={(e) => handleLegChange(index, 'pickup_address', e.target.value)}
                          placeholder="Enter pickup address"
                        />
                      </div>

                      <div>
                        <Label>Dropoff Address</Label>
                        <Input
                          value={leg.dropoff_address}
                          onChange={(e) => handleLegChange(index, 'dropoff_address', e.target.value)}
                          placeholder="Enter dropoff address"
                        />
                      </div>

                      {/* Times */}
                      <div>
                        <Label>Pickup Time</Label>
                        <Input
                          type="datetime-local"
                          value={leg.pickup_time}
                          onChange={(e) => handleLegChange(index, 'pickup_time', e.target.value)}
                        />
                      </div>

                      <div>
                        <Label>Dropoff Time</Label>
                        <Input
                          type="datetime-local"
                          value={leg.dropoff_time}
                          onChange={(e) => handleLegChange(index, 'dropoff_time', e.target.value)}
                        />
                      </div>

                      {/* Financial */}
                      <div>
                        <Label>Distance (miles)</Label>
                        <Input
                          type="number"
                          step="0.1"
                          min="0"
                          value={leg.distance}
                          onChange={(e) => handleLegChange(index, 'distance', parseFloat(e.target.value) || 0)}
                          placeholder="Enter distance"
                        />
                      </div>

                      <div>
                        <Label>Fuel Surcharge ($)</Label>
                        <Input
                          type="number"
                          step="0.01"
                          min="0"
                          value={leg.fuel_sur_charge}
                          onChange={(e) => handleLegChange(index, 'fuel_sur_charge', parseFloat(e.target.value) || 0)}
                          placeholder="Enter fuel surcharge"
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Form Actions */}
        <DialogFooter className="sticky bottom-0 bg-white border-t pt-4">
          <Button
            type="button"
            variant="outline"
            onClick={resetForm}
            disabled={isSubmitting}
          >
            <RotateCcw className="mr-2 h-4 w-4" />
            Reset
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Updating...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Update Load
              </>
            )}
          </Button>
        </DialogFooter>
      </form>
    </div>
  );
}