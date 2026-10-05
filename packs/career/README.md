# Job applications

One job application, for any occupation: an honest check of your resume against the posting, a tailored resume and a cover letter that say nothing you didn't, the application form's answers drafted from your resume, and a script that lists every figure and name in a draft that your own resume doesn't contain.

`/plugin install career@skilldrop` · generated from [`main`](https://github.com/sananthanarayan/skilldrop) — do not edit.

## Start here: Find out where you stand against a posting before you write the application

Paste this into Claude Code:

```text
My resume is in resume.md and the job I'm looking at is in posting.md. Am I a good fit? Be honest about what's missing.
```

- **Before you start:** Your resume or CV as text, Markdown or a file your agent can read
- **Before you start:** The job posting, pasted or saved as a file
- **How to tell it worked:** job-fit-analysis opens with a verdict (strong match, worth applying, long shot or not a match), lists the requirements an employer screens on first, marks every requirement met, partly, not shown or not met with the resume line behind it, and ends with questions about what your resume doesn't show.
- **If nothing happens:** If it credits you with something that isn't in your resume, say so and run it again. If job-fit-analysis does not activate, ask for it by name ("use job-fit-analysis").

## Loops

- `ship-a-draft`
- `apply`

## Skills

- `application-form-answers`
- `brief-intake`
- `council-review`
- `cover-letter`
- `doc-critique`
- `job-fit-analysis`
- `output-hygiene`
- `resume-tailor`

More: https://sananthanarayan.github.io/skilldrop/packs/career/
