import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  CheckCircle,
  FileText,
  Loader2,
  Plus,
  RouteIcon,
  Truck,
  User,
  Save,
  X,
  Edit,
  Calendar
} from "lucide-react";
import { toast } from "sonner";
import type { Load, Dispatcher, ParsedLoad } from "@/types/models";

interface FullEditFormProps {
  load: Load;
  onSubmit: (data: { text?: string; parsedData?: ParsedLoad; updateData?: Partial<Load> }) => void;
  isSubmitting: boolean;
  parseLoad: (text: string) => Promise<ParsedLoad>;
  dispatchers: Dispatcher[];
}

interface LegData {
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

export function FullEditForm({
  load,
  onSubmit,
  isSubmitting,
  parseLoad,
  dispatchers = [],
}: FullEditFormProps): React.ReactElement {
  // State management
  const [editMode, setEditMode] = useState<'text' | 'form'>('form');
  const [loadText, setLoadText] = useState("");
  const [parsedLoad, setParsedLoad] = useState<ParsedLoad | undefined>(undefined);
  const [isParsing, setIsParsing] = useState(false);
  const [parseError, setParseError] = useState<string | null>(null);

  // Form data state
  const [tripData, setTripData] = useState({
    trip_id: load.trip_id || '',
    pickup_facility: load.pickup_facility || '',
    dropoff_facility: load.dropoff_facility || '',
    pickup_address: load.pickup_address || '',
    dropoff_address: load.dropoff_address || '',
    start_time: load.start_time ? new Date(load.start_time).toISOString().slice(0, 16) : '',
    end_time: load.end_time ? new Date(load.end_time).toISOString().slice(0, 16) : '',
    rate: load.rate || 0,
    rate_per_mile: load.rate_per_mile || 0,
    distance: load.distance || 0,
    assigned_driver: load.assigned_driver || '',
  });

  const [legs, setLegs] = useState<LegData[]>([]);
  const [dispatcherId, setDispatcherId] = useState<number | undefined>(undefined);

  // Initialize legs from load data
  useEffect(() => {
    if (load.legs && load.legs.length > 0) {
      const initialLegs: LegData[] = load.legs.map(leg => ({
        id: leg.id,
        leg_id: leg.leg_id || '',
        pickup_facility_id: leg.pickup_facility_id || '',
        dropoff_facility_id: leg.dropoff_facility_id || '',
        pickup_address: leg.pickup_address || '',
        dropoff_address: leg.dropoff_address || '',
        pickup_time: leg.pickup_time ? new Date(leg.pickup_time).toISOString().slice(0, 16) : '',
        dropoff_time: leg.dropoff_time ? new Date(leg.dropoff_time).toISOString().slice(0, 16) : '',
        fuel_sur_charge: leg.fuel_sur_charge || 0,
        distance: leg.distance || 0,
        assigned_driver: leg.assigned_driver || '',
      }));
      setLegs(initialLegs);
    }
  }, [load]);

  // Format load data for text editing
  const formatLoadForEditing = (loadData: Load): string => {
    const formatDateTime = (dateStr: string | Date | null | undefined) => {
      if (!dateStr) return 'N/A';
      try {
        const date = new Date(dateStr);
        return date.toISOString();
      } catch {
        return String(dateStr);
      }
    };

    let text = `**Trip Information**
**trip id:** ${loadData.trip_id || 'N/A'}
**pick up facility id:** ${loadData.pickup_facility || 'N/A'}
**drop off facility id:** ${loadData.dropoff_facility || 'N/A'}
**pick up address:** ${loadData.pickup_address || 'N/A'}
**drop off address:** ${loadData.dropoff_address || 'N/A'}
**pick up time:** ${formatDateTime(loadData.start_time)}
**drop off time:** ${formatDateTime(loadData.end_time)}
**rate:** ${loadData.rate || 0}
**rate per mile:** ${loadData.rate_per_mile || 0}
**distance:** ${loadData.distance || 0}
**assigned driver:** ${loadData.assigned_driver || 'N/A'}
**is team load:** false

**Load Legs**`;

    if (loadData.legs && loadData.legs.length > 0) {
      loadData.legs.forEach((leg, index) => {
        text += `
**Leg ${index + 1}**
**ID:** ${leg.leg_id || `LEG-${index + 1}`}
**Pickup Facility ID:** ${leg.pickup_facility_id || 'N/A'}
**Dropoff Facility ID:** ${leg.dropoff_facility_id || 'N/A'}
**Pickup Address:** ${leg.pickup_address || 'N/A'}
**Dropoff Address:** ${leg.dropoff_address || 'N/A'}
**Distance:** ${leg.distance || 0} miles
**Fuel Surcharge:** $${leg.fuel_sur_charge || 0}
**Pickup Time:** ${formatDateTime(leg.pickup_time)}
**Dropoff Time:** ${formatDateTime(leg.dropoff_time)}
**Assigned Driver:** ${leg.assigned_driver || 'N/A'}`;
      });
    } else {
      text += '\n**No legs found**';
    }

    return text;
  };

  // Initialize text when switching to text mode
  useEffect(() => {
    if (editMode === 'text' && !loadText) {
      setLoadText(formatLoadForEditing(load));
    }
  }, [editMode, load, loadText]);

  // Parse load text
  const handleParseLoad = async () => {
    if (!loadText.trim()) {
      toast.error("Please enter load text");
      return;
    }

    setIsParsing(true);
    setParseError(null);
    try {
      const result = await parseLoad(loadText);
      setParsedLoad(result);
      
      // Update form data from parsed result
      if (result.tripInfo) {
        setTripData({
          trip_id: result.tripInfo.trip_id || '',
          pickup_facility: result.tripInfo.pick_up_facility_id || result.tripInfo.pickup_facility_id || '',
          dropoff_facility: result.tripInfo.drop_off_facility_id || result.tripInfo.dropoff_facility_id || '',
          pickup_address: result.tripInfo.pick_up_address || result.tripInfo.pickup_address || '',
          dropoff_address: result.tripInfo.drop_off_address || result.tripInfo.dropoff_address || '',
          start_time: result.tripInfo.pick_up_time || result.tripInfo.pickup_time || '',
          end_time: result.tripInfo.drop_off_time || result.tripInfo.dropoff_time || '',
          rate: result.tripInfo.rate || 0,
          rate_per_mile: result.tripInfo.rate_per_mile || 0,
          distance: result.tripInfo.distance || 0,
          assigned_driver: result.tripInfo.assigned_driver || '',
        });
      }

      // Update legs from parsed result
      if (result.legs && result.legs.length > 0) {
        const parsedLegs: LegData[] = result.legs.map((leg, index) => ({
          leg_id: leg.leg_id || `LEG-${index + 1}`,
          pickup_facility_id: leg.pick_up_facility_id || leg.pickup_facility_id || '',
          dropoff_facility_id: leg.drop_off_facility_id || leg.dropoff_facility_id || '',
          pickup_address: leg.pick_up_address || leg.pickup_address || '',
          dropoff_address: leg.drop_off_address || leg.dropoff_address || '',
          pickup_time: leg.pick_up_time || leg.pickup_time || '',
          dropoff_time: leg.drop_off_time || leg.dropoff_time || '',
          fuel_sur_charge: leg.fuel_sur_charge || 0,
          distance: leg.distance || 0,
          assigned_driver: leg.assigned_driver || '',
        }));
        setLegs(parsedLegs);
      }

      toast.success("Load parsed successfully");
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to parse load";
      setParseError(errorMessage);
      toast.error("Failed to parse load");
      console.error(error);
    } finally {
      setIsParsing(false);
    }
  };

  // Update trip data
  const updateTripData = (field: string, value: any) => {
    setTripData(prev => ({ ...prev, [field]: value }));
  };

  // Update leg data
  const updateLeg = (legIndex: number, field: string, value: any) => {
    const updatedLegs = [...legs];
    updatedLegs[legIndex] = {
      ...updatedLegs[legIndex],
      [field]: value
    };
    setLegs(updatedLegs);
  };

  // Add new leg
  const addLeg = () => {
    const newLeg: LegData = {
      leg_id: `LEG-${Date.now()}`,
      pickup_facility_id: '',
      dropoff_facility_id: '',
      pickup_address: tripData.pickup_address,
      dropoff_address: tripData.dropoff_address,
      pickup_time: tripData.start_time,
      dropoff_time: tripData.end_time,
      fuel_sur_charge: 0,
      distance: 0,
      assigned_driver: tripData.assigned_driver,
    };
    setLegs([...legs, newLeg]);
  };

  // Remove leg
  const removeLeg = (legIndex: number) => {
    const updatedLegs = legs.filter((_, index) => index !== legIndex);
    setLegs(updatedLegs);
  };

  // Submit form
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (editMode === 'text') {
      // Submit with text parsing
      onSubmit({
        text: loadText,
        parsedData: parsedLoad
      });
    } else {
      // Submit with form data
      const updateData: Partial<Load> = {
        trip_id: tripData.trip_id,
        pickup_facility: tripData.pickup_facility,
        dropoff_facility: tripData.dropoff_facility,
        pickup_address: tripData.pickup_address,
        dropoff_address: tripData.dropoff_address,
        start_time: tripData.start_time,
        end_time: tripData.end_time,
        rate: tripData.rate,
        rate_per_mile: tripData.rate_per_mile,
        distance: tripData.distance,
        assigned_driver: tripData.assigned_driver,
        legs: legs.map(leg => ({
          ...leg,
          id: leg.id || undefined
        }))
      };
      
      onSubmit({ updateData });
    }
  };

