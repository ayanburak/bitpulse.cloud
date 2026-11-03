---
slug: google-amazon-ai-chip-race
title: "Google and Amazon Made the Same AI Chip Move on the Same Day"
summary: "Two tech giants took the stage on the same day to make AI software run more easily on their own chips. The goal is clear: win over the developers who decide which hardware gets used."
category: technology
date: 2026-10-20
kind: news
sources:
  - name: "Google Cloud Blog: TorchTPU is now open source"
    url: https://cloud.google.com/blog/topics/ai-infrastructure/torchtpu-is-now-open-source-run-native-pytorch-on-tpus
  - name: "PyTorch Blog: Introducing TorchNeuron"
    url: https://pytorch.org/blog/introducing-torchneuron-native-pytorch-backend-for-aws-trainium/
  - name: "Techzine: TorchNeuron brings PyTorch code to AWS Trainium without modifications"
    url: https://www.techzine.eu/news/infrastructure/145105/torchneuron-brings-pytorch-code-to-aws-trainium-without-modifications/
  - name: "The Register: Nvidia's CUDA moat may not be as impenetrable as you think"
    url: https://www.theregister.com/2024/12/17/nvidia_cuda_moat/
  - name: "Wikipedia: Tensor Processing Unit"
    url: https://en.wikipedia.org/wiki/Tensor_Processing_Unit
  - name: "Wikipedia: PyTorch"
    url: https://en.wikipedia.org/wiki/PyTorch
  - name: "Wikipedia: Annapurna Labs"
    url: https://en.wikipedia.org/wiki/Annapurna_Labs
image:
  file: image.jpg
  alt: "Close view of a shiny silicon wafer covered in many colorful microchip patterns."
  credit: "DrHughManning"
  license: "CC BY-SA 4.0"
  licenseUrl: https://creativecommons.org/licenses/by-sa/4.0/
  source: https://commons.wikimedia.org/wiki/File:Semiconductor_Wafer_of_Microelectronics.jpg
---
Some tech rivalries heat up without big advertising campaigns, through announcements that look dull from the outside. October 20 was one of those days. At the PyTorch Conference, a gathering of software developers, Google and Amazon delivered nearly the same message: your AI software can now run easily on our chips too.

At first glance that sounds like an ordinary product launch. Behind it sits one of the most expensive contests of the AI age. Training and running AI systems takes extremely powerful chips, and the best known name in that field is Nvidia. Google and Amazon have spent years building their own alternatives.

## Why companies build their own chips

Google has used its own AI chip, the TPU, in its data centers since 2015 and introduced it to the world in May 2016. Amazon built on the expertise of Annapurna Labs, a chip company it bought in 2015, and announced its Trainium AI chip in December 2020.

It is no surprise that these companies want their own hardware. AI infrastructure is among their [largest investments](/en/stories/alphabet-worst-day-google-cloud-search/), and a company that designs its own chips can shape them around its own needs.

But a powerful chip is only half of the story. If developers do not use it, even the best hardware stays on the shelf.

## The game console problem

Game consoles offer a useful way to picture this. What runs on a console matters as much as how powerful it is. If everyone makes games for one console, a stronger rival is not enough on its own. The games have to arrive there too.

AI works in a similar way. PyTorch is a widely used software tool for building and training AI models. Meta developed it, released it in 2016, and today it is governed by an independent body under the Linux Foundation. Many well known systems, ChatGPT among them, were built with it. Amazon says 85 percent of AI researchers and developers write their code in PyTorch.

Here is the problem. Moving that code to a different chip is often hard. According to the technology publication Techzine, developers who wanted to switch chips often spent months rewriting and revalidating their code.

## What Google and Amazon did

Both companies are trying to shrink that obstacle.

Google made TorchTPU, a tool it developed with Meta, open source, which means anyone can now see and use its code. The company says a training system used with the tool has been tested on up to 8,000 chips.

Amazon released TorchNeuron for its own chips. The company says moving a model to Trainium can sometimes take a single settings change. The tool is currently in a public trial.

Both moves share one aim: letting developers keep working with the tools they already know, with no new language to learn. To return to the console picture, the companies want existing games to run on their machines without being rewritten one by one.

## What this means for Nvidia

Nvidia's strength does not come from its chips alone. The software world it has built over the years is a major advantage too, and PyTorch can run on Nvidia chips through that software.

Still, the picture is shifting. An Intel executive told The Register that most developers no longer work at the level closest to the chip, and instead use higher level tools such as PyTorch. Intel is a Nvidia rival, so that is one side's view. That gives rivals an opening. If PyTorch runs smoothly on other chips, switching could become easier.

That does not mean Nvidia will be easily unseated. The chip business runs on habits and investments built over years. But two major rivals pressing on the same door on the same day shows where the battle is moving.

## Why it is too early to get excited

For now, most of these promises come from the companies themselves. Amazon's own blog post says some features are missing from the first release. It also reports that about 69,000 of roughly 154,000 test results were skipped, and that about 22,000 of those came from operations that are not supported yet.

The real test will happen outside these companies. Once independent developers try the tools on their own projects, it will become clear how well the single setting promise holds up. The race is heating up, but it is too early to say who is ahead.
