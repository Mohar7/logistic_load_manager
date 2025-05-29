import {useState} from "react";
import {Button} from "@/components/ui/button";
import {Textarea} from "@/components/ui/textarea";
import {Input} from "@/components/ui/input";
import type {Dispatcher, ParsedLoad} from "@/types/models";
import {Select, SelectContent, SelectItem, SelectTrigger, SelectValue,} from "@/components/ui/select";
import {Label} from "@/components/ui/label";
import {Card, CardContent, CardDescription, CardHeader, CardTitle} from "@/components/ui/card";
import {Badge} from "@/components/ui/badge";
import {Separator} from "@/components/ui/separator";
import {toast} from "sonner";
import {CheckCircle, FileText, Loader2, MapPin, Plus, RouteIcon, Truck, User, Edit, Save, X} from "lucide-react";
import {Alert, AlertDescription} from "@/components/ui/alert";
import {Switch} from "@/components/ui/switch";

interface LoadFormProps {
  onSubmit: (data: { text: string; dispatcherId?: number; parsedData?: ParsedLoad }) => void;
  isSubmitting?: boolean;
  parseLoad: (text: string) => Promise<ParsedLoad>;
  dispatchers: Dispatcher[];
  initialData?: {
    text?: string;
    dispatcherId?: number;
  };
}

