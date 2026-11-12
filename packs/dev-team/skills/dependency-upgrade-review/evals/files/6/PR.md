# Bump github.com/fernwire/httpkit from 1.8.1 to 1.8.4 #412

**dependabot** wants to merge 1 commit into `main` from `dependabot/go_modules/github.com/fernwire/httpkit-1.8.4`

Bumps [github.com/fernwire/httpkit](https://github.com/fernwire/httpkit) from 1.8.1 to 1.8.4.

<details>
<summary>Release notes</summary>
<p><em>Sourced from <a href="https://github.com/fernwire/httpkit/releases">github.com/fernwire/httpkit's releases</a>.</em></p>
<blockquote>
<h2>v1.8.4</h2>
<ul>
<li>Add optional OpenTelemetry hooks via <code>WithTracer</code> (backed by the new <code>fernwire/otelshim</code> module). No behaviour change unless the option is passed.</li>
<li>Fix a data race in connection-pool metrics (#240).</li>
</ul>
</blockquote>
</details>
<details>
<summary>Commits</summary>
<ul>
<li><code>9c1e4b7</code> release v1.8.4</li>
<li><code>3fa02d1</code> pool: fix metrics race (#240)</li>
<li><code>b81d6e0</code> add WithTracer option (#238)</li>
<li>Additional commits viewable in <a href="https://github.com/fernwire/httpkit/compare/v1.8.1...v1.8.4">compare view</a></li>
</ul>
</details>
<br />

Dependabot will resolve any conflicts with this PR as long as you don't alter it yourself.

---

### Checks

- ci / lint — passed (41s)
- ci / test — passed (1m 52s)
- ci / build — passed (38s)

All checks have passed.
