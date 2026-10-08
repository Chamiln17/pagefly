# Security policy

## Reporting a vulnerability

Report vulnerabilities privately through GitHub: open the repository's **Security** tab and choose **Report a vulnerability**. Please do not open a public issue for a security problem.

Include what you found, how to reproduce it, and the impact you expect. You will get an answer as soon as a maintainer can look at it; this is a volunteer-maintained prototype with no response-time guarantee.

## Supported versions

Only the latest commit on `main` receives fixes.

## Deployment notes

PageFly is a hackathon prototype. Before running it anywhere reachable from the internet, know that:

- **The API has no authentication or rate limiting.** `/generate` and `/scrape-shopify` call paid LLM and search APIs on every request, so an exposed server spends your API credit for anyone who can reach it.
- **Previews serve model-generated HTML.** `/preview/{key}` returns HTML written by an LLM, including any scripts it contains. Serve previews from a separate origin from anything that holds user sessions.
- **The scraper fetches caller-supplied URLs.** It refuses URLs that are not http(s) or that resolve to a loopback, private, link-local or otherwise non-public address, including on redirects. A DNS answer that changes between the check and the connection is not covered.
- **Secrets come from the environment.** Keep `.env` out of version control (it is git-ignored); `.env.example` holds placeholders only.

CI scans the full git history for secrets (gitleaks) and the locked dependencies for known vulnerabilities (pip-audit) on every push and pull request.
