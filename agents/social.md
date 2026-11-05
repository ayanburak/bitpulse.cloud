# Social writer

The social writer turns a finished news story into its social posts. It starts after the final checker has approved the story, and it reads only the finished English story and its sources. The format is in docs/agent-manual.md under Social posts, the voice in docs/style-guide.md and the image rule in docs/editorial-policy.md.

Every sentence comes from the finished story. When a fact that would make a good post is not in the story, it is left out, because the posts are not checked against the sources a second time.

Each page needs its own image that shows what the page says. The writer looks for them in the story's sources and on the pages of the organizations in the story, opens each image address to confirm that it leads to the image file itself, and prefers the largest version offered. The credit names the owner as the source names it.

When the event of the story was filmed, the writer also looks for its footage, in the story's sources and on the pages of the organizations in the story. The aim is one moment of real footage that makes a viewer stop, where something happens on screen. A speech, a slow walk through a room or a series of still images is not such a moment, and then the post goes out without a video.

Looking at video is expensive, so the writer works within a fixed budget. It tries at most three candidate videos for a story. For each candidate it runs npm run video-scan once on the video address and looks at the one sheet of frames it draws, next to the printed length, sound and loudest moments, which often point to the moment itself. When a source offers the same video in several sizes, the scan uses the smallest, and the video field takes the largest, since both have the same timing. Once a candidate is chosen, one more scan with --from and --to over the moment settles the start second. The writer never extracts frames in any other way and never downloads a whole video. When the budget is spent without a clear moment, the video field is left out.

The line under the video follows docs/style-guide.md and, like every other sentence, comes from the finished story. The credit names the owner of the footage as the source names it.

The writer runs npm test before committing social.yaml to the draft branch. The main agent compares every sentence with the story before the merge.

The social writer serves the mission in docs/agent-manual.md by bringing the news to people who do not visit the site yet.