  // Reset form
  const resetForm = () => {
    setTripData({
      trip_id: load.trip_id || '',
      pickup_facility: load.pickup_facility || '',
      dropoff_facility: load.dropoff_facility || '',
      pickup_address: load.pickup_address || '',
      dropoff_address: load.dropoff_address || '',
      start_time: load.start_time ? new Date(load.start_time).toISOString().slice(0, 16) : '',
      end_time: load.end_time ? new Date(load.end_time).toISOString().slice(0, 16) : '',
      rate: load.rate || 0,
      rate_per_mile: load.rate_per_mile || 0,
      distance: load.distance || 0,
      assigned_driver: load.assigned_driver || '',
    });
    
    if (load.legs && load.legs.length > 0) {
      const initialLegs: LegData[] = load.legs.map(leg => ({
        id: leg.id,
        leg_id: leg.leg_id || '',
        pickup_facility_id: leg.pickup_facility_id || '',
        dropoff_facility_id: leg.dropoff_facility_id || '',
        pickup_address: leg.pickup_address || '',
        dropoff_address: leg.dropoff_address || '',
        pickup_time: leg.pickup_time ? new Date(leg.pickup_time).toISOString().slice(0, 16) : '',
        dropoff_time: leg.dropoff_time ? new Date(leg.dropoff_time).toISOString().slice(0, 16) : '',
        fuel_sur_charge: leg.fuel_sur_charge || 0,
        distance: leg.distance || 0,
        assigned_driver: leg.assigned_driver || '',
      }));
      setLegs(initialLegs);
    } else {
      setLegs([]);
    }
    
    setLoadText(formatLoadForEditing(load));
    setParsedLoad(undefined);
    setParseError(null);
  };

