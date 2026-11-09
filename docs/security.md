# Security model

The whole code of Bitpulse is public, so an attacker is assumed to have read all of it. Protection comes from keys, from separated rights and from layers, so that one failed layer does not open the whole system. How to report a problem is in [SECURITY.md](../SECURITY.md).

## Separation

Every service on the server runs as its own user and can write only to its own folders. The API and the render worker are not allowed to open a connection to the internet, which is enforced by the operating system and not by their code. An attacker who takes over the API can not send data out or write a page, and one who takes over the worker has no way to reach the database.

The API listens only inside the server. From the internet, only the panel files and the panel routes can be reached. The routes for devices and for the radar never pass through the public web server.

GitHub has no access to the server. Code is released only from the maintainer's machine, so a stolen GitHub account can change the repository but can not change the live site.

## Keys

There are two kinds of key and each opens only its own routes. Only a hash of a key is stored, so a leaked database or backup holds nothing that works. A key lasts ninety days and can be revoked at once from the panel.

A device key can upload drafts and publish. It can not withdraw a story, undo a publish or create a key, because those routes exist only in the panel behind a second factor.

The radar reads pages from the open web all day, which makes its key the likeliest to leak. A radar key can write radar events and nothing else, it can not read a story or publish one. A radar key can only be made on the server.

## The panel

There is one account and no registration page. The password is stored with Argon2id, and the second factor is a passkey, which a fake site can not trick out of its owner. Paper backup codes exist for a lost passkey. After five wrong attempts the login locks for fifteen minutes, and the web server also limits how often it can be tried.

A session lives on the server and ends after thirty minutes without use or twelve hours in any case. Its cookie is out of reach of scripts and is only sent to the panel itself. Every change needs a token and a matching origin, so another site can not submit a form on behalf of the signed in editor.

Publishing, undoing, withdrawing and managing keys and passkeys ask for the second factor again, for that exact action on that exact target. Decisions on radar events and marking a post as shared do not change the site and need only a session.

## Text from the web

Anything read from the web is treated as untrusted, including the headlines and links shown in the panel. Headlines are shown as plain text, and a link that is not a web address is refused before it is stored. Raw HTML inside a story is dropped when pages are built. The panel previews a story in an isolated frame, and both the site and the panel send a strict content security policy and load nothing from third parties.

The API never fetches an address it is given. An image or a page is downloaded by the device or by the radar, and the radar refuses any address or redirect that leads to a private network.

## Uploaded files

Cover images and social pages are decoded and drawn again, so what reaches the disk is pixels the API produced, without metadata and without any byte of the upload. Sizes and pixel counts are limited before decoding. The server has no tool to rebuild a video, so a video is checked by its signature and leaves only as a download, the panel never plays it.

## Knowing what happened

Every change is written to an audit log, and the database refuses any edit or removal of that log and of story versions. Logins, publishes, undos and key changes are sent to Telegram by a separate service with its own bot. Because that bot is not the radar's, a compromised radar can neither silence those notices nor imitate them.

## Data and dependencies

An encrypted backup is written every night and kept for fourteen days. The server holds only the public half of the key, so nothing on it can open its own backups.

Dependencies are locked to exact versions and updated by hand with tests. GitHub Actions are pinned to full commit hashes. Every commit and every push is scanned for secrets.

## Accepted risks

A writing session can publish, and it reads text from the web, so a hidden instruction in a source could in principle lead to an unwanted story. This was accepted to keep publishing to one approval. That is why the key of a session can publish but can not remove anything or change access, why every publish produces a notice and why the panel can undo it in one step.

A story that reaches the site was approved by one person. There is no second reviewer by design, the site has one editor.
