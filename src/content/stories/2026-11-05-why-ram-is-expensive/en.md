---
slug: why-is-ram-so-expensive
title: "Why AI Data Centers Are Making Your RAM So Expensive"
summary: "Memory makers are earning more than ever. One kind of chip built for AI is crowding out the memory in laptops and phones, and SK hynix, one of its biggest makers, expects demand to outrun supply through 2030."
category: economy
date: 2026-11-05
kind: long
sources:
  - name: "Micron: Fourth quarter fiscal 2026 results (SEC Form 8-K, exhibit 99.1)"
    url: https://www.sec.gov/Archives/edgar/data/0000723125/000072312526000018/a2026q4ex991-pressrelease.htm
  - name: "Micron: Micron announces exit from Crucial consumer business"
    url: https://investors.micron.com/news-releases/news-release-details/micron-announces-exit-crucial-consumer-business
  - name: "SK hynix: SK hynix announces 3Q26 financial results"
    url: https://www.placera.se/pressmeddelanden/sk-hynix-announces-3q26-financial-results-20261028
  - name: "TrendForce: SK hynix 3Q26 results (news)"
    url: https://www.trendforce.com/news/?p=65818
  - name: "TrendForce: Samsung 3Q26 results (news)"
    url: https://www.trendforce.com/news/?p=65900
  - name: "TrendForce: AI Server Demand Sustains Memory Contract Price Increases in 4Q26, While Consumer-Side Pressure Persists"
    url: https://www.trendforce.com/presscenter/news/20260930-13258.html
  - name: "TrendForce: DRAM Prices Seen Rising 20% QoQ in 4Q26 Despite Slower Gains"
    url: https://www.trendforce.com/news/2026/10/20/news-dram-prices-seen-rising-20-qoq-in-4q26-despite-slower-gains-ai-demand-tight-supply-support-outlook/
  - name: "TrendForce: Tight DRAM Supply Gives Suppliers Greater Pricing Power in HBM"
    url: https://www.trendforce.com/presscenter/news/20260602-13074.html
  - name: "TrendForce: Memory Prices Soar; DRAM and NAND Flash to Account for 68% of Major CSP CapEx in 2027"
    url: https://www.trendforce.com/presscenter/news/20260825-13198.html
  - name: "TrendForce: DRAM Market Bulletin, 23 September 2026"
    url: https://trendforce.com/research/download/RP260923EN
  - name: "Wikimedia Commons: AMD Epyc 9754 in dual-CPU-socket server system (file description)"
    url: https://commons.wikimedia.org/wiki/File:AMD_Epyc_9754_in_Dual-CPU-Socket-Serversystem_(%E6%9E%81%E5%AE%A2%E6%B9%BEGeekerwan)_07.png
  - name: "Wikipedia: Dynamic random-access memory"
    url: https://en.wikipedia.org/wiki/Dynamic_random-access_memory
  - name: "Wikipedia: High Bandwidth Memory"
    url: https://en.wikipedia.org/wiki/High_Bandwidth_Memory
image:
  file: image.jpg
  alt: "Inside a server with two large AMD Epyc processors on a black motherboard, each surrounded by rows of green memory modules in slots, with yellow-black cooling fans at the lower left."
  credit: "极客湾Geekerwan"
  license: "CC BY 3.0"
  licenseUrl: https://creativecommons.org/licenses/by/3.0/
  source: https://commons.wikimedia.org/wiki/File:AMD_Epyc_9754_in_Dual-CPU-Socket-Serversystem_(%E6%9E%81%E5%AE%A2%E6%B9%BEGeekerwan)_07.png
---
A year ago, Micron, a memory maker based in Boise, Idaho, sold about $11.3 billion worth of chips in a quarter. In its latest quarter it sold $54.2 billion. Its gross margin, the share of sales left after the cost of making the chips, went from 44.7% to 86.8% over the same year. For a chipmaker, that is an extraordinary change.

The same boom is in the price tags on laptops, phones and memory sticks. The short answer to "why is RAM so expensive" is that the companies that make it have found a better customer than you. The longer answer explains why that customer is so hard to compete with, and why nobody who sells memory is promising relief soon.

## What RAM is, and the chip that is eating it

RAM is the memory a device uses for whatever it is doing right now: the open apps, the browser tabs, the game level. Most of it is a type called DRAM, short for dynamic random-access memory. It holds data as tiny electric charges, which fade, so the chip must keep refreshing them. It also forgets everything when the power goes off. That is why files live on a separate drive and RAM is only the workspace.

Laptops, desktops and phones all use DRAM. So do servers, the computers in data centers.

AI has created demand for a special version called HBM, high-bandwidth memory. Instead of one flat chip, HBM stacks several DRAM chips, typically 4 to 16, on top of a base chip and links them with vertical connections. The stack sits right beside the processor. Its very wide data path lets the processor pull data far faster than ordinary memory allows. AI processors are the main customers for that speed.

The two products are made in the same kind of factory, from the same kind of silicon wafer, the thin disc on which chips are printed. That shared supply is the heart of the story.

## How much memory an AI chip wants

An AI accelerator carries a lot of HBM. TrendForce, a firm that tracks the memory market, says upgrades to custom AI chips this year raise the HBM per chip from 96 or 192 gigabytes to 216 or 288. For next year it expects Nvidia's Rubin Ultra to reach 384 gigabytes per processor. For comparison, the whole server in the photo at the top holds about 825 gigabytes of ordinary memory.

Ordinary server memory is in demand too. TrendForce reports that better supplies of server processors are lifting purchases by cloud companies for memory that supports what it calls agentic AI, meaning AI systems that carry out tasks on their own. And the spending is huge. TrendForce estimates that DRAM and NAND flash, the chips behind solid-state drives, will make up 47% of the capital spending of the major cloud companies this year and 68% next year.

