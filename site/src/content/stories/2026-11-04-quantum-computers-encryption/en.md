---
slug: will-quantum-computers-break-encryption
title: "Will Quantum Computers Break Encryption?"
summary: "Nobody can name the date, and that is only part of the story. The danger is narrower than it sounds, secrets sent today can be recorded and opened later, and the fix is already running in your browser."
category: technology
date: 2026-11-04
time: "12:00"
kind: long
sources:
  - name: "Cloudflare: State of the post-quantum Internet in 2025"
    url: https://blog.cloudflare.com/pq-2025/
  - name: "NIST: NIST Releases First 3 Finalized Post-Quantum Encryption Standards"
    url: https://www.nist.gov/news-events/news/2024/08/nist-releases-first-3-finalized-post-quantum-encryption-standards
  - name: "NIST: Post-Quantum Cryptography FAQs"
    url: https://csrc.nist.gov/projects/post-quantum-cryptography/faqs
  - name: "NIST: Transition to Post-Quantum Cryptography Standards (IR 8547, final, October 2026)"
    url: https://csrc.nist.gov/pubs/ir/8547/final
  - name: "NIST: IR 8547, full report (PDF)"
    url: https://nvlpubs.nist.gov/nistpubs/ir/2026/NIST.IR.8547.pdf
  - name: "Gidney (Google Quantum AI): How to factor 2048 bit RSA integers with less than a million noisy qubits (arXiv)"
    url: https://arxiv.org/abs/2505.15917
  - name: "Google Research: Safeguarding cryptocurrency by disclosing quantum vulnerabilities responsibly"
    url: https://research.google/blog/safeguarding-cryptocurrency-by-disclosing-quantum-vulnerabilities-responsibly/
  - name: "Google: Google's timeline for PQC migration"
    url: https://blog.google/innovation-and-ai/technology/safety-security/cryptography-migration-timeline/
  - name: "Google: Meet Willow, our state-of-the-art quantum chip"
    url: https://blog.google/technology/research/google-willow-quantum-chip/
  - name: "Cain et al.: Shor's algorithm is possible with as few as 10,000 reconfigurable atomic qubits (arXiv preprint)"
    url: https://arxiv.org/abs/2603.28627
  - name: "UK National Cyber Security Centre: Timelines for migration to post-quantum cryptography"
    url: https://www.ncsc.gov.uk/guidance/pqc-migration-timelines
  - name: "Signal: Signal Protocol and Post-Quantum Ratchets (SPQR)"
    url: https://signal.org/blog/spqr/
  - name: "Apple Security Research: iMessage with PQ3"
    url: https://security.apple.com/blog/imessage-pq3/
image:
  file: image.jpg
  alt: "Three people in white cleanroom suits, masks and gloves look closely at a gold-coloured stack of metal plates and colourful wiring, the cooling part of a superconducting quantum computer, in a laboratory."
  credit: "FMNLab"
  license: "CC BY 4.0"
  licenseUrl: https://creativecommons.org/licenses/by/4.0/
  source: https://commons.wikimedia.org/wiki/File:Measuring_a_qubit_leaves_no_room_for_error.jpg
---
The padlock in your browser's address bar does two jobs, and a future quantum computer threatens one of them far more than the other. To see which, it helps to look at what happens in the second before a page loads.

Your phone and a bank's server have never met. They need to agree on a secret code, and they have to do it over a network where anyone may be listening. The tool for this is called public-key cryptography. Each side does some maths that is easy to perform but practically impossible to undo, and at the end both hold the same secret key, while an eavesdropper who saw every message cannot work it out. Cloudflare, the internet infrastructure company, calls this step key agreement.

Then comes a second job: proof. The server must show that it really is your bank and not an impostor. It does this with a digital signature, which is also built on public-key maths.

Once the key is agreed, the rest is simple. Your messages, passwords and card numbers are scrambled with that key using a different family of methods, symmetric encryption, in which one key locks and unlocks the data. A widely used example is AES.

So the padlock rests on two kinds of maths. The question is which of them a quantum computer could break.

## What a quantum computer is good at

A quantum computer is not a faster laptop. It uses the physics of very small things to handle certain problems in a completely different way, and only a few special problems get a dramatic speed-up.

Two of those problems are exactly the ones that hold up public-key cryptography. RSA relies on the fact that multiplying two huge prime numbers is easy while splitting the result back into those primes is not. Elliptic curve cryptography, another widely used method, relies on a related hard problem. A procedure called Shor's algorithm lets a large enough quantum computer attack both of them. The UK's National Cyber Security Centre puts it plainly: quantum computers will be able to efficiently solve the hard mathematical problems that today's public-key systems depend on.

That is the whole threat in one sentence. Both key agreement and signatures would fail, and with them the way strangers on the internet set up secrets and trust each other.

## Why AES gets to stay

The other half of the padlock is in much better shape. A second quantum method, Grover's algorithm, speeds up brute-force guessing of a key, but only by the square root: a search that needs a trillion steps needs about a million. That helps an attacker much less than Shor's algorithm helps against RSA.

NIST, the US standards agency, has looked at this closely. Its FAQ says it is quite likely that Grover's algorithm will provide "little or no advantage" in attacking AES, that AES-128 "will remain secure for decades to come," and that the larger AES-192 and AES-256 "will still be safe for a very long time." Those conclusions assume nobody finds a new weakness in AES itself. Cloudflare puts the practical result simply: symmetric ciphers such as AES-GCM are already secure against quantum computers.

So the headline "quantum computers will break all encryption" is wrong about one word: "all." The part that would break is the part that lets strangers agree on a key and prove who they are. The part that scrambles the data afterwards would survive.

