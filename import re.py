import re
import json
import ast
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, Counter
import pandas as pd
from typing import Dict, List, Tuple

class QwenFrontendAnalyzer:
    def __init__(self, response_text: str):
        """
        Initialize the analyzer with the model's response text
        """
        self.response = response_text
        self.analysis_results = {}
        self.code_blocks = []
        self.files_detected = {}
        
    def extract_code_blocks(self) -> Dict:
        """
        Extract all code blocks and file structures from the response
        """
        # Pattern to match code blocks with language specification
        code_block_pattern = r'```(\w+)?\n(.*?)\n```'
        matches = re.findall(code_block_pattern, self.response, re.DOTALL)
        
        # Pattern to match file names/paths
        file_pattern = r'(?:// |# |<!-- )?([\w/.-]+\.(jsx?|css|json|md))'
        
        code_blocks = []
        for i, (lang, code) in enumerate(matches):
            # Try to extract filename from code content
            filename = None
            first_lines = code.strip().split('\n')[:3]
            for line in first_lines:
                file_match = re.search(file_pattern, line)
                if file_match:
                    filename = file_match.group(1)
                    break
            
            # If no filename found, try to infer from context
            if not filename:
                if 'import React' in code or 'export default' in code:
                    filename = f'Component_{i}.jsx'
                elif 'module.exports' in code or 'export {' in code:
                    filename = f'Module_{i}.js'
                elif '@tailwind' in code or 'body {' in code:
                    filename = f'Style_{i}.css'
                else:
                    filename = f'Unknown_{i}.{lang or "txt"}'
            
            code_blocks.append({
                'filename': filename,
                'language': lang or 'unknown',
                'code': code.strip(),
                'line_count': len(code.strip().split('\n')),
                'char_count': len(code.strip())
            })
        
        self.code_blocks = code_blocks
        return code_blocks
    
    def analyze_react_patterns(self) -> Dict:
        """
        Analyze React patterns and modern practices used
        """
        react_analysis = {
            'components_found': 0,
            'functional_components': 0,
            'class_components': 0,
            'hooks_used': [],
            'imports_analysis': {},
            'modern_patterns': [],
            'potential_issues': []
        }
        
        hooks_pattern = r'use([A-Z]\w+)'
        import_pattern = r'import\s+(?:{([^}]+)}|\*\s+as\s+\w+|\w+)\s+from\s+[\'"]([^\'"]+)[\'"]'
        
        for block in self.code_blocks:
            if block['language'] in ['jsx', 'js', 'javascript']:
                code = block['code']
                
                # Count components
                if 'export default' in code and ('function' in code or 'const' in code):
                    react_analysis['components_found'] += 1
                    
                    if 'function' in code or 'const' in code and '=>' in code:
                        react_analysis['functional_components'] += 1
                    elif 'class' in code and 'extends' in code:
                        react_analysis['class_components'] += 1
                
                # Find hooks
                hooks = re.findall(hooks_pattern, code)
                react_analysis['hooks_used'].extend(hooks)
                
                # Analyze imports
                imports = re.findall(import_pattern, code)
                for import_items, module in imports:
                    if module not in react_analysis['imports_analysis']:
                        react_analysis['imports_analysis'][module] = []
                    if import_items:
                        react_analysis['imports_analysis'][module].extend(
                            [item.strip() for item in import_items.split(',')]
                        )
                
                # Check for modern patterns
                if 'useState' in code:
                    react_analysis['modern_patterns'].append('State Hooks')
                if 'useEffect' in code:
                    react_analysis['modern_patterns'].append('Effect Hooks')
                if 'useContext' in code:
                    react_analysis['modern_patterns'].append('Context API')
                if 'React.memo' in code:
                    react_analysis['modern_patterns'].append('Memoization')
                if 'useCallback' in code or 'useMemo' in code:
                    react_analysis['modern_patterns'].append('Performance Optimization')
                
                # Check for potential issues
                if 'dangerouslySetInnerHTML' in code:
                    react_analysis['potential_issues'].append('XSS Risk: dangerouslySetInnerHTML used')
                if re.search(r'onClick=.*{.*}', code) and 'useCallback' not in code:
                    react_analysis['potential_issues'].append('Performance: Inline functions in JSX')
                if 'key=' not in code and '.map(' in code:
                    react_analysis['potential_issues'].append('Missing keys in mapped elements')
        
        # Clean up duplicates
        react_analysis['hooks_used'] = list(set(react_analysis['hooks_used']))
        react_analysis['modern_patterns'] = list(set(react_analysis['modern_patterns']))
        
        return react_analysis
    
    def analyze_design_system_compliance(self) -> Dict:
        """
        Check compliance with the specified design system
        """
        design_analysis = {
            'colors_used': [],
            'tailwind_classes': [],
            'responsive_design': False,
            'typography_compliance': False,
            'spacing_system': False,
            'design_score': 0
        }
        
        # Expected colors from the prompt
        expected_colors = [
            '2563eb', 'blue-600',  # Primary
            '7c3aed', 'violet-600',  # Secondary  
            '059669', 'emerald-600',  # Tertiary
            '1f2937', 'gray-800',  # Neutral
            'f9fafb', 'gray-50'
        ]
        
        # Tailwind responsive prefixes
        responsive_prefixes = ['sm:', 'md:', 'lg:', 'xl:', '2xl:']
        
        all_code = ' '.join([block['code'] for block in self.code_blocks])
        
        # Check for color usage
        for color in expected_colors:
            if color in all_code:
                design_analysis['colors_used'].append(color)
        
        # Extract Tailwind classes
        tailwind_pattern = r'className=["\']([^"\']+)["\']'
        classes = re.findall(tailwind_pattern, all_code)
        all_classes = ' '.join(classes)
        design_analysis['tailwind_classes'] = all_classes.split()
        
        # Check responsive design
        for prefix in responsive_prefixes:
            if prefix in all_code:
                design_analysis['responsive_design'] = True
                break
        
        # Check typography classes
        typography_patterns = ['text-', 'font-', 'leading-', 'tracking-']
        for pattern in typography_patterns:
            if pattern in all_code:
                design_analysis['typography_compliance'] = True
                break
        
        # Check spacing system
        spacing_patterns = ['p-', 'm-', 'space-', 'gap-']
        for pattern in spacing_patterns:
            if pattern in all_code:
                design_analysis['spacing_system'] = True
                break
        
        # Calculate design score
        score = 0
        if len(design_analysis['colors_used']) >= 3:
            score += 25
        if design_analysis['responsive_design']:
            score += 25
        if design_analysis['typography_compliance']:
            score += 25
        if design_analysis['spacing_system']:
            score += 25
        
        design_analysis['design_score'] = score
        
        return design_analysis
    
    def analyze_project_structure(self) -> Dict:
        """
        Analyze if the generated code follows the requested project structure
        """
        structure_analysis = {
            'total_files': len(self.code_blocks),
            'file_types': Counter([block['language'] for block in self.code_blocks]),
            'expected_files': [],
            'missing_files': [],
            'structure_score': 0
        }
        
        # Expected files from the prompt
        expected_structure = [
            'Header.jsx', 'Footer.jsx', 'Navigation.jsx',
            'Button.jsx', 'Input.jsx', 'Badge.jsx',
            'ProductCard.jsx', 'ProductGrid.jsx',
            'HomePage.jsx', 'ProductListPage.jsx',
            'App.jsx', 'index.js'
        ]
        
        generated_files = [block['filename'] for block in self.code_blocks]
        
        for expected in expected_structure:
            found = any(expected.lower() in f.lower() for f in generated_files)
            if found:
                structure_analysis['expected_files'].append(expected)
            else:
                structure_analysis['missing_files'].append(expected)
        
        # Calculate structure score
        structure_score = (len(structure_analysis['expected_files']) / len(expected_structure)) * 100
        structure_analysis['structure_score'] = round(structure_score, 1)
        
        return structure_analysis
    
    def analyze_functionality(self) -> Dict:
        """
        Analyze functional completeness based on requirements
        """
        functionality_analysis = {
            'ecommerce_features': [],
            'navigation_implemented': False,
            'cart_functionality': False,
            'search_functionality': False,
            'responsive_features': False,
            'functionality_score': 0
        }
        
        all_code = ' '.join([block['code'] for block in self.code_blocks])
        
        # Check for e-commerce features
        ecommerce_keywords = {
            'cart': ['cart', 'addToCart', 'removeFromCart', 'updateCart'],
            'product': ['product', 'ProductCard', 'ProductGrid'],
            'search': ['search', 'filter', 'SearchBar'],
            'navigation': ['nav', 'Navigation', 'Header'],
            'checkout': ['checkout', 'order', 'purchase']
        }
        
        for feature, keywords in ecommerce_keywords.items():
            if any(keyword.lower() in all_code.lower() for keyword in keywords):
                functionality_analysis['ecommerce_features'].append(feature)
        
        # Specific checks
        functionality_analysis['navigation_implemented'] = 'navigation' in functionality_analysis['ecommerce_features']
        functionality_analysis['cart_functionality'] = 'cart' in functionality_analysis['ecommerce_features']
        functionality_analysis['search_functionality'] = 'search' in functionality_analysis['ecommerce_features']
        
        # Check for responsive features
        responsive_indicators = ['mobile', 'tablet', 'desktop', 'sm:', 'md:', 'lg:']
        functionality_analysis['responsive_features'] = any(
            indicator in all_code.lower() for indicator in responsive_indicators
        )
        
        # Calculate functionality score
        score = 0
        score += len(functionality_analysis['ecommerce_features']) * 15
        score += 20 if functionality_analysis['responsive_features'] else 0
        score = min(score, 100)  # Cap at 100
        
        functionality_analysis['functionality_score'] = score
        
        return functionality_analysis
    
    def generate_comprehensive_report(self) -> Dict:
        """
        Generate a comprehensive analysis report
        """
        print("🔍 Analyzing Qwen Frontend Generation Response...")
        print("=" * 60)
        
        # Extract code blocks
        code_blocks = self.extract_code_blocks()
        print(f"📁 Code Blocks Extracted: {len(code_blocks)}")
        
        # Run all analyses
        react_analysis = self.analyze_react_patterns()
        design_analysis = self.analyze_design_system_compliance()
        structure_analysis = self.analyze_project_structure()
        functionality_analysis = self.analyze_functionality()
        
        # Calculate overall score
        overall_score = (
            (structure_analysis['structure_score'] * 0.3) +
            (design_analysis['design_score'] * 0.25) +
            (functionality_analysis['functionality_score'] * 0.25) +
            (min(react_analysis['components_found'] * 10, 50) * 0.2)
        )
        
        report = {
            'overall_score': round(overall_score, 1),
            'code_blocks': code_blocks,
            'react_analysis': react_analysis,
            'design_analysis': design_analysis,
            'structure_analysis': structure_analysis,
            'functionality_analysis': functionality_analysis,
            'metadata': {
                'total_lines': sum(block['line_count'] for block in code_blocks),
                'total_chars': sum(block['char_count'] for block in code_blocks),
                'response_length': len(self.response)
            }
        }
        
        return report
    
    def print_detailed_report(self, report: Dict):
        """
        Print a formatted detailed report
        """
        print("\n🎯 QWEN FRONTEND GENERATION ANALYSIS REPORT")
        print("=" * 60)
        
        # Overall Score
        score = report['overall_score']
        score_color = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
        print(f"\n{score_color} OVERALL SCORE: {score}/100")
        
        if score >= 90:
            grade = "Exceptional (A+)"
        elif score >= 80:
            grade = "Excellent (A)"
        elif score >= 70:
            grade = "Good (B)"
        elif score >= 60:
            grade = "Fair (C)"
        else:
            grade = "Poor (D)"
        
        print(f"📊 Grade: {grade}")
        
        # Metadata
        meta = report['metadata']
        print(f"\n📈 CODE STATISTICS:")
        print(f"   • Total Files Generated: {len(report['code_blocks'])}")
        print(f"   • Total Lines of Code: {meta['total_lines']:,}")
        print(f"   • Total Characters: {meta['total_chars']:,}")
        print(f"   • Response Length: {meta['response_length']:,} chars")
        
        # React Analysis
        react = report['react_analysis']
        print(f"\n⚛️ REACT ANALYSIS:")
        print(f"   • Components Found: {react['components_found']}")
        print(f"   • Functional Components: {react['functional_components']}")
        print(f"   • Hooks Used: {', '.join(react['hooks_used']) or 'None'}")
        print(f"   • Modern Patterns: {', '.join(react['modern_patterns']) or 'None'}")
        if react['potential_issues']:
            print(f"   • ⚠️ Issues: {'; '.join(react['potential_issues'])}")
        
        # Design Analysis
        design = report['design_analysis']
        print(f"\n🎨 DESIGN SYSTEM COMPLIANCE:")
        print(f"   • Design Score: {design['design_score']}/100")
        print(f"   • Colors Used: {', '.join(design['colors_used']) or 'None detected'}")
        print(f"   • Responsive Design: {'✅' if design['responsive_design'] else '❌'}")
        print(f"   • Typography System: {'✅' if design['typography_compliance'] else '❌'}")
        print(f"   • Spacing System: {'✅' if design['spacing_system'] else '❌'}")
        
        # Structure Analysis  
        structure = report['structure_analysis']
        print(f"\n📁 PROJECT STRUCTURE:")
        print(f"   • Structure Score: {structure['structure_score']}/100")
        print(f"   • Expected Files Found: {len(structure['expected_files'])}")
        print(f"   • Missing Files: {len(structure['missing_files'])}")
        if structure['missing_files']:
            print(f"   • Missing: {', '.join(structure['missing_files'][:5])}{'...' if len(structure['missing_files']) > 5 else ''}")
        
        # Functionality Analysis
        func = report['functionality_analysis']
        print(f"\n🛍️ FUNCTIONALITY ANALYSIS:")
        print(f"   • Functionality Score: {func['functionality_score']}/100")
        print(f"   • E-commerce Features: {', '.join(func['ecommerce_features']) or 'None'}")
        print(f"   • Navigation: {'✅' if func['navigation_implemented'] else '❌'}")
        print(f"   • Cart System: {'✅' if func['cart_functionality'] else '❌'}")
        print(f"   • Search: {'✅' if func['search_functionality'] else '❌'}")
        
        # File Details
        print(f"\n📋 GENERATED FILES:")
        for i, block in enumerate(report['code_blocks'][:10], 1):  # Show first 10 files
            print(f"   {i}. {block['filename']} ({block['language']}) - {block['line_count']} lines")
        
        if len(report['code_blocks']) > 10:
            print(f"   ... and {len(report['code_blocks']) - 10} more files")
        
        print("\n" + "=" * 60)
        print("Analysis complete! 🎉")
        
        return report

