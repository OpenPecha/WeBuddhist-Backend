from pecha_api.texts.otr_transcript_parser import parse_otr_transcript

# A real OTR export (oTranscribe-style): plain intro text followed by
# paragraphs where `<span class="timestamp" data-timestamp="SECONDS">label</span>`
# marks the point in the audio where the following text begins.
SAMPLE_HTML = (
    '༧གོང་ས་མཆོག་གི་སྤྱོད་འཇུག་འཆད་ཁྲིད། <p><br /></p><p><br /></p>'
    '<p>སྒྲ་འཇུག་ཨང་༢༢༨། '
    'https://drive.google.com/file/d/11ax8HneQxn3pNVa5luDX0Io8E88tMyaI/view?usp=sharing</p>'
    '<p><br /><span class="timestamp" data-timestamp="4140.016695">1:09:00</span> '
    'རྒྱ་གར་སྐད་དུ། བོ་དྷི་སཏྭ་ཙརྱ་ཨ་བ་ཏཱ་ར། <br /></p>'
    '<p><br /></p>'
    '<p> བོད་སྐད་དུ། བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ། </p>'
    '<p><br /></p>'
    '<p><span class="timestamp" data-timestamp="4165.249377">1:09:25</span> '
    'སངས་རྒྱས་དང་བྱང་ཆུབ་སེམས་དཔའ་ཐམས་ཅད་ལ་ཕྱག་འཚལ་ལོ། །</p>'
    '<p><br /></p>'
    '<p><span class="timestamp" data-timestamp="4179.507328">1:09:39</span> '
    'བདེ་གཤེགས་ཆོས་ཀྱི་སྐུ་མངའ་སྲས་བཅས་དང་། །ཕྱག་འོས་ཀུན་ལའང་གུས་པར་ཕྱག་འཚལ་ཏེ། །'
    'བདེ་གཤེགས་སྲས་ཀྱི་སྡོམ་ལ་འཇུག་པ་ནི། །ལུང་བཞིན་མདོར་བསྡུས་ནས་ནི་བརྗོད་པར་བྱ། །</p>'
    '<p><br /></p>'
    '<p><span class="timestamp" data-timestamp="4755.921096">1:19:15</span> '
    'སྔོན་ཆད་མ་བྱུང་བ་ཡང་འདིར་བརྗོད་མེད། །སྡེབ་སྦྱོར་མཁས་པའང་བདག་ལ་ཡོད་མིན་ཏེ། །'
    'དེ་ཕྱིར་གཞན་དོན་བསམ་པ་བདག་ལ་མེད། །རང་གི་ཡིད་ལ་བསྒོམ་ཕྱིར་ངས་འདི་བརྩམས། །</p>'
    '<p><br /></p>'
    '<p><span class="timestamp" data-timestamp="4989.651923">1:23:09</span> '
    'དགེ་བ་བསྒོམ་ཕྱིར་བདག་གི་དད་པའི་ཤུགས། །འདི་དག་གིས་ཀྱང་རེ་ཞིག་འཕེལ་འགྱུར་ལ། །'
    'བདག་དང་སྐལ་བ་མཉམ་པ་གཞན་གྱིས་ཀྱང་། །ཅི་སྟེ་འདི་དག་མཐོང་ན་དོན་ཡོད་འགྱུར། །</p>'
    '<p><br /></p>'
    '<p><span class="timestamp" data-timestamp="5075.389981">1:24:35</span> '
    'དལ་འབྱོར་འདི་ནི་རྙེད་པར་ཤིན་ཏུ་དཀའ། །སྐྱེས་བུའི་དོན་སྒྲུབ་ཐོབ་པར་གྱུར་པ་ལ། །'
    'གལ་ཏེ་འདི་ལ་ཕན་པ་མ་བསྒྲུབས་ན། ། ཕྱིས་འདི་ཡང་དག་འབྱོར་པར་ག་ལ་འགྱུར། །<br /></p>'
    '<p><br /></p><p><br /></p><p><br /></p><p></p><p></p>'
)

EXPECTED_TIMESTAMPS = [
    4140.016695,
    4165.249377,
    4179.507328,
    4755.921096,
    4989.651923,
    5075.389981,
]


class TestParseOtrTranscript:
    def test_finds_one_span_per_timestamp_marker(self):
        _, spans = parse_otr_transcript(SAMPLE_HTML)

        assert [entry.timestamp for entry in spans] == EXPECTED_TIMESTAMPS

    def test_spans_are_contiguous_and_cover_the_tail_of_the_text(self):
        text, spans = parse_otr_transcript(SAMPLE_HTML)

        for earlier, later in zip(spans, spans[1:]):
            assert earlier.span.end == later.span.start
        assert spans[0].span.start < spans[0].span.end
        assert spans[-1].span.end == len(text)

    def test_span_text_matches_the_marker_it_follows(self):
        text, spans = parse_otr_transcript(SAMPLE_HTML)

        assert "རྒྱ་གར་སྐད་དུ" in text[spans[0].span.start : spans[0].span.end]
        assert "སངས་རྒྱས་དང་" in text[spans[1].span.start : spans[1].span.end]
        assert "དལ་འབྱོར་འདི་ནི" in text[spans[-1].span.start : spans[-1].span.end]

    def test_timestamp_labels_and_markup_are_stripped_from_the_text(self):
        text, _ = parse_otr_transcript(SAMPLE_HTML)

        assert "1:09:00" not in text
        assert "timestamp" not in text
        assert "<span" not in text
        assert "<p>" not in text

    def test_text_before_the_first_marker_is_not_part_of_any_span(self):
        text, spans = parse_otr_transcript(SAMPLE_HTML)

        intro = text[: spans[0].span.start]
        assert "སྒྲ་འཇུག་ཨང་༢༢༨" in intro
        assert "drive.google.com" in intro

    def test_no_markers_yields_plain_text_and_no_spans(self):
        text, spans = parse_otr_transcript("<p>hello world</p>")

        assert text == "hello world"
        assert spans == []

    def test_blank_or_missing_text_yields_nothing(self):
        assert parse_otr_transcript(None) == ("", [])
        assert parse_otr_transcript("") == ("", [])
        assert parse_otr_transcript("   ") == ("", [])
        assert parse_otr_transcript(123) == ("", [])

    def test_malformed_timestamp_attribute_does_not_crash_and_strips_label(self):
        text, spans = parse_otr_transcript(
            '<p><span class="timestamp" data-timestamp="not-a-number">1:00</span> hi</p>'
        )

        assert spans == []
        assert "1:00" not in text
        assert "hi" in text
