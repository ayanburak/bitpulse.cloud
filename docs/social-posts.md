# Social posts

Every news story is shared on the X and Instagram accounts of Bitpulse. Explainers are not shared. The posts are published by hand.

## The file

The posts of a story are written in the file social.yaml in the story folder, in English only. A news story is published only together with that file.

The file has three fields. x holds the X post. pages is a list of Instagram pages, and each page has an image, given as a direct address to the image file, a credit naming the owner of that image, and a text. A page may also have a position, such as 85% 50%, when the subject of a wide photo sits near an edge. The page shows the photo cut to the shape of its upper part, from the center unless a position moves the cut, the first number across and the second down. caption holds the text written under the Instagram post. From 8 November 2026 a post has one page, and everything else goes into the caption. Posts made before that keep their pages, at most twenty, each with its own image. The link to the story, the line that points to the link in the profile, the image credits and the note that every claim is sourced in the full story are added by site/scripts/social.ts, so they are never written in the file. Hashtags are not used.

The tests check the fields, the number of pages, an X post of at most 280 characters with the link, the length of the text on a page and an Instagram caption within its limit. The images and the finished page are made by npm run social outside this repository. It also saves the page as post.mp4, a silent vertical video of six seconds in which nothing moves, so the post can be shared on Instagram as a reel. The page sits in the middle of the 1080 by 1920 frame, so the feed, which cuts a reel to 4:5, shows exactly the page. On X the page goes out as an image.

## Writing the posts

An Instagram page carries one short sentence of at most 120 characters, and the caption carries the rest of the story. A page is looked at for a moment while scrolling, so it gives one fact and a strong photo, and the reader who stops finds the details below it. Posts made before 7 November 2026 had one or two paragraphs of up to 300 characters on a page and keep them.

Social text uses only facts that are in the finished English story. It adds no new claim, number, quote or name, so checking it means comparing it with the story. When a fact that would make a good post is not in the story, it is left out. How it sounds is defined in docs/style-guide.md, and which images it may use is defined in docs/editorial-policy.md.

The page is the hook described under Social posts in docs/style-guide.md. Its image shows what the page says. Images are looked for in the story's sources and on the pages of the organizations in the story. Each image address is opened to confirm that it leads to the image file itself, and the largest version offered is preferred. The credit names the owner as the source names it.
