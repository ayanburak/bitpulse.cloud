"""
file: tests/test_collect.py
importable: nothing, pytest loads this file

description: Checks the parts of gathering that need no network: quotes, names, pages, storyboards, sheets.
"""

import io
from datetime import date
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

from PIL import Image

import reels.collect.commons
import reels.collect.gather
from reels.collect.commons import search
from reels.collect.gather import picture_sheet
from reels.collect.pages import addresses, credit
from reels.collect.quotes import find_quote
from reels.collect.story import Story, names, quotes
from reels.collect.youtube import storyboard

BODY = """The United States is offering a reward, "possibly relocation," officials said.

## Trump and the talks

He also said Iran wants to end the conflict. "We're dealing with them now. They want to make a deal very badly," he said. The State Department's Rewards for Justice program gave no "details."
"""
STORY = Story("2026-11-07-test", "Title", "Summary", date(2026, 11, 7), BODY, [])


# A quote may hold sentences of its own, and a two word quote is a term, not a quote.
def test_quotes_keep_their_inner_sentences_and_skip_terms():
    found = [quote.words for quote in quotes(STORY)]
    assert "We're dealing with them now. They want to make a deal very badly," in found
    assert "details." not in found
    assert "possibly relocation," not in found


def test_names_join_their_words_and_drop_the_possessive():
    counted = dict(names(STORY))
    assert "State Department Rewards for Justice" in counted
    assert "Iran" in counted


def test_a_quote_is_found_in_captions_by_likeness():
    words = [(10.0 + i, w) for i, w in enumerate("so we will see what happens we're dealing with them now they want to make a deal very badly they have".split())]
    match = find_quote("We're dealing with them now. They want to make a deal very badly,", words)
    assert match is not None and match.second == 16.0 and match.score > 0.95
    assert find_quote("an entirely different sentence about the weather", words) is None


def test_page_addresses_take_linked_full_images_and_skip_logos():
    html = """<meta property="og:image" content="/og.jpg">
    <a href="https://site.org/up/poster.jpg"><img src="https://site.org/up/poster-300x176.jpg"></a>
    <img src="/img/footer-logo.png"><img srcset="/a-400.jpg 400w, /a-1600.jpg 1600w" src="/a-400.jpg">"""
    found = addresses("https://site.org/page/", html)
    assert found[:2] == ["https://site.org/og.jpg", "https://site.org/up/poster.jpg"]
    assert "https://site.org/a-1600.jpg" in found
    assert not any("logo" in url for url in found)


# Two grids of 2 by 2 frames, the second cut short to one row, as YouTube sends the last one.
def test_storyboard_frames_get_their_seconds(tmp_path):
    message = MIMEMultipart()
    for size in ((640, 360), (640, 180)):
        data = io.BytesIO()
        Image.new("RGB", size, "gray").save(data, "JPEG")
        message.attach(MIMEImage(data.getvalue(), "jpeg"))
    path = tmp_path / "board.mhtml"
    path.write_bytes(message.as_bytes())
    layout = {"width": 320, "height": 180, "rows": 2, "columns": 2, "fragments": [{"duration": 20}, {"duration": 8}]}
    frames = storyboard(path, layout)
    assert [round(second, 1) for second, _ in frames] == [0, 5, 10, 15, 20, 22]
    assert frames[0][1].size == (320, 180)


# A Commons picture keeps the address of its small copy, the sheet is made from that copy.
def test_commons_picture_gets_a_sheet_of_its_small_copy(tmp_path, monkeypatch):
    answers = iter([{"query": {"search": [{"title": "File:Stadium.jpg"}]}},
                    {"query": {"pages": [{"title": "File:Stadium.jpg", "imageinfo": [{
                        "url": "https://upload/Stadium.jpg", "thumburl": "https://upload/480px-Stadium.jpg",
                        "width": 4032, "height": 3024, "extmetadata": {}}]}]}}])
    monkeypatch.setattr(reels.collect.commons, "query", lambda params: next(answers))
    item = search("stadium", "image", 6)[0]
    assert item.thumb == "https://upload/480px-Stadium.jpg"
    small = io.BytesIO()
    Image.new("RGB", (480, 360), "green").save(small, "JPEG")
    monkeypatch.setattr(reels.collect.gather.web, "get", lambda url: small.getvalue())
    sheet = picture_sheet(item.thumb, "C1", tmp_path / "C1.jpg")
    assert sheet == tmp_path / "C1.jpg" and Image.open(sheet).width == 240


# A credit is read from a caption after the image, from a copyright field, or from the file name,
# and left empty when the page gives none. The same photograph in two sizes and a branded copy count once.
def test_page_pictures_keep_their_credit_and_skip_copies():
    page = "https://news.example/story"
    html = ('<meta property="og:image" content="https://img.example/branded/1200/a1.jpg">'
            '<img src="https://img.example/1024/a1.jpg"><span>Image source, </span>Getty Images</span>'
            '<img srcset="https://img.example/800/a1.jpg 800w">'
            '<img src="https://img.example/b2.jpg">{"copyrightHolder":"Reuters"}'
            '<img src="https://img.example/AFP__2026__x.jpg"><img src="https://img.example/c3.jpg">'
            '<img src="https://img.example/d4.jpg"><span>Getty Images</span>')
    urls = addresses(page, html)
    assert urls == ["https://img.example/1024/a1.jpg", "https://img.example/b2.jpg",
                    "https://img.example/AFP__2026__x.jpg", "https://img.example/c3.jpg", "https://img.example/d4.jpg"]
    assert [credit(html, url, page) for url in urls] == ["Getty Images", "Reuters", "AFP", "", "Getty Images"]
