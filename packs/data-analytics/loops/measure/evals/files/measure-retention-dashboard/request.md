From: Anouk Verhoeven (Head of Retention, Larkspur Kitchens)
To: Analytics
Subject: Retention dashboard for the Monday win-back meeting

Hi all,

Every Monday the retention team meets to decide which plan cohorts get a win-back offer
that week (we have budget for about two offers a week, so we have to choose). Right now we
do it off three spreadsheets that never agree. We want one dashboard instead.

What we need to answer in that meeting, most important first:

1. Which plans are losing subscribers fastest right now? (churn rate by plan, weekly)
2. Is the active subscriber base growing or shrinking, by plan?
3. How much net revenue is each plan bringing in per week, so we know what a lost
   subscriber is worth?
4. Did last week's win-back offer bring people back? (we log offers in `winback_offers`)

Plans: Classic, Veggie, Family, Lean. Our week runs Monday to Sunday, UK time.

Metric owners:
- Churn rate and active subscribers: me (Anouk)
- Net revenue: Callum Reyes in Finance. He's particular that refunds come off and test
  accounts are excluded.

The BI team (Sana's team) will build it in our usual tool once the spec is agreed. I've put
the queries we use today in the sql/ folder. They're from three different people, so please
check them before anything gets built on them. Schema notes are in schema.md.

The marketing team also asked for page views and app downloads on it. I don't think we use
those in the meeting.

Thanks,
Anouk