export function LoadForm({
  onSubmit,
  isSubmitting = false,
  parseLoad,
  dispatchers = [],
  initialData,
}: LoadFormProps) {
  const [loadText, setLoadText] = useState(initialData?.text || "");
  const [dispatcherId, setDispatcherId] = useState<number | undefined>(initialData?.dispatcherId);
  const [parsedLoad, setParsedLoad] = useState<ParsedLoad | undefined>(undefined);
  const [editedLoad, setEditedLoad] = useState<ParsedLoad | undefined>(undefined);
  const [isParsing, setIsParsing] = useState(false);
  const [parseError, setParseError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  // Helper functions
  const formatValue = (value: any, fallback: string = "Not specified") => {
    if (value === null || value === undefined || value === "" || value === "N/A") {
      return fallback;
    }
    return value;
  };

  const formatCurrency = (value: any) => {
    const num = parseFloat(value);
    return isNaN(num) ? "$0.00" : `${num.toFixed(2)}`;
  };

  const formatDistance = (value: any) => {
    const num = parseFloat(value);
    return isNaN(num) ? "0 miles" : `${num} miles`;
  };

  const formatTripInfo = (tripInfo: any) => {
    return Object.entries(tripInfo)
      .filter(([_, value]) => value !== null && value !== undefined && value !== "" && value !== "N/A")
      .map(([key, value]) => ({ key, value }));
  };

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
      setEditedLoad(JSON.parse(JSON.stringify(result))); // Deep copy
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

  const handleSubmit = () => {
    if (!loadText.trim()) {
      toast.error("Please enter load text");
      return;
    }

    onSubmit({
      text: loadText,
      dispatcherId,
      parsedData: isEditing ? editedLoad : parsedLoad,
    });
  };

  const handleClearForm = () => {
    setLoadText("");
    setDispatcherId(undefined);
    setParsedLoad(undefined);
    setEditedLoad(undefined);
    setParseError(null);
    setIsEditing(false);
  };

  const updateTripInfo = (field: string, value: any) => {
    if (!editedLoad) return;
    setEditedLoad({
      ...editedLoad,
      tripInfo: {
        ...editedLoad.tripInfo,
        [field]: value
      }
    });
  };

  const updateLeg = (legIndex: number, field: string, value: any) => {
    if (!editedLoad) return;
    const updatedLegs = [...editedLoad.legs];
    updatedLegs[legIndex] = {
      ...updatedLegs[legIndex],
      [field]: value
    };
    setEditedLoad({
      ...editedLoad,
      legs: updatedLegs
    });
  };

  const addLeg = () => {
    if (!editedLoad) return;
    const newLeg = {
      id: editedLoad.legs.length + 1,
      leg_id: `LEG-${Date.now()}`,
      pickup_facility_id: editedLoad.tripInfo.pick_up_facility_id || editedLoad.tripInfo.pickup_facility_id || "",
      dropoff_facility_id: editedLoad.tripInfo.drop_off_facility_id || editedLoad.tripInfo.dropoff_facility_id || "",
      pickup_address: editedLoad.tripInfo.pick_up_address || editedLoad.tripInfo.pickup_address || "",
      dropoff_address: editedLoad.tripInfo.drop_off_address || editedLoad.tripInfo.dropoff_address || "",
      pickup_time: editedLoad.tripInfo.pick_up_time || editedLoad.tripInfo.pickup_time || "",
      dropoff_time: editedLoad.tripInfo.drop_off_time || editedLoad.tripInfo.dropoff_time || "",
      fuel_sur_charge: 0,
      distance: editedLoad.tripInfo.distance || 0,
      assigned_driver: editedLoad.tripInfo.assigned_driver || ""
    };
    setEditedLoad({
      ...editedLoad,
      legs: [...editedLoad.legs, newLeg]
    });
  };

  const removeLeg = (legIndex: number) => {
    if (!editedLoad) return;
    const updatedLegs = editedLoad.legs.filter((_, index) => index !== legIndex);
    setEditedLoad({
      ...editedLoad,
      legs: updatedLegs
    });
  };

  const autoFillLegData = () => {
    if (!editedLoad) return;
    
    const updatedLegs = editedLoad.legs.map(leg => ({
      ...leg,
      pickup_address: leg.pickup_address ||
                     editedLoad.tripInfo.pick_up_address ||
                     editedLoad.tripInfo.pickup_address ||
                     leg.pickup_address,
      dropoff_address: leg.dropoff_address ||
                      editedLoad.tripInfo.drop_off_address ||
                      editedLoad.tripInfo.dropoff_address ||
                      leg.dropoff_address,
      pickup_time: leg.pickup_time ||
                  editedLoad.tripInfo.pick_up_time ||
                  editedLoad.tripInfo.pickup_time ||
                  leg.pickup_time,
      dropoff_time: leg.dropoff_time ||
                   editedLoad.tripInfo.drop_off_time ||
                   editedLoad.tripInfo.dropoff_time ||
                   leg.dropoff_time,
      pickup_facility_id: leg.pickup_facility_id ||
                         editedLoad.tripInfo.pick_up_facility_id ||
                         editedLoad.tripInfo.pickup_facility_id ||
                         leg.pickup_facility_id,
      dropoff_facility_id: leg.dropoff_facility_id ||
                          editedLoad.tripInfo.drop_off_facility_id ||
                          editedLoad.tripInfo.dropoff_facility_id ||
                          leg.dropoff_facility_id,
      distance: leg.distance || editedLoad.tripInfo.distance || leg.distance,
      assigned_driver: leg.assigned_driver || editedLoad.tripInfo.assigned_driver || leg.assigned_driver
    }));

    setEditedLoad({
      ...editedLoad,
      legs: updatedLegs
    });
    
    toast.success("Auto-filled missing leg data from trip information");
  };

  const displayLoad = isEditing ? editedLoad : parsedLoad;

  return (
    <div className="max-h-[80vh] overflow-y-auto pr-2 space-y-6">
      {/* Dispatcher Selection */}
      <div className="space-y-2">
        <Label htmlFor="dispatcher" className="flex items-center space-x-2">
          <User className="h-4 w-4" />
          <span>Dispatcher (Optional)</span>
        </Label>
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

      {/* Load Text Input */}
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
          rows={8}
          className="font-mono text-sm resize-none"
        />
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>{loadText.length} characters</span>
          {loadText && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={handleClearForm}
            >
              Clear
            </Button>
          )}
        </div>
      </div>

      {/* Parse Button */}
      <div className="flex items-center space-x-2">
        <Button
          type="button"
          variant="outline"
          onClick={handleParseLoad}
          disabled={isParsing || !loadText.trim()}
          className="flex-1"
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
        {parsedLoad && (
          <Badge variant="default" className="bg-green-100 text-green-800">
            Parsed Successfully
          </Badge>
        )}
      </div>

      {/* Parse Error */}
      {parseError && (
        <Alert className="border-red-200 bg-red-50">
          <AlertDescription className="text-red-800">
            <strong>Parse Error:</strong> {parseError}
          </AlertDescription>
        </Alert>
      )}

      {/* Parsed Load Preview/Edit */}
      {displayLoad && (
        <Card className="border-green-200 bg-green-50">
          <CardHeader className="sticky top-0 bg-green-50 z-10 border-b border-green-200">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center space-x-2 text-green-800">
                <CheckCircle className="h-5 w-5" />
                <span>{isEditing ? "Edit Load Details" : "Parsed Load Details"}</span>
              </CardTitle>
              <div className="flex items-center space-x-2">
                <div className="flex items-center space-x-2">
                  <Label htmlFor="edit-mode" className="text-sm">Edit Mode</Label>
                  <Switch
                    id="edit-mode"
                    checked={isEditing}
                    onCheckedChange={setIsEditing}
                  />
                </div>
              </div>
            </div>
            <CardDescription>
              {isEditing ? "Modify the parsed information as needed" : "Preview of the extracted load information"}
            </CardDescription>
          </CardHeader>
          <CardContent className="max-h-[50vh] overflow-y-auto space-y-6">
            {/* Trip Information */}
            <div>
              <h3 className="font-semibold flex items-center space-x-2 mb-3">
                <Truck className="h-4 w-4" />
                <span>Trip Information</span>
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {Object.entries(displayLoad.tripInfo).map(([key, value]) => (
                  <div key={key} className="space-y-1">
                    <Label className="text-xs text-muted-foreground capitalize">
                      {key.replace(/_/g, ' ')}
                    </Label>
                    {isEditing ? (
                      <Input
                        value={value?.toString() || ""}
                        onChange={(e) => updateTripInfo(key, e.target.value)}
                        className="h-8"
                      />
                    ) : (
                      <div className="p-2 bg-white rounded border text-sm font-mono">
                        {value?.toString() || "N/A"}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <Separator />

            {/* Legs Information */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold flex items-center space-x-2">
                  <RouteIcon className="h-4 w-4" />
                  <span>Load Legs</span>
                  <Badge variant="outline">{displayLoad.legs.length} legs</Badge>
                </h3>
                {isEditing && (
                  <div className="flex space-x-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={autoFillLegData}
                      title="Auto-fill missing leg data from trip information"
                    >
                      <CheckCircle className="h-4 w-4 mr-1" />
                      Auto-Fill
                    </Button>
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
                )}
              </div>
              
              {displayLoad.legs.length > 0 ? (
                <div className="space-y-3 max-h-[40vh] overflow-y-auto pr-2">
                  {displayLoad.legs.map((leg, index) => (
                    <Card key={index} className="bg-white border">
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="font-medium">Leg {index + 1}</h4>
                          <div className="flex items-center space-x-2">
                            {leg.leg_id && leg.leg_id !== "N/A" && (
                              <Badge variant="outline" className="font-mono text-xs">
                                {leg.leg_id}
                              </Badge>
                            )}
                            {isEditing && (
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
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="space-y-3">
                            <div>
                              <Label className="text-xs text-muted-foreground">Leg ID</Label>
                              {isEditing ? (
                                <Input
                                  value={leg.leg_id || ""}
                                  onChange={(e) => updateLeg(index, "leg_id", e.target.value)}
                                  className="h-8 font-mono"
                                  placeholder="Enter leg ID"
                                />
                              ) : (
                                <div className="text-sm font-mono font-medium">
                                  {formatValue(leg.leg_id)}
                                </div>
                              )}
                            </div>
                            <div>
                              <Label className="text-xs text-muted-foreground">Pickup Address</Label>
                              {isEditing ? (
                                <Input
                                  value={leg.pickup_address || ""}
                                  onChange={(e) => updateLeg(index, "pickup_address", e.target.value)}
                                  className="h-8"
                                  placeholder="Enter pickup address"
                                />
                              ) : (
                                <div className="text-sm font-medium">
                                  {formatValue(
                                    leg.pickup_address ||
                                    leg.pickup_facility_id ||
                                    displayLoad.tripInfo.pickup_address ||
                                    displayLoad.tripInfo.pick_up_address
                                  )}
                                </div>
                              )}
                            </div>
                            <div>
                              <Label className="text-xs text-muted-foreground">Dropoff Address</Label>
                              {isEditing ? (
                                <Input
                                  value={leg.dropoff_address || ""}
                                  onChange={(e) => updateLeg(index, "dropoff_address", e.target.value)}
                                  className="h-8"
                                  placeholder="Enter dropoff address"
                                />
                              ) : (
                                <div className="text-sm font-medium">
                                  {formatValue(
                                    leg.dropoff_address ||
                                    leg.dropoff_facility_id ||
                                    displayLoad.tripInfo.dropoff_address ||
                                    displayLoad.tripInfo.drop_off_address
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                          
                          <div className="space-y-3">
                            <div>
                              <Label className="text-xs text-muted-foreground">Distance (miles)</Label>
                              {isEditing ? (
                                <Input
                                  type="number"
                                  value={leg.distance || ""}
                                  onChange={(e) => updateLeg(index, "distance", parseFloat(e.target.value) || 0)}
                                  className="h-8"
                                />
                              ) : (
                                <div className="text-sm font-medium">
                                  {formatDistance(leg.distance || displayLoad.tripInfo.distance)}
                                </div>
                              )}
                            </div>
                            <div>
                              <Label className="text-xs text-muted-foreground">Fuel Surcharge</Label>
                              {isEditing ? (
                                <Input
                                  type="number"
                                  step="0.01"
                                  value={leg.fuel_sur_charge || ""}
                                  onChange={(e) => updateLeg(index, "fuel_sur_charge", parseFloat(e.target.value) || 0)}
                                  className="h-8"
                                />
                              ) : (
                                <div className="text-sm font-medium text-green-600">
                                  {formatCurrency(leg.fuel_sur_charge)}
                                </div>
                              )}
                            </div>
                            <div>
                              <Label className="text-xs text-muted-foreground">Pickup Time</Label>
                              {isEditing ? (
                                <Input
                                  type="datetime-local"
                                  value={leg.pickup_time || ""}
                                  onChange={(e) => updateLeg(index, "pickup_time", e.target.value)}
                                  className="h-8"
                                />
                              ) : (
                                <div className="text-sm">
                                  {leg.pickup_time ||
                                   displayLoad.tripInfo.pickup_time ||
                                   displayLoad.tripInfo.pick_up_time ||
                                   displayLoad.tripInfo.pickup_time_str ||
                                   displayLoad.tripInfo.pick_up_time_str ||
                                   "Not specified"}
                                </div>
                              )}
                            </div>
                            <div>
                              <Label className="text-xs text-muted-foreground">Dropoff Time</Label>
                              {isEditing ? (
                                <Input
                                  type="datetime-local"
                                  value={leg.dropoff_time || ""}
                                  onChange={(e) => updateLeg(index, "dropoff_time", e.target.value)}
                                  className="h-8"
                                />
                              ) : (
                                <div className="text-sm">
                                  {leg.dropoff_time ||
                                   displayLoad.tripInfo.dropoff_time ||
                                   displayLoad.tripInfo.drop_off_time ||
                                   displayLoad.tripInfo.dropoff_time_str ||
                                   displayLoad.tripInfo.drop_off_time_str ||
                                   "Not specified"}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="text-center py-4 text-muted-foreground">
                  No legs found in the parsed data
                  {isEditing && (
                    <div className="mt-2">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={addLeg}
                      >
                        <Plus className="h-4 w-4 mr-2" />
                        Add First Leg
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Submit Button */}
      <div className="sticky bottom-0 bg-white border-t pt-4 flex justify-end space-x-3">
        <Button
          type="button"
          variant="outline"
          onClick={handleClearForm}
          disabled={isSubmitting}
        >
          Clear Form
        </Button>
        {isEditing && editedLoad && (
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              setParsedLoad(editedLoad);
              setIsEditing(false);
              toast.success("Changes saved");
            }}
          >
            <Save className="mr-2 h-4 w-4" />
            Save Changes
          </Button>
        )}
        <Button
          type="button"
          onClick={handleSubmit}
          disabled={isSubmitting || !loadText.trim()}
          size="lg"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Creating Load...
            </>
          ) : (
            <>
              <Plus className="mr-2 h-4 w-4" />
              Create Load
            </>
          )}
        </Button>
      </div>
    </div>
  );
}