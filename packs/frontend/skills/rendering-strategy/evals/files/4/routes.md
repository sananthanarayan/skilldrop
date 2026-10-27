# Crumbly Kitchen routes

| Route | What's on it | Notes |
|---|---|---|
| `/` | featured recipes, seasonal picks | editors swap the featured set every day at 06:00 |
| `/recipes/[slug]` | the recipe: title, hero image, ingredients, steps, avg rating + review count, "Save" heart | ~42,000 recipes. Recipe text rarely changes after publish. ~3,000 reviews posted per day across the site. Heart is filled if the logged-in user saved it |
| `/category/[name]` | paginated list of recipes in a category, 24 per page | 180 categories |
| `/search?q=` | search results from FindIt | |
| `/account/saved` | the logged-in user's saved recipes | login required |
| `/account/settings` | email, password, newsletter prefs | login required |
| `/print/[slug]` | printer-friendly version of a recipe | same content as /recipes/[slug] |

Content comes from Larder CMS. Larder can send a webhook on publish, edit and unpublish.

Hosting: static files in a storage bucket behind a CDN. No servers.
