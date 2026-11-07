# Social posts

Every news story is shared on the X and Instagram accounts of Bitpulse. Explainers are not shared. The posts are published by hand.

## The file

The posts of a story are written in the file social.yaml in the story folder, in English only. A news story reaches main only together with that file. The tests allow a news story without one only on a draft/ branch, and fail for it on main.

The file has three fields. x holds the X post. pages is a list of Instagram pages, and each page has an image, given as a direct address to the image file, a credit naming the owner of that image, and a text of one or two paragraphs. caption holds the text written under the Instagram post. A post has as many pages as the story needs, at most twenty, and every page has its own image. The link to the story, the line that points to the link in the profile, the image credits and the note that every claim is sourced in the full story are added by scripts/social.ts, so they are never written in the file. Hashtags are not used.

A fourth field, video, turns the post into a vertical video for Instagram and X. The video is one unbroken clip of the event itself with its own sound, the logo above it and one line of text below it that never changes, followed by a short closing screen. It is never cut together from several clips and never made from still images. When no such footage exists, the field is left out and the post goes out with its pages only. The field holds source, the address of the video file, the stream or the YouTube page, start, the second the clip starts at, duration, between 8 and 20 seconds, text, the line under the clip, and credit, the owner of the video. An optional crop, written as width:height:x:y in pixels of the source, keeps the part of the picture where the moment happens, otherwise the clip is cut from the middle. The line has at most two sentences and 80 characters and takes at most three lines on the video, because a fourth line runs into the account name Instagram draws over a reel. Words between asterisks are drawn in the accent color. The video credit goes into the caption, nothing is written on the video but the line.

Two optional fields are for a slow event. speed, between 2 and 60, shows duration times speed seconds of the source within the duration, and sound, the second where the clip's own sound starts, plays that sound in real time. Without sound a sped up clip is silent. scripts/social.ts adds to the caption that the clip was sped up.

The tests check the fields, an X post of at most 280 characters with the link, at most 300 characters of text on a page, an Instagram caption within its limit and the limits of the video field. The images, the finished pages and the video are made by npm run social outside this repository. npm run social measures the lines of the video text and stops when there are more than three.

## Writing the posts

Social text uses only facts that are in the finished English story. It adds no new claim, number, quote or name, so checking it means comparing it with the story. When a fact that would make a good post is not in the story, it is left out. How it sounds is defined in docs/style-guide.md, and which images it may use is defined in docs/editorial-policy.md.

The first page is the hook described under Social posts in docs/style-guide.md, and so is the line under the video. Each page needs its own image that shows what the page says. Images are looked for in the story's sources and on the pages of the organizations in the story. Each image address is opened to confirm that it leads to the image file itself, and the largest version offered is preferred. The credit names the owner as the source names it.

## Footage

The aim is one real, unbroken moment of the event itself, or for an economy story without footage of its event, of what the story is about. It does not need to be dramatic. A speech, a presentation or a series of still images is not such a moment.

A candidate video is looked at with npm run video-scan on its address. The scan draws one sheet of frames and prints the length, the sound and the loudest moments, which often point to the moment itself. A YouTube page counts like any other address: npm run video-scan and npm run social open it through yt-dlp, so the page address itself goes into the video field. When a source offers the same video in several sizes, the scan uses the smallest, and the video field takes the largest, since both have the same timing. Once a candidate is chosen, one more scan with --from and --to over the moment settles the start second. A whole video is never downloaded.

A slow event can be sped up. This is done only when three things hold together: the footage is one fixed, unbroken shot, the event is a slow and steady change that lasts minutes, so that a stretch of the clip's length at its own speed shows almost no change, and no one in the picture speaks or moves at a normal pace. speed is then set so that the clip shows the whole change within its duration, and the refinement scan covers that whole stretch to confirm that the shot never cuts to another camera. An event that already moves at its own pace is never sped up. sound is set to a second where the event's own sound says something about the event, played in real time, and left out when there is no such moment.
