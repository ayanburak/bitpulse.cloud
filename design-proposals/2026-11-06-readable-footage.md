# Proposal: count footage only at an address the video scan can open

Status: open, waiting for review.

Branch: proposal/readable-footage

This changes one paragraph in agents/writer.md. It does not change how the site looks, so it has no screenshots.

## The reason

A news story is chosen only when real footage of its event exists, because every news story is shared as a vertical video. On 2026-11-06 the writer chose the Nasdaq debut of Agility Robotics and passed on three YouTube videos of its Digit robot at work. The scan and npm run social both read video through ffmpeg, which can open a direct video file or a stream address but not a YouTube page. The writer could not scan the videos. The social writer then found only silent, edited montages on Agility's own site, and the story went out with no video field.

The footage rule is meant to guarantee a video for every news story. The video is the format most likely to reach people who do not visit the site yet. A video that the tools cannot read gives no such guarantee.

## The change

agents/writer.md gains two sentences after the one that asks the writer to confirm the footage. Footage counts only at an address that npm run video-scan opens, with its own sound. A page the scan cannot read, such as a YouTube page, does not count, and the writer looks for the same footage as a file from its owner or chooses another story.

The ISS story of 2026-11-06 is the working example: NASA's stream address opened in the scan, and the moment was found from its frames.
