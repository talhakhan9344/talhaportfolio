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
TOP_Y = 726.4                      # first baseline on a page
BOTTOM_Y = 48                      # don't draw below this
FOOTER_Y = 32.4

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
        if wordspace:
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

    def para(self, text, font=F, size=8.7, leading=11.6, color=DARK,
             gap=2.9, justify=True, indent=0):
        width = CONTENT_W - indent
        lines = self.wrap(text, font, size, width)
        self.need(len(lines) * leading + gap)
        self._draw_lines(lines, MARGIN_X + indent, font, size, leading,
                         color, width, justify)
        self.y -= leading + gap

    def bullet(self, text):
        size, leading, indent = 8.5, 11.2, 10
        width = CONTENT_W - indent
        prefix = '–  '
        pw = stringWidth(prefix, F, size)
        # first line holds the dash + text; continuations align with dash
        first = self.wrap(text, F, size, width - pw)
        rest = ' '.join(first[1:])
        lines = [first[0]] + (self.wrap(rest, F, size, width)
                              if rest else [])
        self.need(len(lines) * leading + 2.6)
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
        self.y -= 2.6

    def section(self, title):
        self.need(13 + 4.6 + 14.7 + 24)   # title + rule + first content
        self.y -= 2                        # extra air before a section
        self.c.setFillColorRGB(*DARK)
        self.c.setFont(FB, 10.5)
        self.c.drawString(MARGIN_X, self.y, title)
        self.y -= 4.6 + 2.5
        self.c.setLineWidth(0.6)
        self.c.setStrokeColorRGB(*GOLD)
        self.c.line(MARGIN_X, self.y, MARGIN_X + CONTENT_W, self.y)
        self.y -= 14.7

    def line(self, text, font=F, size=8.7, color=DARK, gap=5.4):
        self.need(size + gap)
        self.c.setFont(font, size)
        self.c.setFillColorRGB(*color)
        self.c.drawString(MARGIN_X, self.y, text)
        self.y -= size + gap

    def skills(self, label, text):
        size, leading = 8.7, 11.6
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
    d.y -= 15
    d.line('Technical Project Manager  |  AI Product & Platform Delivery'
           '  |  Healthcare', size=10.5, color=GOLD, gap=2.5)
    d.line('New Jersey, USA  |  talha.khan9344@gmail.com  |  '
           '(848) 348-1267  |  linkedin.com/in/talhakhan9344',
           size=8.5, color=GREY, gap=5)

    # ── Executive Summary ──────────────────────────────────────────
    d.section('EXECUTIVE SUMMARY')
    d.para(
        'Technical Project Manager and product builder — I conceived '
        'and shipped two AI products from zero to production: OpenParser '
        'AI (enterprise document intelligence) and Innovatix ATS (an '
        'AI-native recruitment platform now heading to market), owning '
        'both from product vision through engineering leadership and '
        'go-to-market. With 9+ years of professional experience (8+ in '
        'technology), I’ve paired account stewardship with delivery '
        'excellence across AI and Healthcare portfolios — leading '
        'distributed teams across the U.S., Pakistan, and India, with '
        'the technical fluency to partner closely with engineering and '
        'the executive presence to align C-suite stakeholders, often in '
        'the same conversation.')

    # ── Core Competencies ──────────────────────────────────────────
    d.section('CORE COMPETENCIES')
    d.line('Product Vision & Roadmapping  |  Technical Project '
           'Management  |  AI & ML Platform Delivery', gap=2.9)
    d.line('Distributed Team Leadership (US · Pakistan · India)  |  '
           'Revenue Growth & Client Expansion  |  Agile / SAFe / Scrum '
           'at Scale', gap=2.9)
    d.line('RPA & Process Automation  |  Risk, Scope & Budget Management',
           gap=2.9)

    # ── Career Highlights ──────────────────────────────────────────
    d.section('CAREER HIGHLIGHTS')
    for h in [
        '$6.5M+ in active client business managed; contributed to $4.5M+ '
        'in account growth',
        'Up to 47% reduction in delivery timelines via AI-assisted '
        'development (since 2024)',
        '2 AI products shipped zero-to-production — OpenParser AI '
        'and Innovatix ATS (1,000+ resumes AI-parsed)',
        '21% infrastructure cost reduction through legacy platform '
        'modernization',
        '20% average under-budget delivery across managed projects',
        '6 direct reports, plus a broader team of 12+ coordinated across '
        'functions',
        '3-5 concurrent AI, cloud & analytics projects delivered at any '
        'given time',
    ]:
        d.line(h, gap=5.4)

    # ── Professional Experience ────────────────────────────────────
    d.section('PROFESSIONAL EXPERIENCE')
    d.line('Innovatix Technology Partners  |  Total Tenure: 8+ Years  |  '
           'New Jersey, USA (Hybrid)', font=FI, size=8.3, color=GREY,
           gap=8.7)

    d.line('Technical Project Manager', font=FB, size=9.3, gap=2.2)
    d.line('Innovatix Technology Partners  |  January 2019 - Present  |  '
           'New Jersey, USA · Hybrid', font=FI, size=8.3, color=GREY,
           gap=5.7)
    for b in [
        'Conceived and drove product vision, roadmap, and delivery for '
        'OpenParser AI, a RAG-based document intelligence platform with '
        '30+ AI agents — owning project planning, engineering '
        'leadership, and go-to-market execution across the full delivery '
        'lifecycle.',
        'Served as the primary point of contact for requirements, '
        'expectations, and contractual delivery across enterprise '
        'accounts spanning data & analytics, healthcare intelligence, '
        'and healthcare payer clients — pairing account stewardship '
        'with delivery excellence to drive $4.5M+ in account growth.',
        'Led 6 direct reports and coordinated a broader team of 12+ '
        'across the U.S., Pakistan, and India — engineers, QA '
        'analysts, and data scientists — improving team velocity by '
        '33% through Agile KPIs, sprint governance, and structured '
        'capacity planning.',
        'Managed 3-5 concurrent projects in production at any given time '
        '— partnering directly with C-suite and director-level '
        'stakeholders against high-stakes delivery timelines, and '
        'consistently delivering on time, within scope, and under '
        'budget.',
        'Built Innovatix ATS from the ground up (2025-present) — an '
        'AI-native applicant tracking platform now being productized for '
        'market launch. Personally developed the initial MVP through '
        'AI-assisted development, then led a lean team (1 engineer, 1 '
        'QA) to production, owning product vision, roadmap, and release '
        'management end to end.',
        'Shipped the ATS platform’s AI capabilities — bulk AI '
        'resume parsing, AI candidate-job matching, and Microsoft '
        'Teams-integrated interviews with automated post-interview AI '
        'analysis (JD-match scoring, competency assessments, hiring '
        'recommendations) — enabling non-technical interviewers to '
        'technically evaluate candidates, with 1,000+ resumes AI-parsed '
        'to date.',
        'Since 2024, leveraged AI-assisted development to accelerate '
        'delivery timelines by up to 47%, meaningfully reducing project '
        'costs in the process, and establishing a repeatable '
        'AI-augmented delivery model across the organization.',
        'Implemented structured risk, issue, and dependency management '
        'frameworks that prevented three major delivery delays, '
        'protecting revenue-critical client commitments.',
        'Led modernization of a legacy claims and provider onboarding '
        'platform to .NET and AWS, reducing infrastructure spend by 21% '
        'and cutting release cycles from 2 weeks to 1 day.',
        'Built AWS-native analytics workflows (Lambda, API Gateway, S3, '
        'RDS) enabling secure, compliant data processing for AdTech and '
        'HealthTech clients.',
    ]:
        d.bullet(b)

    d.gap(4)
    d.need(60)  # keep role header with its first bullet
    d.line('Data Scientist', font=FB, size=9.3, gap=2.2)
    d.line('Innovatix Technology Partners  |  July 2018 - December 2018 '
           ' |  Remote · Internal Rotation', font=FI, size=8.3,
           color=GREY, gap=5.7)
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

    d.gap(4)
    d.need(60)
    d.line('Senior Software Engineer (Consulting) - Concurrent, '
           'Part-Time', font=FB, size=9.3, gap=2.2)
    d.line('Cinnova Technologies, LLC  |  November 2021 - January 2023  '
           '|  Remote', font=FI, size=8.3, color=GREY, gap=5.7)
    for b in [
        'Part-time consulting engagement carried alongside the full-time '
        'Technical Project Manager role at Innovatix above.',
        'Delivered web applications, APIs, and BI dashboards for '
        'U.S.-based clients using Angular, .NET, and cloud-based '
        'development workflows.',
    ]:
        d.bullet(b)

    # ── Early Career ───────────────────────────────────────────────
    d.section('EARLY CAREER')
    d.para('Founder & CEO, Grounded Sax Nature, Inc.  |  Jul 2017 '
           '– Apr 2018 — Founded an eco-friendly apparel '
           'startup (eucalyptus-based denim); business plan through '
           'incorporation and distribution outreach.', size=8.3,
           leading=11.5, gap=3.4, justify=False)
    d.para('RPA Analyst, Accelirate, Inc.  |  Mar 2017 – Jun 2017 '
           '— Built RPA workflow POCs for financial data processes '
           '(Mark-to-Market, AR/GL, invoice entry).', size=8.3,
           leading=11.5, gap=3.4, justify=False)

    # ── Education ──────────────────────────────────────────────────
    d.section('EDUCATION')
    d.line('BS in Business Administration - Accounting & Finance, Minor '
           'in Economics', font=FB, size=9.3, gap=2.2)
    d.line('Peter T. Paul College of Business & Economics, University of '
           'New Hampshire  |  August 2013 - December 2016  |  Durham, NH',
           font=FI, size=8.3, color=GREY, gap=2.7)
    d.line("GPA: 3.41  |  Dean's List Honors (Fall 2013, Spring 2014, "
           "Fall 2014)  |  Dean's List HIGH Honors (Spring 2016)",
           size=8.3, gap=5.4)

    # ── Certifications ─────────────────────────────────────────────
    d.section('CERTIFICATIONS & CREDENTIALS')
    for cert in [
        'PMP - Project Management Professional (PMI)',
        'PMI-ACP - Agile Certified Practitioner (PMI)',
        'SAFe 6 Agilist',
        'SAFe 6 Scrum Master',
        'PSM I - Professional Scrum Master (Scrum.org)',
        'PSPO I - Professional Scrum Product Owner (Scrum.org)',
        'AWS Certified Cloud Practitioner',
        'AI Product Management - Certificate, Duke University (Coursera)',
    ]:
        d.bullet(cert)
    d.gap(2)
    d.para('Additional credentials: AWS Technical Professional & Cloud '
           'Economics Accredited (AWS partner training) - Microsoft Data '
           'Science Professional Program & Power Platform Fundamentals - '
           'Python Programmer (DataCamp) - UiPath RPA Developer - '
           'WorkFusion Power User - CallMiner BI Analyst+', size=8.3,
           leading=11.5, gap=3.4, justify=False)

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
             'Power BI, Tableau, QuickSight, Snowflake')
    d.skills('Cloud & Infrastructure',
             'AWS Lambda, API Gateway, S3, RDS, CI/CD, .NET, '
             'Microservices, Azure, Power Platform')
    d.skills('Automation',
             'RPA (UiPath, WorkFusion, Power Automate), AI-Assisted '
             'Development, Process Optimization')
    d.skills('Domains',
             'Healthcare (payer), AdTech, with additional exposure to '
             'InsurTech, E-Commerce, Manufacturing, SaaS, Enterprise AI '
             'Platforms')

    # ── Languages ──────────────────────────────────────────────────
    d.section('LANGUAGES')
    d.line('English (Native/Bilingual)  |  Urdu (Native/Bilingual)  |  '
           'Punjabi (Full Professional)', gap=5.4)

    d.save()
    print('wrote', out, '- pages:', d.page)


if __name__ == '__main__':
    main()
