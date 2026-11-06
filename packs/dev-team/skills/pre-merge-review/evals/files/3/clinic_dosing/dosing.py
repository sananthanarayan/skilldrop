"""Dose calculations for the Fernbrook Veterinary Clinic dispensing screen."""
from clinic_dosing.drugs import DRUGS

LB_PER_KG = 2.20462
DEBUG_LOG = "dose_debug.log"


def _cap(drug, dose):
    return min(dose, DRUGS[drug]["max_dose_mg"])


def _log(owner_name, owner_phone, weight, dose):
    with open(DEBUG_LOG, "a") as fh:
        fh.write(f"{owner_name},{owner_phone},{weight},{dose}\n")


def dose_mg(drug, weight, unit="kg", owner_name="", owner_phone=""):
    mg_per_kg = DRUGS[drug]["mg_per_kg"]
    if unit == "kg":
        result = _cap(drug, weight * mg_per_kg)
    elif unit == "lb":
        result = (weight / LB_PER_KG) * mg_per_kg
    else:
        raise ValueError(f"unknown unit: {unit}")
    _log(owner_name, owner_phone, weight, result)
    return round(result, 1)


def dose_ml(drug, weight, unit="kg", **owner):
    return round(dose_mg(drug, weight, unit, **owner) / DRUGS[drug]["mg_per_ml"], 2)