## The distance between 105 and half a million

Does such a machine exist? Not remotely. Google's Willow chip has 105 qubits, the basic units of a quantum computer. Its main achievement was about reliability. Qubits are fragile and make errors, and Willow showed that errors fell, rather than grew, as Google linked more of them into larger error-correcting groups. Google calls this being "below threshold" and describes it as an outstanding challenge for the field. On a benchmark test that has no practical commercial use yet, it finished in under five minutes a computation that Google says would take a leading supercomputer an enormous amount of time. That is a milestone for the field. It is not a code-breaker.

Breaking RSA would need far more, and the estimates of how much have been falling. In 2019, Craig Gidney, a researcher at Google Quantum AI, and a colleague estimated that cracking a 2048-bit RSA key would take 20 million noisy qubits. In May 2025, Gidney published a new estimate: fewer than a million, running for under a week. In March 2026, Google's researchers reported that the 256-bit elliptic curve problem, which protects cryptocurrency and other systems, could be solved with fewer than 500,000 physical qubits in a few minutes, about 20 times fewer than before. These are paper estimates under stated hardware assumptions.

Other teams are exploring different hardware. A group including the physicist John Preskill posted a preprint in March 2026, a paper shared before formal review. It argues that a machine built from atomic qubits could run Shor's algorithm with as few as 10,000 of them, and that about 26,000 would attack a 256-bit elliptic curve in a few days. The authors say the figures rest on plausible assumptions and that substantial engineering challenges remain.

Put those together and the picture is this. Google's Willow chip has 105 qubits. The estimates for breaking public-key cryptography run from about 10,000 to under a million, and they are all for machines that do not yet exist. The gap is large, but the estimates have fallen sharply in a few years.

## Recorded today, read tomorrow

Here is why a machine that does not exist yet already matters. Someone who cannot read your encrypted traffic today can still copy it and store it. If a capable quantum computer arrives in ten or twenty years, they can open the old files then. The name is "harvest now, decrypt later," and Apple, Signal and NIST all use it.

The risk is greatest for information that stays sensitive for a long time: state secrets, medical records, business plans, private messages. A password that expires next month is not worth hoarding for twenty years. A diplomatic cable might be.

Notice which part of the padlock this concerns. It is key agreement, because a recorded connection can be opened later only if the key that was agreed at the time can be worked out. Cloudflare says this makes it urgent to upgrade key agreement now. Signatures are different. A forged signature only helps an attacker at the moment of the attack, so they matter only once a capable quantum computer actually exists. Cloudflare adds that moving to post-quantum signatures is much more difficult.

## What is already switched on

The replacements exist. NIST published its first three post-quantum standards in August 2024. One, called ML-KEM, covers key agreement. Two cover signatures: ML-DSA as the main one, and SLH-DSA, built on a different kind of maths, as a backup in case the first one turns out to have a weakness. NIST said they were ready to use and urged organisations to start integrating them immediately.

Much of the shift has happened without anyone noticing. Chrome turned on a hybrid method, which runs a post-quantum key agreement together with a classic one so that an attacker must beat both, by default on desktop in March 2024. Firefox followed in November 2024, and Apple's phones and computers began using it with their 2025 software releases. By late October 2025, Cloudflare reported that a majority of the human-driven traffic it handles was already protected this way.

Messaging apps have moved too. Apple announced a post-quantum design called PQ3 for iMessage in February 2024, and says it addresses current and future threats from quantum computers. Signal added a post-quantum upgrade to its protocol in October 2025. Signal says its purpose is to protect conversations if cryptographically relevant quantum computers eventually become a reality.

Many of these deployments are hybrid: Signal, for example, runs its new upgrade alongside its existing protocol and mixes their keys. A flaw in one part does not automatically expose everything.

## The deadlines governments set

Governments have chosen dates, mostly in the 2030s. The UK's cyber agency asks organisations to define their migration goals and plan by 2028, to finish the highest-priority work by 2031, and to complete the move by 2035. In the United States, NIST's final transition report, published in October 2026, says that it will deprecate quantum-vulnerable public-key cryptography after 2030 and disallow it after 2035. It also repeats a target that US federal agencies must meet. The most sensitive systems have to adopt post-quantum key agreement by the end of 2030 and signatures by the end of 2031. The report notes that earlier changes of this kind took 10 to 20 years, so the deadlines leave little margin.

Companies are setting their own dates. In March 2026, Google said it was setting a 2029 target for its own migration. It said that the timeline reflects progress in quantum hardware, error correction and resource estimates for factoring, and that the threat to encryption is relevant today because data can be stored now and decrypted later. It treats signatures as a future threat that must be handled before a capable machine exists.

## The one thing nobody can tell you

So when will the first machine that can break RSA arrive? Nobody knows. NIST's 2024 announcement says only that some experts predict such a device could appear within a decade, and does not claim to know. Cloudflare is blunter. It says the honest answer is that no one really knows for sure, because there are too many unknowns, and that whether it comes in 2034 or 2050, it will be too soon. Every number in this article is an estimate of a machine that nobody has built, and every future date is a planning choice, not a prediction.

What can be said with more confidence is smaller but useful. Encryption as a whole is not on the edge of collapse. The data-scrambling half of the padlock is expected to survive. The half that is at risk has tested replacements, which are standardised and already switched on for a large share of web traffic. What is left is slow, unglamorous work: finding every place where old public-key methods are used and replacing them. For most people that work happens in updates, without any action on their part. Keeping your browser, phone and messaging apps up to date is the simple part you can play.