# Usage function
def analyze_qwen_response(response_text: str):
    """
    Main function to analyze the Qwen model response
    Usage: analyze_qwen_response(response)
    """
    analyzer = QwenFrontendAnalyzer(response_text)
    report = analyzer.generate_comprehensive_report()
    detailed_report = analyzer.print_detailed_report(report)
    
    return report

# Additional visualization function
def create_analysis_charts(report: Dict):
    """
    Create visualization charts for the analysis
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Overall scores
    categories = ['Structure', 'Design', 'Functionality', 'React Quality']
    scores = [
        report['structure_analysis']['structure_score'],
        report['design_analysis']['design_score'],
        report['functionality_analysis']['functionality_score'],
        min(report['react_analysis']['components_found'] * 10, 100)
    ]
    
    ax1.bar(categories, scores, color=['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b'])
    ax1.set_title('Category Scores')
    ax1.set_ylabel('Score')
    ax1.set_ylim(0, 100)
    
    # File types distribution
    file_types = report['structure_analysis']['file_types']
    ax2.pie(file_types.values(), labels=file_types.keys(), autopct='%1.1f%%')
    ax2.set_title('File Types Distribution')
    
    # Features implemented
    features = report['functionality_analysis']['ecommerce_features']
    feature_counts = Counter(features)
    if feature_counts:
        ax3.bar(feature_counts.keys(), feature_counts.values(), color='#059669')
        ax3.set_title('E-commerce Features Implemented')
        ax3.tick_params(axis='x', rotation=45)
    
    # Code volume by file
    files = report['code_blocks'][:10]  # Top 10 files
    file_names = [f['filename'][:20] + '...' if len(f['filename']) > 20 else f['filename'] for f in files]
    line_counts = [f['line_count'] for f in files]
    
    ax4.barh(file_names, line_counts, color='#dc2626')
    ax4.set_title('Lines of Code by File (Top 10)')
    ax4.set_xlabel('Lines of Code')
    
    plt.tight_layout()
    plt.show()

# Quick test function
def quick_test(response_text: str):
    """
    Quick test function for immediate feedback
    """
    print("🚀 Quick Analysis of Qwen Response...")
    
    # Basic stats
    code_blocks = len(re.findall(r'```[\w]*\n.*?\n```', response_text, re.DOTALL))
    react_components = len(re.findall(r'export default|function \w+\(|const \w+ = \(', response_text))
    jsx_usage = 'jsx' in response_text.lower() or '<' in response_text and '>' in response_text
    
    print(f"📊 Code blocks found: {code_blocks}")
    print(f"⚛️ React components detected: {react_components}")
    print(f"🏷️ JSX syntax present: {'Yes' if jsx_usage else 'No'}")
    print(f"📏 Response length: {len(response_text):,} characters")
    
    # Quick quality indicators
    quality_indicators = 0
    if 'useState' in response_text: quality_indicators += 1
    if 'useEffect' in response_text: quality_indicators += 1
    if 'className' in response_text: quality_indicators += 1
    if 'export default' in response_text: quality_indicators += 1
    if 'import' in response_text: quality_indicators += 1
    
    print(f"✅ Quality indicators: {quality_indicators}/5")
    
    if quality_indicators >= 4:
        print("🟢 Looks promising! Run full analysis.")
    elif quality_indicators >= 2:
        print("🟡 Mixed results. Full analysis recommended.")
    else:
        print("🔴 Potential issues detected. Check full analysis.")

print("✅ Qwen Frontend Analyzer loaded!")
print("📝 Usage:")
print("   quick_test(response)           # Quick overview")
print("   report = analyze_qwen_response(response)  # Full analysis") 
print("   create_analysis_charts(report) # Visualizations")