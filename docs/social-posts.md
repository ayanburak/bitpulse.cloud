# Social posts

Every news story is shared on the X and Instagram accounts of Bitpulse. Explainers are not shared. The posts are published by hand. A clip is a post for Instagram only that has no story, described at the end of this document.

## The file

The posts of a story are written in the file social.yaml in the story folder, in English only. A news story is published only together with that file.

The file has three fields. x holds the X post. pages is a list of Instagram pages, and each page has an image, given as a direct address to the image file, a credit naming the owner of that image, and a text. A page may also have a position, such as 85% 50%, when the subject of a wide photo sits near an edge. The page shows the photo cut to the shape of its upper part, from the center unless a position moves the cut, the first number across and the second down. caption holds the text written under the Instagram post. A post has one page, and everything else goes into the caption. The link to the story, the line that points to the link in the profile, the image credits and the note that every claim is sourced in the full story are added by site/scripts/social.ts, so they are never written in the file. Hashtags are not used.

The tests check the fields, the number of pages, an X post of at most 280 characters with the link, the length of the text on a page and an Instagram caption within its limit. The images and the finished page are made by npm run social outside this repository. It also saves the page as post.mp4, a silent vertical video of six seconds in which nothing moves, so the post can be shared on Instagram as a reel. The page sits in the middle of the 1080 by 1920 frame, so the feed, which cuts a reel to 4:5, shows exactly the page. On X the page goes out as an image.

## Writing the posts

An Instagram page carries one short sentence of at most 120 characters, and the caption carries the rest of the story. A page is looked at for a moment while scrolling, so it gives one fact and a strong photo, and the reader who stops finds the details below it.

What Instagram shows, the text of the page and the caption, is plain sentences. It has no dash of any kind, no bullet, no formatting and no emoji. A compound such as Houthi-run is written out as run by the Houthis, and a score such as 3-0 as 3 to 0. A dash stays only inside a name that can not be written another way, such as Jean-Noël or F-35. Older posts keep the format they were made in. The date from which the tests apply each rule is written in site/src/social.ts.

Social text uses only facts that are in the finished English story. It adds no new claim, number, quote or name, so checking it means comparing it with the story. When a fact that would make a good post is not in the story, it is left out. How it sounds is defined in docs/style-guide.md, and which images it may use is defined in docs/editorial-policy.md.

The page is the hook described under Social posts in docs/style-guide.md. Its image shows what the page says. Images are looked for in the story's sources and on the pages of the organizations in the story. Each image address is opened to confirm that it leads to the image file itself, and the largest version offered is preferred. The credit names the owner as the source names it.

## Clips

A clip shows footage or a picture of an event that someone else published, such as a video on YouTube or a post on X, and goes to Instagram only. It never becomes a story on the site, so it has no X post and no link to a story.

Its file is clip.yaml in a folder under site/social-posts, outside this repository, next to the media that bitpulse fetch saved. source is the address of the footage and credit its owner as the site names them. text is the sentence on the page, one plain sentence of at most 120 characters. caption is the news in plain sentences. start and end give the seconds of the video to use, and position moves the cut like on a story page.

npm run clip lays the page over the video, keeps its sound and saves post.mp4. A picture becomes a still video like a story post. The source line, Source: followed by the owner and the address, is added to the caption by the script. The same rules as for any post apply: the text reports what the footage shows and gives no message, the footage shows the event itself and the rules on graphic content come first. Footage from another day may be used when it shows the people of the news, and the caption then says what it shows and when it was filmed.

When the clip shows something that a social media account published about itself, such as work a person says they did or a claim they make, the sentence on the page starts with A user says or A user did: A user says she ran 100 km in Antarctica. The post shows what the account published and does not present it as a confirmed fact. The caption names the account and keeps the claim attributed to it.