## Why the squeeze reaches ordinary memory

A factory that makes more HBM has less room for everything else. TrendForce estimates that HBM takes about 22% of the DRAM wafers fed into production by the three largest suppliers at the end of this year, rising to about 30% at the end of 2027. Yet HBM is only about 9% of the memory produced this year, measured in bits, and about 13% in 2027. So a wafer given to HBM yields far less memory than one given to ordinary chips. TrendForce points to larger chips in later HBM generations and expects the crowding-out of conventional DRAM to intensify.

It is also a question of where the effort goes. TrendForce says suppliers are putting their most advanced production lines toward server products, and that this keeps the market undersupplied. The supply of memory for phones is tight as capacity moves to servers.

The choice shows in company decisions. In December 2025 Micron announced it would leave its Crucial consumer business, the consumer brand sold through shops, online retailers and distributors. Sumit Sadana, its chief business officer, said the aim was "to improve supply and support for our larger, strategic customers in faster-growing segments." The release cited a surge in demand for memory and storage from AI data centers.

The choice is not limited to the biggest names. Macronix, a Taiwanese chipmaker, said it is phasing out the ROM chips that hold [Nintendo Switch games](/en/stories/macronix-phases-out-rom-switch-cartridges/) and giving capacity to NAND, a faster-growing kind of memory. Those chips are not DRAM, but the pattern is similar: factory lines are limited, and a maker gives them to the memory that is growing fastest.

## What higher prices look like

TrendForce tracks contract prices, the prices that large buyers such as PC makers agree with suppliers. Those costs feed into the devices people buy. A TrendForce news report of 20 October, drawing on Korean and Taiwanese press, says DRAM contract prices rose about 80% in the second quarter of this year and about 40% in the third. TrendForce expects a smaller rise in the fourth quarter, though its figures differ by measure. A release on 30 September projected 10% to 15% for conventional DRAM, the kind used in everyday devices. The 20 October report put the overall fourth-quarter rise at about 20%.

The makers' own results tell the same story. Kim Jae-june, an executive of Samsung's memory business, said its DRAM prices rose about 20% in the third quarter, with shipments up only a low to mid single-digit percentage, according to News 1 as relayed by TrendForce. Prices are climbing much faster than the quantity sold.

Buyers are feeling it. TrendForce says higher component costs are weighing on notebook sales, that rising costs and exhausted stocks of low-cost memory are cutting smartphone production, and that PC brands are shrinking the storage in their machines to save money. Televisions, set-top boxes and wearables, it adds, have little room to absorb higher costs.

## Who has already bought the future

A second reason prices can stay high is that much of the supply is spoken for. SK hynix says it has signed long-term supply agreements with 14 major customers, including large cloud companies. TrendForce notes that this is up from 10 in the second quarter. These agreements typically run five years. SK hynix says the volume secured so far equals more than half of its total production capacity for 2027 and 2028, with prices set within agreed ranges.

TrendForce says these agreements are shrinking the supply left for open negotiation. It also notes the other side of these contracts: some agreements signed since the second quarter include price ceilings, and some suppliers' increases are expected to lag the market average because of how their contracts work.

## When could it ease?

Nobody can say, and the companies that sell memory are the ones giving most of the forecasts. Here is what they and TrendForce say.

SK hynix said in its results that it expects the structure in which demand exceeds supply to continue through 2030. It points to the technical difficulty of the newest chip processes and the long lead times for building new factories. The Korean outlet Chosun Biz, as relayed by TrendForce, reported that its DRAM and HBM output is effectively sold out through 2029. Samsung expects chip supply to tighten further in 2027, according to Reuters as relayed by TrendForce. Both companies are speaking as sellers.

New supply is coming, slowly. SK hynix says a plant called M15X will reach full capacity by the end of this year and that the first phase of its Yongin site will enter full operation next year. TrendForce expects the combined bit supply of server DRAM and HBM to grow 27% in 2027, helped by new factory capacity in the second half of that year. But it warns that PC memory supply could fall in 2027 as capacity shifts to servers. PC makers, it says, are still buying aggressively because they expect tightness.

The pace of price rises is already slowing. TrendForce's reasons are a higher starting point, weaker buying power among consumers and the ceilings in long-term contracts. Price rises for phone memory are slowing because large rises are already priced in. A slowing rise is not a fall, however, and none of the forecasts quoted here describes prices going down.

## What could change the picture

A few things could shift the balance, and none of them is certain.

Suppliers can move production between HBM and ordinary DRAM. TrendForce notes that in the first quarter of this year, HBM earned less per wafer than a common type of server memory module, because HBM prices are set annually and had not kept up with quick rises in ordinary prices. The Korean outlet iNews24, as relayed by TrendForce, reports that SK hynix expects the profit gap between HBM and conventional DRAM to narrow significantly. If making ordinary memory pays as well as HBM, makers have less reason to favour one over the other.

Demand could soften. TrendForce says high memory costs may lead cloud companies to cut the memory in each system or turn to other designs. TrendForce's October report also names the Chinese maker CXMT, which is working on a new memory design. Citing the Korean outlet MoneyToday, it says this has not yet significantly affected spot prices, the prices paid for immediate delivery. The report adds that full commercial production is generally expected only after 2028.

And forecasts can be wrong. Micron's own guidance, a revenue forecast of about $61.5 billion for its next quarter, is the company's own expectation, not a certainty.

## Waiting in line

The memory in a phone or a laptop is, in effect, in a queue behind the memory in an AI server, because the same factories supply both and the AI side pays more. SK hynix expects demand to exceed supply through 2030, and Samsung expects supply to get tighter next year. TrendForce sees price rises easing, in a market that stays short of supply.
