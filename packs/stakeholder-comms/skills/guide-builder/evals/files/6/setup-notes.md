# larkspur local setup - rough notes (Tobin, not tidied)

- `lark seed --sample` loads the sample dataset so you have tables to query. do this first thing so there's something to look at
- install the CLI from the intranet: Fenmoor Hub > Tools > Larkspur CLI, run the installer. check with `lark --version`, should be 2.4 or later
- seed writes into your local db, so you need one: `lark db init` (creates it on port 5433)
- db init only works if the local runtime is up: `lark runtime start`
- config lives at ~/.lark/config.toml. clone the larkspur-starter repo, copy config.example.toml to ~/.lark/config.toml, fill in `workspace` and `region`
- `lark login` opens the browser for SSO. it reads workspace from the config file so the config has to exist first or it errors
- you must be in the lark-analysts group or login fails with "not authorised". Ines on the platform team adds people. can take up to a working day so ideally request before day one
- after login, `lark sync` pulls the shared dimension tables. first sync takes about 10 min, later ones are quick
- `lark status` shows runtime, db and login state if something looks off
