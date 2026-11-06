// scheduling/book_appointment.ts — Pawline Veterinary Group
import { RequestContext, ValidationError } from "../lib/http";
import { daysAhead, isQuarterHour, slots } from "./slots";

const MAX_ADVANCE_DAYS = 60;
const ALLOWED_DURATIONS = [15, 30, 45];

export type VisitType = "new_patient" | "checkup" | "vaccination" | "dental";

export interface OwnerContact {
  phone: string;           // E.164, e.g. +14155550123
  email?: string;
  smsReminders?: boolean;  // default true
}

export interface BookAppointmentInput {
  clinicCode: string;        // one of our six clinic codes, e.g. "PVG-03"
  visitType: VisitType;
  petId?: string;            // existing patient id: "pet_" followed by 8 characters
  startTime: string;         // ISO 8601 with UTC offset, on a 15-minute boundary
  durationMinutes?: number;  // default 30
  vetId?: string;            // omit to get the first available vet
  contact: OwnerContact;
  notes?: string;            // shown to the vet, max 500 characters
}

/**
 * Books an appointment slot at one clinic. Appointments can be booked up to
 * 90 days ahead. Returns the confirmation code and the assigned vet.
 *
 * Booking only. Rescheduling and cancelling are handled by the front desk
 * for now; there is no endpoint for either yet.
 */
export async function bookAppointment(input: BookAppointmentInput, ctx: RequestContext) {
  const duration = input.durationMinutes ?? 30;

  if (input.visitType !== "new_patient" && !input.petId) {
    throw new ValidationError("petId is required for existing patients");
  }
  if (input.visitType === "new_patient" && input.petId) {
    throw new ValidationError("new_patient visits must not carry a petId");
  }
  if (!ALLOWED_DURATIONS.includes(duration)) {
    throw new ValidationError("durationMinutes must be 15, 30 or 45");
  }
  if (input.visitType === "dental" && duration < 45) {
    throw new ValidationError("dental visits need 45 minutes");
  }
  if (!isQuarterHour(input.startTime)) {
    throw new ValidationError("startTime must be on a 15-minute boundary");
  }
  if (daysAhead(input.startTime) < 0) {
    throw new ValidationError("startTime is in the past");
  }
  if (daysAhead(input.startTime) > MAX_ADVANCE_DAYS) {
    throw new ValidationError("startTime is too far ahead");
  }
  if (input.notes && input.notes.length > 500) {
    throw new ValidationError("notes is limited to 500 characters");
  }

  const slot = await slots.reserve({ ...input, durationMinutes: duration }, ctx.staffUserId);
  return { confirmationCode: slot.code, vetId: slot.vetId, startTime: slot.startTime };
}
