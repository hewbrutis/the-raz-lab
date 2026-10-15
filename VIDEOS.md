# From the printer — Instagram carousels

Who: a visitor who just read the lab intro and wants to see the real prints, grouped.

Source of truth: the Commander's desktop folder
`C:\Users\Matt\Desktop\StarNet Trusted\STARNET Storefront Website\Embed Links to Videos from socials`

Each `.txt` file is one category and one carousel on the public page.

Live API: `GET /api/videos` re-reads the folder when a text file changes, then writes `videos.json` as a snapshot. If the folder is missing (public host), the snapshot still serves.
