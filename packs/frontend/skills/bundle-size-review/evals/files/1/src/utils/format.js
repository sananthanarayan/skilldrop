import _ from "lodash";
import { format, parseISO, isValid } from "date-fns";

// Shared formatting helpers for the dispatch board, the header and the report pages.

export function formatDay(iso) {
  const d = parseISO(iso);
  return isValid(d) ? format(d, "EEE d MMM") : "—";
}

export function formatTime(iso) {
  const d = parseISO(iso);
  return isValid(d) ? format(d, "HH:mm") : "";
}

export function byTechnician(jobs) {
  return _.groupBy(jobs, "technicianId");
}

export function sortJobs(jobs) {
  return _.sortBy(jobs, ["priority", "dueAt"]);
}

export function money(amount) {
  return _.round(amount, 2).toFixed(2);
}
