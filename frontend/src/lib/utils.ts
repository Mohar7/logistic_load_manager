import {type ClassValue, clsx} from "clsx";
import {twMerge} from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date, includeTime = false): string {
  if (!date) return "";
  const dateObj = date instanceof Date ? date : new Date(date);
  
  // Check if date is valid
  if (isNaN(dateObj.getTime())) return "Invalid date";
  
  // Format options
  const options: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "short",
    day: "numeric",
  };

  if (includeTime) {
    Object.assign(options, {
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  return new Intl.DateTimeFormat("en-US", options).format(dateObj);
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  }).format(amount);
}

export function formatNumber(
  number: number,
  decimalPlaces = 2,
  addCommas = true
): string {
  if (number === undefined || number === null) return "";
  
  const fixed = Number(number).toFixed(decimalPlaces);
  
  if (addCommas) {
    const parts = fixed.split(".");
    if (parts[0]) {
      parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
      return parts.join(".");
    }
  }
  
  return fixed;
}