# Northwind Health information security policy

Version 4.2, approved by the CTO on 2026-03-14. Reviewed annually.

## 1. Scope
Applies to all staff, contractors and systems that store or process customer data.

## 2. Encryption
2.1 All customer data in transit is encrypted with TLS 1.2 or higher.
2.2 Customer data at rest in the production database and object storage is encrypted with AES-256.

## 3. Access control
3.1 Multi-factor authentication is enforced for engineering staff and for all administrative access to production.
3.2 Roll-out of multi-factor authentication to all remaining staff is in progress.
3.3 Access is reviewed quarterly by system owners.

## 4. Training
4.1 All staff complete security awareness training on joining and annually after that.

## 5. Incident response
5.1 The incident response plan (IR-001) is maintained by the security lead and tested annually.
5.2 Security on-call covers business hours, 08:00 to 18:00 UK time, Monday to Friday.

## 6. Backups
6.1 Production databases are backed up daily. Restores are tested quarterly.

## 7. Retention
7.1 Customer data is deleted 90 days after contract termination.

## 8. Customer portal
8.1 Single sign-on for the customer portal is planned for Q1 2027.
