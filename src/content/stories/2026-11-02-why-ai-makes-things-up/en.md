---
slug: why-do-ai-chatbots-make-things-up
title: "Why Do AI Chatbots Make Things Up?"
summary: "ChatGPT told a New York lawyer that a court case it had given him was real. The case was invented. The reasons behind that answer explain why chatbots bluff, why a confident tone proves nothing, and how to protect yourself."
category: technology
date: 2026-11-02
time: "12:00"
kind: long
sources:
  - name: "Kalai, Nachum, Vempala and Zhang: Why Language Models Hallucinate (paper, full text)"
    url: https://cdn.openai.com/pdf/d04913be-3f6f-4d2b-b283-ff432ef4aaa5/why-language-models-hallucinate.pdf
  - name: "arXiv: Why Language Models Hallucinate (abstract page)"
    url: https://arxiv.org/abs/2509.04664
  - name: "Anthropic: Tracing the thoughts of a large language model"
    url: https://www.anthropic.com/research/tracing-thoughts-language-model
  - name: "US District Court, Southern District of New York: Mata v. Avianca, Opinion and Order on Sanctions (22 June 2023)"
    url: https://storage.courtlistener.com/recap/gov.uscourts.nysd.575368/gov.uscourts.nysd.575368.54.0.pdf
  - name: "Columbia Journalism Review, Tow Center: AI search has a citation problem"
    url: https://www.cjr.org/tow_center/we-compared-eight-ai-search-engines-theyre-all-bad-at-citing-news.php
  - name: "arXiv: Semantic Entropy Probes: Robust and Cheap Hallucination Detection in LLMs"
    url: https://arxiv.org/abs/2406.15927
  - name: "Union of Turkish Bar Associations (TBB), Informatics and Technology Law Commission: Avukatlar İçin Yapay Zekâ Kullanımı Tavsiye Rehberi (advisory guide for lawyers, PDF)"
    url: https://hukukihabernet.teimg.com/hukukihaber-net/uploads/2026/08/tbb-yapayzekatavsiyerehberi.pdf
  - name: "Hukuki Haber: TBB'den avukatlar için yapay zeka kullanımı tavsiye rehberi"
    url: https://www.hukukihaber.net/tbbden-avukatlar-icin-yapay-zeka-kullanimi-tavsiye-rehberi
  - name: "Hukuki Haber: Güçlü bir ilk çerçeve, ancak \"tavsiye\" ile yükümlülüğün sınırı her yerde açık değil"
    url: https://www.hukukihaber.net/tbb-avukatlar-icin-yapay-zeka-rehberininin-analizi
image:
  file: image.jpg
  alt: "Close view of a rack of black servers with rows of drive bays and glowing blue and green status lights, in a computer server room."
  credit: "NOIRLab/NSF/AURA/T. Slovinský"
  license: "CC BY 4.0"
  licenseUrl: https://creativecommons.org/licenses/by/4.0/
  source: https://commons.wikimedia.org/wiki/File:NOIRLab_HQ_Server_Racks_(6V6A0402-CC).jpg
---
In May 2023, a New York lawyer named Steven Schwartz gave a federal court a set of phone screenshots. A filing he had written and a colleague had signed, in a lawsuit against an airline, cited court decisions that no one could find, and they had come from ChatGPT. In the screenshots, he asked the chatbot whether one of them, Varghese v. China Southern Airlines, was a real case, and whether the others it had given him were fake. ChatGPT answered that they were real and could be found through Westlaw, LexisNexis and the Federal Reporter, the standard places to look up American case law.

They did not exist. The judge later called the decisions non-existent judicial opinions with fake quotes and citations. The episode shows the strangest part of the problem: the chatbot that invented the case was also asked to vouch for it, and it vouched.

AI researchers call this behaviour hallucination, meaning a fluent, confident statement that is false. The question is why it happens at all.

## What a chatbot is built to do

