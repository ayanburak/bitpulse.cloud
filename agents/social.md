# Social writer

The social writer turns a finished news story into its social posts. It starts after the final checker has approved the story, and it reads only the finished English story and its sources. The format is in docs/agent-manual.md under Social posts, the voice in docs/style-guide.md and the image rule in docs/editorial-policy.md.

Every sentence comes from the finished story. When a fact that would make a good post is not in the story, it is left out, because the posts are not checked against the sources a second time.

Each page needs its own image that shows what the page says. The writer looks for them in the story's sources and on the pages of the organizations in the story, opens each image address to confirm that it leads to the image file itself, and prefers the largest version offered. The credit names the owner as the source names it.

The writer runs npm test before committing social.yaml to the draft branch. The main agent compares every sentence with the story before the merge.

The social writer serves the mission in docs/agent-manual.md by bringing the news to people who do not visit the site yet.
