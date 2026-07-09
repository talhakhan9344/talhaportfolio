#!/usr/bin/env python3
"""Generate Talha_Khan_Resume.pdf.

Reproduces the resume's visual design (Helvetica, gold rules, justified
body text) from structured content below. Edit the CONTENT section and
re-run:  python3 scripts/generate_resume.py
"""
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth

# ── Design constants (measured from the original PDF) ─────────────
PAGE_W, PAGE_H = letter            # 612 x 792
MARGIN_X = 52.8
CONTENT_W = PAGE_W - 2 * MARGIN_X  # 506.4
TOP_Y = 750                        # first baseline on a page
BOTTOM_Y = 30                      # don't draw below this
FOOTER_Y = 18

DARK = (0.101961, 0.101961, 0.101961)
GREY = (0.333333, 0.333333, 0.333333)
GOLD = (0.541176, 0.427451, 0.121569)

F, FB, FI = 'Helvetica', 'Helvetica-Bold', 'Helvetica-Oblique'


class Doc:
    def __init__(self, path):
        self.c = canvas.Canvas(path, pagesize=letter)
        self.page = 1
        self.y = TOP_Y
        self._footer()

    def _footer(self):
        t = f'Talha Khan - Resume - Page {self.page}'
        self.c.setFont(F, 7.5)
        self.c.setFillColorRGB(*GREY)
        self.c.drawString((PAGE_W - stringWidth(t, F, 7.5)) / 2, FOOTER_Y, t)

    def need(self, h):
        if self.y - h < BOTTOM_Y:
            self.c.showPage()
            self.page += 1
            self.y = TOP_Y
            self._footer()

    def _text(self, x, ln, font, size, wordspace=0):
        t = self.c.beginText(x, self.y)
        t.setFont(font, size)
        # Tw is graphics state, not reset by BT/beginText -- always set
        # it explicitly (including 0) or a prior justified line's
        # word-spacing silently bleeds into every later draw.
        t.setWordSpace(wordspace)
        t.textOut(ln)
        self.c.drawText(t)

    # ── text primitives ────────────────────────────────────────────
    def wrap(self, text, font, size, width):
        words = text.split(' ')
        lines, cur = [], ''
        for w in words:
            trial = (cur + ' ' + w) if cur else w
            if stringWidth(trial, font, size) <= width or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    def _draw_lines(self, lines, x, font, size, leading, color, width,
                    justify):
        self.c.setFillColorRGB(*color)
        for i, ln in enumerate(lines):
            ws = 0
            if justify and i < len(lines) - 1 and ln.count(' '):
                ws = (width - stringWidth(ln, font, size)) / ln.count(' ')
            self._text(x, ln, font, size, ws)
            if i < len(lines) - 1:
                self.y -= leading

    def para(self, text, font=F, size=10, leading=13.5, color=DARK,
             gap=3.5, justify=True, indent=0):
        width = CONTENT_W - indent
        lines = self.wrap(text, font, size, width)
        self.need(len(lines) * leading + gap)
        self._draw_lines(lines, MARGIN_X + indent, font, size, leading,
                         color, width, justify)
        self.y -= leading + gap

    def bullet(self, text):
        size, leading, indent = 10, 12.2, 11
        width = CONTENT_W - indent
        prefix = '–  '
        pw = stringWidth(prefix, F, size)
        # first line holds the dash + text; continuations align with dash
        first = self.wrap(text, F, size, width - pw)
        rest = ' '.join(first[1:])
        lines = [first[0]] + (self.wrap(rest, F, size, width)
                              if rest else [])
        self.need(len(lines) * leading + 2)
        self.c.setFillColorRGB(*DARK)
        for i, ln in enumerate(lines):
            x = MARGIN_X + indent
            w = width
            if i == 0:
                self._text(x, prefix, F, size)
                x += pw
                w -= pw
            ws = 0
            if i < len(lines) - 1 and ln.count(' '):
                ws = (w - stringWidth(ln, F, size)) / ln.count(' ')
            self._text(x, ln, F, size, ws)
            self.y -= leading
        self.y -= 2

    def bullets_two_col(self, items, col_gap=24):
        """Lay out items in two columns: first half left, second half right."""
        size, leading, indent = 10, 11.6, 11
        half = (len(items) + 1) // 2
        left_items, right_items = items[:half], items[half:]
        col_w = (CONTENT_W - col_gap) / 2 - indent
        prefix = '–  '
        pw = stringWidth(prefix, F, size)

        def wrap_col(col_items):
            out = []
            for text in col_items:
                first = self.wrap(text, F, size, col_w - pw)
                rest = ' '.join(first[1:])
                lines = [first[0]] + (self.wrap(rest, F, size, col_w)
                                      if rest else [])
                out.append(lines)
            return out

        left_lines = wrap_col(left_items)
        right_lines = wrap_col(right_items)
        col_h = lambda ls: sum(len(l) for l in ls) * leading + len(ls) * 1.2
        self.need(max(col_h(left_lines), col_h(right_lines)))
        y0 = self.y

        def draw_col(col_lines, x0):
            y = y0
            self.c.setFillColorRGB(*DARK)
            for lines in col_lines:
                for i, ln in enumerate(lines):
                    x = x0 + indent
                    w = col_w
                    if i == 0:
                        t = self.c.beginText(x, y)
                        t.setFont(F, size)
                        t.setWordSpace(0)
                        t.textOut(prefix)
                        self.c.drawText(t)
                        x += pw
                        w -= pw
                    t2 = self.c.beginText(x, y)
                    t2.setFont(F, size)
                    t2.setWordSpace(0)
                    t2.textOut(ln)
                    self.c.drawText(t2)
                    y -= leading
                y -= 1.2
            return y

        y_left = draw_col(left_lines, MARGIN_X)
        y_right = draw_col(right_lines, MARGIN_X + col_w + indent + col_gap)
        self.y = min(y_left, y_right)

    def section(self, title):
        self.need(13 + 4.5 + 15 + 15)   # title + rule + first content
        self.y -= 2                      # extra air before a section
        self.c.setFillColorRGB(*DARK)
        self.c.setFont(FB, 12)
        self.c.drawString(MARGIN_X, self.y, title)
        self.y -= 4.5 + 2.5
        self.c.setLineWidth(0.6)
        self.c.setStrokeColorRGB(*GOLD)
        self.c.line(MARGIN_X, self.y, MARGIN_X + CONTENT_W, self.y)
        self.y -= 15

    def line(self, text, font=F, size=10, color=DARK, gap=6):
        self.need(size + gap)
        self.c.setFont(font, size)
        self.c.setFillColorRGB(*color)
        self.c.drawString(MARGIN_X, self.y, text)
        self.y -= size + gap

    def skills(self, label, text):
        size, leading = 10, 13.5
        lbl = label + ':  '
        lbl_w = stringWidth(lbl, FB, size)
        first_w = CONTENT_W - lbl_w
        words = text.split(' ')
        lines, cur, w = [], '', first_w
        for word in words:
            trial = (cur + ' ' + word) if cur else word
            if stringWidth(trial, F, size) <= w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur, w = word, CONTENT_W
        lines.append(cur)
        self.need(len(lines) * leading + 5.0)
        self.c.setFillColorRGB(*DARK)
        self.c.setFont(FB, size)
        self.c.drawString(MARGIN_X, self.y, lbl)
        for i, ln in enumerate(lines):
            self.c.setFont(F, size)
            self.c.drawString(MARGIN_X + (lbl_w if i == 0 else 0),
                              self.y, ln)
            if i < len(lines) - 1:
                self.y -= leading
        self.y -= leading + 5.0

    def gap(self, h):
        self.y -= h

    def save(self):
        self.c.showPage()
        self.c.save()


