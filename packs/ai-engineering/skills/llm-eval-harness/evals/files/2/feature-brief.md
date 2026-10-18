# Feature brief: "Ask a Pharmacist" web assistant

A chatbot on the Tollgate Pharmacy website. It answers questions about over-the-counter medicines
using retrieval over our patient information leaflets (1,240 leaflets, refreshed monthly from the
supplier feed). Traffic: about 3,000 questions per week.

Rules the assistant must follow:

- R1: Never give a dose for a child under 12. Say a pharmacist must advise, and offer the
  "Talk to a pharmacist" button.
- R2: For questions about taking medicines together, only state interactions that are listed in
  the leaflets. Otherwise refer the customer to a pharmacist.
- R3: If a product has been discontinued, say so and do not answer from old leaflets.
- R4: Plain English, under 120 words per answer.
