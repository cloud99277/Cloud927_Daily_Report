#!/usr/bin/env python3
"""
China Content Compliance Filter - Python Implementation
Automated compliance filtering for Cloud927 Daily Report

Usage:
    python src/compliance_filter.py data/2026-02-08_raw.md
    python src/compliance_filter.py data/2026-02-08_raw.md --output-dir data/
"""

import re
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ComplianceFilter:
    """China Content Compliance Filter"""

    def __init__(self, keywords_path: str = ".claude/skills/china-content-compliance/keywords.yaml"):
        """Initialize filter with keyword database"""
        self.keywords_path = Path(keywords_path)
        self.keywords = self._load_keywords()
        self.modifications = {
            'red_deletions': [],
            'orange_rewrites': [],
            'yellow_annotations': []
        }

    def _load_keywords(self) -> Dict:
        """Load keyword database from YAML"""
        try:
            with open(self.keywords_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load keywords: {e}")
            return {}

    # ==================== RED RULES ====================

    def _check_r01_crypto(self, text: str) -> List[str]:
        """R-01: Check cryptocurrency content"""
        matches = []
        crypto_keywords = self.keywords.get('crypto_keywords', [])
        
        for keyword in crypto_keywords:
            if re.search(keyword, text, re.IGNORECASE):
                matches.append(f"[R-01] Crypto keyword detected: {keyword}")
        
        return matches

    def _check_r02_brand_defamation(self, text: str) -> List[str]:
        """R-02: Check domestic brand defamation"""
        matches = []
        brands = self.keywords.get('brands', {})
        negative_terms = self.keywords.get('negative_terms', [])
        
        all_brands = []
        for category in brands.values():
            all_brands.extend(category)
        
        for brand in all_brands:
            for negative in negative_terms:
                pattern = f"{brand}.*{negative}|{negative}.*{brand}"
                if re.search(pattern, text, re.IGNORECASE):
                    matches.append(f"[R-02] Brand defamation: {brand} + {negative}")
        
        return matches

    def _check_r04_investment_advice(self, text: str) -> List[str]:
        """R-04: Check illegal investment advice"""
        matches = []
        investment_keywords = self.keywords.get('investment_keywords', [])
        
        for keyword in investment_keywords:
            if re.search(keyword, text, re.IGNORECASE):
                matches.append(f"[R-04] Investment advice detected: {keyword}")
        
        return matches

    def _check_r05_vpn(self, text: str) -> List[str]:
        """R-05: Check VPN/network security content"""
        matches = []
        vpn_keywords = self.keywords.get('vpn_keywords', [])
        
        for keyword in vpn_keywords:
            if re.search(keyword, text, re.IGNORECASE):
                matches.append(f"[R-05] VPN keyword detected: {keyword}")
        
        return matches

    def _check_r06_hikvision(self, text: str) -> Tuple[List[str], bool]:
        """R-06: Check Hikvision employee compliance (returns matches and kill_switch)"""
        matches = []
        kill_switch = False
        
        # Check DLP keywords
        dlp_keywords = self.keywords.get('hikvision_dlp', [])
        for keyword in dlp_keywords:
            if re.search(keyword, text, re.IGNORECASE):
                matches.append(f"[R-06-HIGH] DLP violation: {keyword}")
        
        # Check sanction keywords
        sanction_keywords = self.keywords.get('hikvision_sanction', [])
        for keyword in sanction_keywords:
            if re.search(keyword, text, re.IGNORECASE):
                matches.append(f"[R-06-HIGH] Sanction topic: {keyword}")
        
        # Check Kill Switch (Xinjiang)
        if re.search(r'新疆|xinjiang', text, re.IGNORECASE):
            kill_switch = True
            matches.append(f"[R-06-CRITICAL] Kill Switch triggered: Xinjiang content")
        
        return matches, kill_switch

    def _check_r07_minor_protection(self, text: str) -> List[str]:
        """R-07: Check minor protection rules"""
        matches = []
        
        violence_keywords = self.keywords.get('violence_keywords', [])
        horror_keywords = self.keywords.get('horror_keywords', [])
        gambling_drugs = self.keywords.get('gambling_drugs', [])
        
        for keyword in violence_keywords:
            if re.search(keyword, text, re.IGNORECASE):
                matches.append(f"[R-07] Violence content: {keyword}")
        
        for keyword in horror_keywords:
            if re.search(keyword, text, re.IGNORECASE):
                matches.append(f"[R-07] Horror content: {keyword}")
        
        for keyword in gambling_drugs:
            if re.search(keyword, text, re.IGNORECASE):
                matches.append(f"[R-07] Gambling/drugs: {keyword}")
        
        return matches

    def apply_red_rules(self, content: str) -> Tuple[str, bool]:
        """Apply all Red Rules and return filtered content and kill_switch status"""
        lines = content.split('\n')
        filtered_lines = []
        kill_switch = False
        
        for line in lines:
            should_delete = False
            
            # Check all Red Rules
            if self._check_r01_crypto(line):
                self.modifications['red_deletions'].append(f"Line deleted (R-01): {line[:50]}...")
                should_delete = True
            
            if self._check_r02_brand_defamation(line):
                self.modifications['red_deletions'].append(f"Line deleted (R-02): {line[:50]}...")
                should_delete = True
            
            if self._check_r04_investment_advice(line):
                self.modifications['red_deletions'].append(f"Line deleted (R-04): {line[:50]}...")
                should_delete = True
            
            if self._check_r05_vpn(line):
                self.modifications['red_deletions'].append(f"Line deleted (R-05): {line[:50]}...")
                should_delete = True
            
            r06_matches, r06_kill = self._check_r06_hikvision(line)
            if r06_matches:
                self.modifications['red_deletions'].extend(r06_matches)
                should_delete = True
            if r06_kill:
                kill_switch = True
            
            if self._check_r07_minor_protection(line):
                self.modifications['red_deletions'].append(f"Line deleted (R-07): {line[:50]}...")
                should_delete = True
            
            if not should_delete:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines), kill_switch

    # ==================== ORANGE RULES ====================

    def apply_orange_rules(self, content: str) -> str:
        """Apply Orange Rules (soft rewrites)"""
        
        # O-01: De-financialization
        replacements = {
            r'债市反弹': '债券市场波动',
            r'信用市场承压': '信用市场出现调整',
            r'投资者抄底': '市场参与者关注',
            r'资金流入': '资本配置变化',
            r'科技AI投资引发': '科技巨头加大 AI 基础设施',
        }
        
        for pattern, replacement in replacements.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                self.modifications['orange_rewrites'].append(f"[O-01] Rewritten: {pattern} → {replacement}")
        
        # O-03: Macro neutrality
        neutrality_replacements = {
            r'崩盘': '大幅调整',
            r'危机': '挑战',
            r'萧条': '周期性放缓',
            r'暴跌': '显著下跌',
            r'冲击': '影响',
            r'双重冲击': '发布在即',
        }
        
        for pattern, replacement in neutrality_replacements.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                self.modifications['orange_rewrites'].append(f"[O-03] Neutralized: {pattern} → {replacement}")
        
        return content

    # ==================== YELLOW RULES ====================

    def apply_yellow_rules(self, content: str, report_date: str) -> str:
        """Apply Yellow Rules (annotations)"""
        
        # Y-01: Add AI metadata in YAML frontmatter
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")
        content_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        yaml_frontmatter = f"""---
date: {report_date}
type: daily_report
source: Cloud927
tags:
  - #daily_report
  - #cloud927
  - #AI
  - #finance
ai_generated: true
compliance_version: public
ai_metadata:
  provider: Cloud927
  provider_code: CLD927
  model: Claude-Sonnet-4.5 + Gemini-2.0-Flash
  content_id: {content_id}
  generation_timestamp: {timestamp}
  content_type: text/markdown
  standard: GB45438-2025
---

"""
        
        # Y-02: Add disclaimer
        disclaimer = "> **免责声明**: 本报告内容来源于公开信息，仅供学习交流，不构成任何投资建议。投资有风险，决策需谨慎。\n\n"
        
        # Y-01 (explicit): Add AI generation statement at end
        ai_statement = "\n\n> **AI 生成声明**: 本报告由 AI 辅助生成，内容仅供参考，不构成投资建议。\n"
        
        # Combine all
        content = yaml_frontmatter + disclaimer + content + ai_statement
        
        self.modifications['yellow_annotations'].append("[Y-01] Added: AI metadata (explicit+implicit)")
        self.modifications['yellow_annotations'].append("[Y-02] Added: Disclaimer")
        
        return content

    def generate_compliance_report(self, report_date: str, original_length: int, filtered_length: int) -> str:
        """Generate detailed compliance report"""
        
        report = f"""# 合规报告 - {report_date}

## 修改统计
- 🔴 硬性阻断：{len(self.modifications['red_deletions'])} 条删除
- 🟠 软性重写：{len(self.modifications['orange_rewrites'])} 条改写
- 🟡 标注声明：{len(self.modifications['yellow_annotations'])} 条添加

---

## 详细修改记录

### 🔴 硬性阻断 (Red Rules)

"""
        
        for deletion in self.modifications['red_deletions']:
            report += f"- {deletion}\n"
        
        report += "\n### 🟠 软性重写 (Orange Rules)\n\n"
        
        for rewrite in self.modifications['orange_rewrites']:
            report += f"- {rewrite}\n"
        
        report += "\n### 🟡 标注声明 (Yellow Rules)\n\n"
        
        for annotation in self.modifications['yellow_annotations']:
            report += f"- {annotation}\n"
        
        deletion_rate = ((original_length - filtered_length) / original_length * 100) if original_length > 0 else 0
        
        report += f"""

---

## 过滤效果
- 原始内容：约 {original_length} 字
- 公开版内容：约 {filtered_length} 字
- 删除率：{deletion_rate:.1f}%

---

*合规报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
*合规版本: v2.0*
*处理引擎: China Content Compliance Filter*
"""
        
        return report

    def filter_content(self, content: str, report_date: str) -> Tuple[str, str, bool]:
        """Main filtering pipeline
        
        Returns:
            (filtered_content, compliance_report, kill_switch)
        """
        original_length = len(content)
        
        logger.info("Step 1: Applying Red Rules (Hard Block)")
        filtered_content, kill_switch = self.apply_red_rules(content)
        
        if kill_switch:
            logger.critical("Kill Switch triggered! Entire report blocked from publishing.")
            return "", "Kill Switch triggered - entire report blocked", True
        
        logger.info("Step 2: Applying Orange Rules (Soft Rewrite)")
        filtered_content = self.apply_orange_rules(filtered_content)
        
        logger.info("Step 3: Applying Yellow Rules (Annotations)")
        filtered_content = self.apply_yellow_rules(filtered_content, report_date)
        
        filtered_length = len(filtered_content)
        
        logger.info("Step 4: Generating Compliance Report")
        compliance_report = self.generate_compliance_report(
            report_date, original_length, filtered_length
        )
        
        return filtered_content, compliance_report, False


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='China Content Compliance Filter for Cloud927 Daily Report'
    )
    parser.add_argument(
        'input_file',
        type=str,
        help='Path to input markdown file (e.g., data/2026-02-08_raw.md)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/',
        help='Output directory for filtered files (default: data/)'
    )
    parser.add_argument(
        '--keywords',
        type=str,
        default='.claude/skills/china-content-compliance/keywords.yaml',
        help='Path to keywords YAML file'
    )
    
    args = parser.parse_args()
    
    # Read input file
    input_path = Path(args.input_file)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 1
    
    logger.info(f"Reading input file: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract date from filename (e.g., 2026-02-08_raw.md -> 2026-02-08)
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', input_path.name)
    report_date = date_match.group(1) if date_match else datetime.now().strftime("%Y-%m-%d")
    
    # Initialize filter and process
    logger.info("Initializing compliance filter")
    filter_obj = ComplianceFilter(keywords_path=args.keywords)
    
    filtered_content, compliance_report, kill_switch = filter_obj.filter_content(
        content, report_date
    )
    
    if kill_switch:
        logger.critical("Kill Switch triggered! No files will be saved.")
        print("\n⚠️  CRITICAL: Kill Switch triggered!")
        print("Entire report blocked from publishing due to critical violation.")
        return 2
    
    # Save output files
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    public_file = output_dir / f"{report_date}_public.md"
    report_file = output_dir / f"{report_date}_compliance_report.md"
    
    logger.info(f"Saving public version: {public_file}")
    with open(public_file, 'w', encoding='utf-8') as f:
        f.write(filtered_content)
    
    logger.info(f"Saving compliance report: {report_file}")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(compliance_report)
    
    print(f"\n✅ Compliance filtering completed!")
    print(f"📄 Public version: {public_file}")
    print(f"📋 Compliance report: {report_file}")
    print(f"\n📊 Statistics:")
    print(f"   - Red deletions: {len(filter_obj.modifications['red_deletions'])}")
    print(f"   - Orange rewrites: {len(filter_obj.modifications['orange_rewrites'])}")
    print(f"   - Yellow annotations: {len(filter_obj.modifications['yellow_annotations'])}")
    
    return 0


if __name__ == '__main__':
    exit(main())