A chatbot such as ChatGPT or Claude runs on a large language model, a program trained on enormous amounts of text. Its basic skill is continuing text. Anthropic, the company behind Claude, describes models as trained to output one word at a time and "always supposed to give a guess for the next word."

That design has a consequence. A model is not looking facts up in a catalogue and reporting what it finds. It is producing the most plausible continuation of the conversation, and a plausible-sounding answer exists for almost every question. A court case needs a name, a court, a year and a citation. The model knows exactly what those look like, so it can produce one that looks right in every way except that it is not real.

## Facts that appear once

Not all facts are equally at risk, and a 2025 research paper by Adam Tauman Kalai and colleagues explains the difference. During the first stage of training, called pretraining, a model learns the patterns of language from a huge collection of text. Some things have patterns that are easy to learn, such as spelling. The researchers note that models avoid many types of errors, spelling mistakes among them.

Other facts have no pattern at all. A birthday, a dissertation title or the name of an obscure court case cannot be worked out from anything else. If it appeared in the training text only once, or never, the model has nothing solid to lean on. The paper makes this concrete: if 20 percent of birthday facts appear exactly once in the training text, a model straight out of pretraining should be expected to get at least 20 percent of such birthday questions wrong.

Famous facts are safer. The paper notes that language models seldom go wrong on frequently repeated facts such as Einstein's birthday. The danger sits with the minor details: a little-known person, a niche paper, a small town's history.

The paper's own examples are worth remembering. Asked for the birthday of one of its authors, with the instruction to answer only if known, an open-source model gave three different wrong dates in three attempts. Asked for the title of his doctoral dissertation, three popular chatbots each gave a different, wrong title, along with a wrong year. Every answer was specific and none was correct.

## Knowing a name is not knowing the person

Anthropic published a look inside Claude in March 2025, and it points to something deeper. The researchers found that declining to answer is the model's default behaviour: a circuit that is on from the start and makes it say it does not have enough information. A separate feature, tracking whether the model recognises the subject of a question, switches that default off. For a famous name, that is what you want.

The trouble comes when the recognition misfires. In the researchers' words, this can happen when the model "recognizes a name but doesn't know anything else about that person." The feeling of familiarity turns off the "I don't know" reflex, and the model carries on and makes something up. In an experiment, the team made the model state that an unknown person, "Michael Batkin," plays chess by artificially switching on the known-answer features. Without that nudge, the model declined to answer about him.

A chatbot's confidence does not come from checking an answer against reality. It comes from a sense of familiarity with the topic, which can be present when the facts are absent. Anthropic describes its anti-hallucination training as relatively successful but imperfect.

## Rewarded for bluffing

If hallucination begins in pretraining, why does it survive the later stages meant to polish the model? The Kalai paper offers an explanation that sounds almost human: the way models are graded.

Many standard tests of language models score an answer as simply right or wrong. A correct answer earns a point, and both a wrong answer and "I don't know" earn nothing. Under that scoring, guessing is always at least as good as admitting uncertainty. Students know this about exams: when unsure, they write something plausible rather than leave a blank. The authors say models are effectively in permanent "test-taking" mode. They also point out that a model which always admits uncertainty would score lower on these tests than one that always guesses, even if it was far more trustworthy. Bluffs, they note, tend to be specific, such as "September 30" instead of "sometime in autumn."

The paper's proposed fix is to change the scoring. Tests could state a confidence threshold and take points off for wrong answers, so that guessing only pays when the model is likely to be right. The authors observe that some human exams already work this way, including India's JEE and the US SAT in earlier years.

## A model that never bluffs

Can hallucination be eliminated? The paper's answer is careful. It says hallucinations are not inevitable in principle, because a model could simply answer a fixed list of questions it knows and say "I don't know" to everything else. Such a model would not hallucinate, but it would also answer very little. One reading is that usefulness and perfect caution pull in opposite directions.

What companies and researchers do in practice is reduce the problem rather than remove it. Anthropic describes training that often leads Claude to decline questions it cannot answer. Search tools let a chatbot look up pages before answering, though the Kalai paper cautions that search is not a cure, since a model can still guess when the search does not turn up a confident answer.

