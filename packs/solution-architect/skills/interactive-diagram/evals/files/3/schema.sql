-- Clinic bookings
create table clinics (
  id          serial primary key,
  name        text not null,
  timezone    text not null default 'Europe/London'
);

create table practitioners (
  id          serial primary key,
  clinic_id   integer not null references clinics(id),
  full_name   text not null,
  role        text not null check (role in ('physio', 'osteo', 'massage'))
);

create table patients (
  id          serial primary key,
  email       text unique not null,
  phone       text
);

create table appointments (
  id               serial primary key,
  practitioner_id  integer not null references practitioners(id),
  patient_id       integer not null references patients(id),
  starts_at        timestamptz not null,
  minutes          integer not null default 45,
  status           text not null default 'booked',
  booked_by_user_id integer  -- staff login id from the old system; no table here
);

create table appointment_notes (
  appointment_id   integer primary key references appointments(id),
  body             text not null,
  written_at       timestamptz not null default now()
);