  return (
    <div className="max-h-[80vh] overflow-y-auto pr-2">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Edit Mode Toggle */}
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-2">
            <Label htmlFor="edit-mode">Edit Mode:</Label>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <input
                  type="radio"
                  id="form-mode"
                  name="editMode"
                  checked={editMode === 'form'}
                  onChange={() => setEditMode('form')}
                />
                <Label htmlFor="form-mode">Form Editor</Label>
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="radio"
                  id="text-mode"
                  name="editMode"
                  checked={editMode === 'text'}
                  onChange={() => setEditMode('text')}
                />
                <Label htmlFor="text-mode">Text Parser</Label>
              </div>
            </div>
          </div>
          <Badge variant={editMode === 'form' ? 'default' : 'secondary'}>
            {editMode === 'form' ? 'Form Mode' : 'Text Mode'}
          </Badge>
        </div>

        {editMode === 'text' ? (
          // Text Parsing Mode
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="dispatcher">Dispatcher (Optional)</Label>
              <Select
                onValueChange={(value) => setDispatcherId(value ? parseInt(value) : undefined)}
                value={dispatcherId?.toString()}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a dispatcher" />
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
            </div>

            <div className="space-y-2">
              <Label htmlFor="loadText" className="flex items-center space-x-2">
                <FileText className="h-4 w-4" />
                <span>Load Text</span>
              </Label>
              <Textarea
                id="loadText"
                placeholder="Paste load information here..."
                value={loadText}
                onChange={(e) => setLoadText(e.target.value)}
                rows={12}
                className="font-mono text-sm resize-none"
              />
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span>{loadText.length} characters</span>
              </div>
            </div>

            <Button
              type="button"
              variant="outline"
              onClick={handleParseLoad}
              disabled={isParsing || !loadText.trim()}
              className="w-full"
            >
              {isParsing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Parsing...
                </>
              ) : (
                <>
                  <CheckCircle className="mr-2 h-4 w-4" />
                  Parse Load
                </>
              )}
            </Button>

            {parseError && (
              <Alert className="border-red-200 bg-red-50">
                <AlertDescription className="text-red-800">
                  <strong>Parse Error:</strong> {parseError}
                </AlertDescription>
              </Alert>
            )}
          </div>
        ) : (
          // Form Editing Mode
          <div className="space-y-6">
            {/* Trip Information */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Truck className="h-5 w-5" />
                  <span>Trip Information</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="trip_id">Trip ID</Label>
                    <Input
                      id="trip_id"
                      value={tripData.trip_id}
                      onChange={(e) => updateTripData('trip_id', e.target.value)}
                      placeholder="Enter trip ID"
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="assigned_driver">Assigned Driver</Label>
                    <Input
                      id="assigned_driver"
                      value={tripData.assigned_driver}
                      onChange={(e) => updateTripData('assigned_driver', e.target.value)}
                      placeholder="Enter driver name"
                    />
                  </div>

                  <div>
                    <Label htmlFor="pickup_facility">Pickup Facility</Label>
                    <Input
                      id="pickup_facility"
                      value={tripData.pickup_facility}
                      onChange={(e) => updateTripData('pickup_facility', e.target.value)}
                      placeholder="Enter pickup facility"
                    />
                  </div>

                  <div>
                    <Label htmlFor="dropoff_facility">Dropoff Facility</Label>
                    <Input
                      id="dropoff_facility"
                      value={tripData.dropoff_facility}
                      onChange={(e) => updateTripData('dropoff_facility', e.target.value)}
                      placeholder="Enter dropoff facility"
                    />
                  </div>

                  <div>
                    <Label htmlFor="pickup_address">Pickup Address</Label>
                    <Input
                      id="pickup_address"
                      value={tripData.pickup_address}
                      onChange={(e) => updateTripData('pickup_address', e.target.value)}
                      placeholder="Enter pickup address"
                    />
                  </div>

                  <div>
                    <Label htmlFor="dropoff_address">Dropoff Address</Label>
                    <Input
                      id="dropoff_address"
                      value={tripData.dropoff_address}
                      onChange={(e) => updateTripData('dropoff_address', e.target.value)}
                      placeholder="Enter dropoff address"
                    />
                  </div>

                  <div>
                    <Label htmlFor="start_time">Start Time</Label>
                    <Input
                      id="start_time"
                      type="datetime-local"
                      value={tripData.start_time}
                      onChange={(e) => updateTripData('start_time', e.target.value)}
                    />
                  </div>

                  <div>
                    <Label htmlFor="end_time">End Time</Label>
                    <Input
                      id="end_time"
                      type="datetime-local"
                      value={tripData.end_time}
                      onChange={(e) => updateTripData('end_time', e.target.value)}
                    />
                  </div>

                  <div>
                    <Label htmlFor="rate">Rate ($)</Label>
                    <Input
                      id="rate"
                      type="number"
                      step="0.01"
                      value={tripData.rate}
                      onChange={(e) => updateTripData('rate', parseFloat(e.target.value) || 0)}
                      placeholder="Enter rate"
                    />
                  </div>

                  <div>
                    <Label htmlFor="rate_per_mile">Rate per Mile ($)</Label>
                    <Input
                      id="rate_per_mile"
                      type="number"
                      step="0.01"
                      value={tripData.rate_per_mile}
                      onChange={(e) => updateTripData('rate_per_mile', parseFloat(e.target.value) || 0)}
                      placeholder="Enter rate per mile"
                    />
                  </div>

                  <div className="md:col-span-2">
                    <Label htmlFor="distance">Distance (miles)</Label>
                    <Input
                      id="distance"
                      type="number"
                      step="0.1"
                      value={tripData.distance}
                      onChange={(e) => updateTripData('distance', parseFloat(e.target.value) || 0)}
                      placeholder="Enter distance"
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
                {legs.length > 0 ? (
                  <div className="space-y-4 max-h-[40vh] overflow-y-auto pr-2">
                    {legs.map((leg, index) => (
                      <Card key={index} className="bg-gray-50">
                        <CardHeader className="pb-3">
                          <div className="flex items-center justify-between">
                            <h4 className="font-medium">Leg {index + 1}</h4>
                            <div className="flex items-center space-x-2">
                              <Badge variant="outline" className="text-xs">
                                {leg.leg_id}
                              </Badge>
                              <Button
                                type="button"
                                variant="ghost"
                                size="sm"
                                onClick={() => removeLeg(index)}
                                className="text-red-600 hover:text-red-700"
                              >
                                <X className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent className="space-y-4">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <Label>Leg ID</Label>
                              <Input
                                value={leg.leg_id}
                                onChange={(e) => updateLeg(index, 'leg_id', e.target.value)}
                                placeholder="Enter leg ID"
                              />
                            </div>

                            <div>
                              <Label>Assigned Driver</Label>
                              <Input
                                value={leg.assigned_driver}
                                onChange={(e) => updateLeg(index, 'assigned_driver', e.target.value)}
                                placeholder="Enter driver name"
                              />
                            </div>

                            <div>
                              <Label>Pickup Facility ID</Label>
                              <Input
                                value={leg.pickup_facility_id}
                                onChange={(e) => updateLeg(index, 'pickup_facility_id', e.target.value)}
                                placeholder="Enter pickup facility ID"
                              />
                            </div>

                            <div>
                              <Label>Dropoff Facility ID</Label>
                              <Input
                                value={leg.dropoff_facility_id}
                                onChange={(e) => updateLeg(index, 'dropoff_facility_id', e.target.value)}
                                placeholder="Enter dropoff facility ID"
                              />
                            </div>

                            <div>
                              <Label>Pickup Address</Label>
                              <Input
                                value={leg.pickup_address}
                                onChange={(e) => updateLeg(index, 'pickup_address', e.target.value)}
                                placeholder="Enter pickup address"
                              />
                            </div>

                            <div>
                              <Label>Dropoff Address</Label>
                              <Input
                                value={leg.dropoff_address}
                                onChange={(e) => updateLeg(index, 'dropoff_address', e.target.value)}
                                placeholder="Enter dropoff address"
                              />
                            </div>

                            <div>
                              <Label>Pickup Time</Label>
                              <Input
                                type="datetime-local"
                                value={leg.pickup_time}
                                onChange={(e) => updateLeg(index, 'pickup_time', e.target.value)}
                              />
                            </div>

                            <div>
                              <Label>Dropoff Time</Label>
                              <Input
                                type="datetime-local"
                                value={leg.dropoff_time}
                                onChange={(e) => updateLeg(index, 'dropoff_time', e.target.value)}
                              />
                            </div>

                            <div>
                              <Label>Distance (miles)</Label>
                              <Input
                                type="number"
                                step="0.1"
                                value={leg.distance}
                                onChange={(e) => updateLeg(index, 'distance', parseFloat(e.target.value) || 0)}
                                placeholder="Enter distance"
                              />
                            </div>

                            <div>
                              <Label>Fuel Surcharge ($)</Label>
                              <Input
                                type="number"
                                step="0.01"
                                value={leg.fuel_sur_charge}
                                onChange={(e) => updateLeg(index, 'fuel_sur_charge', parseFloat(e.target.value) || 0)}
                                placeholder="Enter fuel surcharge"
                              />
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <RouteIcon className="h-12 w-12 mx-auto mb-4" />
                    <p>No legs added yet</p>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={addLeg}
                      className="mt-4"
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      Add First Leg
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Form Actions */}
        <DialogFooter className="sticky bottom-0 bg-white border-t pt-4">
          <Button
            type="button"
            variant="outline"
            onClick={resetForm}
            disabled={isSubmitting}
          >
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