def main():
    out = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), 'Talha_Khan_Resume.pdf')
    d = Doc(out)

    # ── Header ─────────────────────────────────────────────────────
    d.c.setFillColorRGB(*DARK)
    d.c.setFont(FB, 20)
    d.c.drawString(MARGIN_X, d.y, 'TALHA KHAN')
    d.y -= 16
    d.line('Technical Project Manager  |  AI Product & Platform Delivery'
           '  |  Healthcare', size=10.5, color=GOLD, gap=3.5)
    d.line('New Jersey, USA  |  talha.khan9344@gmail.com  |  '
           '(848) 348-1267  |  linkedin.com/in/talhakhan9344',
           size=10, color=GREY, gap=6)

    # ── Executive Summary ──────────────────────────────────────────
    d.section('EXECUTIVE SUMMARY')
    d.para(
        'Technical Project Manager, currently at Innovatix Technology '
        'Partners, where I lead AI-assisted development and end-to-end '
        'product launches, from OpenParser AI to the Innovatix ATS '
        'platform, using tools like Claude, Cursor, ChatGPT, and Copilot '
        'across my team. With 8+ years of '
        'professional experience, all in technology, I’ve paired account '
        'stewardship with delivery excellence across AI and Healthcare '
        'portfolios, leading international, cross-border teams, with '
        'the technical fluency to partner closely with engineering and '
        'the executive presence to align C-suite stakeholders, often in '
        'the same conversation.')

    # ── Technical Skills ───────────────────────────────────────────
    d.section('TECHNICAL SKILLS')
    d.skills('Project & Product',
             'Technical Project Management, Project Planning & '
             'Scheduling, Risk & Dependency Management, Budgeting & Cost '
             'Control, Product Roadmapping, SDLC Leadership, Agile '
             '(Scrum/SAFe), Release Management, OKRs & KPI Frameworks')
    d.skills('AI / GenAI & Data',
             'LLM Product Development (RAG Pipelines, Prompt Engineering, '
             'AI Agents, Evals), Llama 3, OpenAI, Anthropic, Gemini APIs, '
             'Pinecone, LlamaIndex, Python, Pandas, Scikit-Learn, SQL, '
             'Power BI, Tableau, Snowflake')
    d.skills('Cloud & Infrastructure',
             'AWS Lambda, API Gateway, S3, RDS, CI/CD, .NET, '
             'Microservices, Azure, Power Platform')
    d.skills('Automation',
             'AI-Assisted Development, Process Optimization')
    d.skills('Domains',
             'Healthcare (payer), AdTech, E-Commerce, SaaS, Enterprise AI '
             'Platforms')

    # ── Core Competencies ──────────────────────────────────────────
    d.section('CORE COMPETENCIES')
    d.para('Technical Project Management  |  Product Vision & '
           'Roadmapping  |  AI & ML Platform Delivery  |  Distributed '
           'Team Leadership (International, Cross-Border)  |  Revenue '
           'Growth & Client Expansion  |  Agile / SAFe / Scrum at Scale '
           ' |  RPA & Process Automation  |  Risk, Scope & Budget '
           'Management',
           justify=False, gap=3.5)

    # ── Career Highlights ──────────────────────────────────────────
    d.section('CAREER HIGHLIGHTS')
    d.need(140)  # keep the highlight list from orphaning its last line
    for h in [
        '$6.5M+ in active client business managed; contributed to $4.5M+ '
        'in account growth (Macrosoft)',
        '2 AI products shipped zero-to-production at Innovatix: '
        'OpenParser AI and Innovatix ATS (1,000+ resumes AI-parsed)',
        'Up to 47% reduction in delivery timelines via AI-assisted '
        'development at Innovatix',
        '20%+ average under-budget delivery across managed projects',
        '4 direct reports, plus 10+ indirect reports coordinated at '
        'Innovatix',
        '3-5 concurrent AI, cloud & analytics projects delivered at any '
        'given time',
    ]:
        d.para(h, justify=False, gap=6)

    # ── Professional Experience ────────────────────────────────────
    d.section('PROFESSIONAL EXPERIENCE')

    d.line('Technical Project Manager', font=FB, size=10.5, gap=2.5)
    d.line('Innovatix Technology Partners  |  July 2025 - Present  |  '
           'New Jersey, USA', font=FI, size=10, color=GREY, gap=6)
    for b in [
        'I own and drive product vision, roadmap, and delivery for '
        'OpenParser AI, a RAG-based document intelligence platform with '
        '30+ AI agents, across the full delivery lifecycle, project '
        'planning, engineering leadership, and go-to-market execution.',
        'Built Innovatix ATS from the ground up, an AI-native '
        'applicant tracking platform now being productized for market '
        'launch. Personally developed the initial MVP through '
        'AI-assisted development, then led a lean team of one engineer '
        'and one QA to production.',
        'Shipped the ATS platform’s core AI capabilities: bulk resume '
        'parsing, candidate-job matching, and Teams-integrated '
        'interviews with automated post-interview analysis, JD-match '
        'scoring, competency assessment, hiring recommendations, '
        'letting non-technical interviewers evaluate candidates with '
        'technical rigor. 1,000+ resumes parsed to date.',
        'Leading 4 direct reports and 10+ indirect reports, applying '
        'AI-assisted development to cut delivery timelines by up to '
        '47% and establish a repeatable AI-augmented delivery model.',
    ]:
        d.bullet(b)

    d.gap(2)
    d.need(65)
    d.line('Scrum Master', font=FB, size=10.5, gap=2.5)
    d.line('ASI (Advertising Specialty Institute)  |  June 2024 - June '
           '2025', font=FI, size=10, color=GREY, gap=6)
    for b in [
        'Facilitated Agile ceremonies, sprint planning, daily '
        'stand-ups, reviews, and retrospectives for two '
        'cross-functional teams totaling 14-20 members.',
        'Led backlog refinement and retrospective sessions across 2-3 '
        'concurrent projects, driving continuous process improvement.',
        'Partnered with product owners and stakeholders to maintain '
        'sprint predictability and team velocity across both teams.',
    ]:
        d.bullet(b)

    d.gap(2)
    d.need(65)
    d.line('Technical Project Manager', font=FB, size=10.5, gap=2.5)
    d.line('Macrosoft  |  January 2019 - June 2024', font=FI, size=10,
           color=GREY, gap=6)
    for b in [
        'Managed 2-3 concurrent healthcare technology projects, serving '
        'as primary point of contact for enterprise accounts, growing '
        'managed client business to $6.5M+ and contributing $4.5M+ in '
        'account growth.',
        'Built AWS-native analytics workflows (Lambda, API Gateway, S3, '
        'RDS) enabling secure, compliant data processing for healthcare '
        'clients.',
        'An international team came together under my coordination, '
        'improving velocity by 33% through Agile KPIs, sprint '
        'governance, and structured capacity planning.',
        'Partnered directly with C-suite and director-level '
        'stakeholders across a 3-5 project portfolio; the risk and '
        'dependency management frameworks I put in place prevented '
        'three major delivery delays.',
    ]:
        d.bullet(b)

    d.gap(2)
    d.need(65)
    d.line('Senior Software Engineer (Consulting) - Concurrent, '
           'Part-Time', font=FB, size=10.5, gap=2.5)
    d.line('Cinnova Technologies, LLC  |  November 2021 - January 2023',
           font=FI, size=10, color=GREY, gap=6)
    for b in [
        'Part-time consulting engagement carried out alongside the '
        'full-time Technical Project Manager role at Macrosoft above.',
        'Delivered web applications, APIs, and BI dashboards for '
        'clients using Angular, .NET, and cloud-based development '
        'workflows.',
    ]:
        d.bullet(b)

    d.gap(2)
    d.need(65)
    d.line('Data Scientist', font=FB, size=10.5, gap=2.5)
    d.line('Macrosoft  |  July 2018 - December 2018  |  Internal '
           'Rotation', font=FI, size=10, color=GREY, gap=6)
    for b in [
        'Led analytics development for an out-of-home AdTech platform '
        'client, delivering the full end-to-end analytics stack 2 months '
        'ahead of schedule (5-month project completed in 3).',
        'Built ML models for claims classification and provider '
        'segmentation using Python, Pandas, and Scikit-Learn, achieving '
        '12-18% accuracy improvements over prior baselines.',
        'Developed executive-grade BI dashboards (Power BI, Tableau, '
        'QuickSight) enabling KPI tracking across 20+ enterprise '
        'clients; implemented speech analytics via CallMiner resulting '
        'in 15% call-center efficiency gain.',
    ]:
        d.bullet(b)

    # ── Education ──────────────────────────────────────────────────
    d.section('EDUCATION')
    d.line('BS in Business Administration - Accounting & Finance, Minor '
           'in Economics', font=FB, size=10.5, gap=2.5)
    d.para('Peter T. Paul College of Business & Economics, University of '
           'New Hampshire  |  August 2013 - December 2016  |  Durham, NH',
           font=FI, color=GREY, justify=False, gap=3)
    d.para("GPA: 3.41  |  Dean's List Honors",
           justify=False, gap=6)

    # ── Certifications ─────────────────────────────────────────────
    d.section('CERTIFICATIONS & CREDENTIALS')
    d.bullets_two_col([
        'PMP - Project Management Professional',
        'PMI-ACP - Agile Certified Practitioner',
        'SAFe 6 Agilist',
        'SAFe 6 Scrum Master',
        'PSM I - Professional Scrum Master',
        'PSPO I - Professional Scrum Product Owner',
        'AWS Certified Cloud Practitioner',
        'Microsoft Data Science Professional Program',
    ])

    d.save()
    print('wrote', out, '- pages:', d.page)


if __name__ == '__main__':
    main()
