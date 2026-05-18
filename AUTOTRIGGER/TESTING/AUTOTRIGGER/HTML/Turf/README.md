# Turf Cricket Pulse

This repo holds a single responsive web page that turns your phone into a cricket scorecard, planner, and toss tracker. It is optimized for quick inputs, elegant visuals, and easy deployment via GitHub Pages.

## Features
- Live score dashboard with quick buttons for runs, extras, wickets, and a manual ball form that keeps the overs/balls tally accurate.
- Team and player manager with cleaner add forms plus inline rename/remove actions so squads stay tidy and you can update players quickly on the phone.
- Match planner to jot down upcoming formats and opponents so the team knows what is next.
- Live lineup block where you pick striker/non-striker, current bowler, and incoming players/bowlers; the UI prompts for the next player and bowler when a wicket falls and you can undo the last score change.
- Match scoreboard overview mirrors a live feed with the running score, ball count, next players, toss status, and a running candidate for man of the match.
- Control row now includes undo/redo, a complete-first-innings trigger, and an image download export beside the text scoreboard export.
- LocalStorage persistence keeps the score, log, lineup, and match info alive even after a reload.
- Add players by typing a comma-separated list so you can seed squads quickly on the phone.
- Head or tail toss widget that logs the result into the live feed.
- Mobile-first styling with gradients, rounded panels, and an adaptive grid.

## Usage
1. Clone or download this repo locally.
2. Open `index.html` in any browser or host the folder on a static server.
3. Set the batting/opponent team names, pick your striker/non-striker pair, and use the dropdowns to pick incoming players and bowlers; everything stays saved while you keep scoring on the turf.

## Deployment (GitHub Pages)
1. Push the repo to GitHub if it is not already there.
2. Go to the repository settings, enable GitHub Pages, and choose the `main` branch (or the branch you use) as the source.
3. After deployment the page will be live at `https://<username>.github.io/<repo-name>/`.
4. Repeat commits and pushes to publish new changes, then wait a minute for GitHub to rebuild the site.

## Next steps
- Hook the UI to a backend to store score logs persistently or share with teammates.
- Add export or print options to keep physical scorecards or pass summaries to others.
