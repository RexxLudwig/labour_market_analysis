import os
import json
import logging
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors

logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self, output_path: str = "output/labour_policy_report.pdf"):
        self.output_path = output_path
        os.makedirs(os.path.dirname(os.path.abspath(self.output_path)), exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """Sets up specific Paragraph styles for the report formatting."""
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            alignment=TA_CENTER,
            fontSize=16,
            spaceAfter=8
        ))
        self.styles.add(ParagraphStyle(
            name='CountryHeader',
            parent=self.styles['Heading1'],
            fontSize=14,
            textColor=colors.black,
            spaceBefore=24,
            spaceAfter=4,
            fontName="Helvetica-Bold"
        ))
        self.styles.add(ParagraphStyle(
            name='IssueHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceBefore=16,
            spaceAfter=8,
            fontName="Helvetica-Bold"
        ))
        self.styles.add(ParagraphStyle(
            name='PolicySubHeader',
            parent=self.styles['Normal'],
            fontName="Helvetica-Bold",
            spaceBefore=8,
            spaceAfter=4
        ))
        self.styles.add(ParagraphStyle(
            name='PolicyText',
            parent=self.styles['Normal'],
            spaceAfter=6,
            leading=14 # Line spacing
        ))

    def generate_from_file(self, json_file_path: str = "data/policies.json"):
        """Reads policies from JSON and builds the PDF."""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                policies = json.load(f)
            self.generate(policies)
        except Exception as e:
            logger.error(f"Failed to generate report from file: {e}")

    def generate(self, policies: List[Dict[str, Any]]):
        """Builds the PDF document using ReportLab."""
        doc = SimpleDocTemplate(
            self.output_path, 
            pagesize=letter,
            rightMargin=72, 
            leftMargin=72,
            topMargin=72, 
            bottomMargin=36
        )
        
        story = []
        
        # --- TITLE SECTION ---
        story.append(Paragraph("LABOUR MARKET POLICY DEVELOPMENTS", self.styles['ReportTitle']))
        story.append(Paragraph("PEER COUNTRIES", self.styles['ReportTitle']))
        story.append(Paragraph("2024–2026", self.styles['ReportTitle']))
        story.append(Spacer(1, 24))
        
        # --- GROUPING DATA ---
        # Group by Country, then by Issue
        grouped_data = {}
        for p in policies:
            # We skip policies that weren't verified successfully if we want strictly accurate reports, 
            # or we can just include them with a warning. Let's include everything for now.
            country = str(p.get("country", "Unknown")).upper()
            issue = p.get("labour_market_issue") or p.get("issue") or "Uncategorized"
            
            if country not in grouped_data:
                grouped_data[country] = {}
            if issue not in grouped_data[country]:
                grouped_data[country][issue] = []
            
            grouped_data[country][issue].append(p)
            
        # --- RENDER SECTIONS ---
        for country in sorted(grouped_data.keys()):
            # Country Heading
            story.append(Paragraph(country, self.styles['CountryHeader']))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=16))
            
            issues = grouped_data[country]
            for issue_idx, issue in enumerate(sorted(issues.keys()), 1):
                # Issue Subheading
                story.append(Paragraph(f"{issue_idx}. {issue}", self.styles['IssueHeader']))
                
                for p in issues[issue]:
                    # Policy Title
                    story.append(Paragraph("Policy:", self.styles['PolicySubHeader']))
                    story.append(Paragraph(p.get("policy_title", "N/A"), self.styles['PolicyText']))
                    
                    # Status
                    story.append(Paragraph("Status:", self.styles['PolicySubHeader']))
                    status_text = p.get("status", "N/A")
                    if p.get("effective_date") and p.get("effective_date") != "Unknown":
                        status_text += f" (Effective: {p.get('effective_date')})"
                    story.append(Paragraph(status_text, self.styles['PolicyText']))
                    
                    # Key Provisions (Bullets)
                    provisions = p.get("key_provisions", [])
                    if provisions:
                        story.append(Paragraph("Key provisions:", self.styles['PolicySubHeader']))
                        bullet_items = [ListItem(Paragraph(str(prov), self.styles['PolicyText'])) for prov in provisions]
                        story.append(ListFlowable(bullet_items, bulletType='bullet', spaceAfter=8))
                        
                    # Target Groups
                    t_groups = p.get("target_groups", [])
                    if t_groups:
                        story.append(Paragraph("Target groups:", self.styles['PolicySubHeader']))
                        story.append(Paragraph(", ".join(str(tg) for tg in t_groups), self.styles['PolicyText']))
                        
                    # Labour-market relevance
                    relevance = p.get("policy_objective", "")
                    if relevance:
                        story.append(Paragraph("Labour-market relevance:", self.styles['PolicySubHeader']))
                        story.append(Paragraph(relevance, self.styles['PolicyText']))
                        
                    # Sources (Enumerated)
                    sources = p.get("sources", [])
                    if sources:
                        story.append(Paragraph("Sources:", self.styles['PolicySubHeader']))
                        for src_idx, src in enumerate(sources, 1):
                            story.append(Paragraph(f"[{src_idx}] {src}", self.styles['PolicyText']))
                            
                    # Spacing between individual policies
                    story.append(Spacer(1, 16))
                    
        # Build the PDF
        try:
            doc.build(story)
            logger.info(f"Report successfully generated at {self.output_path}")
        except Exception as e:
            logger.error(f"Failed to build PDF report: {e}")
