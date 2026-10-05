-- Dump of the tables the current booking app uses. Schema only.
-- NOTE (Devraj): all times are stored as Sydney local time, for every clinic.

CREATE TABLE clinics (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  name          VARCHAR(80) NOT NULL,
  city          VARCHAR(40) NOT NULL
);

CREATE TABLE vets (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  full_name     VARCHAR(120) NOT NULL,
  clinic_id     INT NOT NULL            -- home clinic only
);

CREATE TABLE appointments (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  clinic_id     INT NOT NULL,
  vet_id        INT NOT NULL,
  appt_time     DATETIME NOT NULL,      -- start time, Sydney local
  appt_type     VARCHAR(40) NOT NULL,   -- free text: 'consult', 'Consult', 'vacc', ...
  price         FLOAT,
  owner_name    VARCHAR(120),
  owner_phone   VARCHAR(40),
  pet_name      VARCHAR(80),
  status        VARCHAR(20) NOT NULL    -- 'booked', 'cancelled', 'completed'
);

-- no indexes other than the primary keys