Researchers are also working on warning signs. One idea is to ask the same question many times and see whether the answers agree in meaning. If they scatter, the model is probably guessing. That method, called semantic entropy, takes several times the computing power, so a later paper proposed cheaper "probes" that estimate the same signal from inside the model during a single answer. These are research tools, not a button that makes the chatbot honest.

## When search tools get it wrong too

It is tempting to think that connecting a chatbot to the internet solves the problem. A study from Columbia Journalism Review's Tow Center, published in March 2025, tested eight AI search tools. Each was given an excerpt from a news article and asked to name its headline, publisher, date and link, a task chosen so that an ordinary web search would find the original in its top three results. Across 1,600 queries, the tools were wrong more than 60 percent of the time, although the rate varied widely, from 37 percent for one tool to 94 percent for another.

The tone mattered as much as the numbers. The researchers wrote that most tools gave wrong answers with "alarming confidence." ChatGPT misidentified 134 of 200 articles, signalled low confidence only 15 times and never declined to answer. Paid versions of two tools answered more correctly than their free versions but were also wrong more often, because they gave definitive wrong answers instead of declining. More than half of the answers from two of the tools cited fabricated or broken links.

The study tested one narrow task, finding the source of news excerpts, so it does not measure every kind of question. It does show that the confident voice cannot be used as a guide.

## What a court and a bar association say

Back in New York, one detail of those screenshots is less clear: when Schwartz asked his questions. His first affidavit gave no date, but suggested that he had questioned the chatbot before the Varghese case was cited in court, or at least before its supposed text was filed. His later declaration said his doubts began only after the court's first order threatening sanctions, and that ChatGPT then replied that Varghese "does indeed exist." The court called these "shifting and contradictory explanations" and found bad faith. It also noted that his own testimony indicated he knew, before making a submission to the court, that the full text of Varghese could not be found. The chatbot's answers are documented. When he asked rests only on his own conflicting accounts, and the court rejected his claim that, before that order, he could not imagine the chatbot inventing cases.

The worry has reached Turkey too. The Union of Turkish Bar Associations (TBB) has issued an advisory guide on AI for lawyers, which the legal news site Hukuki Haber reported as published in August 2026. The guide warns that AI systems can produce case law, legislation, sources or facts that do not exist, and presents them as real. It says legal outputs should be checked against official and reliable sources, and not be passed to clients, courts or other parties without a lawyer's review. In its foreword, the TBB president writes that professional responsibility cannot be handed to AI at any stage.

The New York judge said much the same, in a different setting. The opinion states that there is nothing inherently improper about using a reliable AI tool for assistance, but that attorneys have a gatekeeping role to ensure that their filings are accurate. The court imposed a $5,000 penalty on the two lawyers and their firm, and noted that they continued to stand by the fake opinions after the court questioned them.

## Habits that protect you

The research points to practical habits.

**Ask for what the chatbot is most likely to know.** Well-known, much-discussed facts are safer. Obscure people, narrow studies, exact quotes and citation details are where made-up answers cluster.

**Treat names, numbers, dates, quotations and links as claims to check.** These are the specific details a model can produce convincingly without knowing them. Open the link. Search for the paper title. Look the case up in an official database.

**Do not ask the chatbot to confirm itself.** When Schwartz put the question to ChatGPT, the answer it gave was worthless. The same system that generated the claim has no separate way of checking it.

**Give permission to say "I don't know."** The research suggests that models bluff partly because bluffing is rewarded. Asking for an answer only if it is confident mirrors what the paper proposes for tests. It may help, but nothing guarantees it.

**Be most careful where mistakes cost most.** In law, medicine, money and schoolwork, use a chatbot to draft, summarise or explain, and verify the result against an authoritative source before relying on it.

A chatbot speaks fluently about things it knows well and about things it does not, in the same smooth voice. That, more than any single wrong answer, is what a reader should take away. A confident tone is part of how the system writes. It is not evidence about whether the answer is true.
