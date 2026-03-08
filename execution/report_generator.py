import csv
import json
import io

def export_csv(videos: list) -> str:
    if not videos:
        return ""
    
    output = io.StringIO()
    # Add BOM for Excel Arabic support
    output.write('\ufeff')
    
    writer = csv.DictWriter(output, fieldnames=videos[0].keys())
    writer.writeheader()
    for row in videos:
        writer.writerow(row)
        
    return output.getvalue()

def export_json(videos: list) -> str:
    return json.dumps(videos, ensure_ascii=False, indent=2)

def export_markdown(videos: list, title="Research Report") -> str:
    if not videos:
        return f"# {title}\n\nNo videos found."
        
    md = f"# {title}\n\n"
    md += f"**Total Videos:** {len(videos)}\n\n"
    
    avg_rate = sum(v.get('rate', 0) for v in videos) / len(videos) if videos else 0
    md += f"**Average Score:** {avg_rate:.2f}\n\n"
    
    md += "## Videos\n\n"
    
    for v in videos:
        md += f"### [{v.get('title', 'Unknown Title')}]({v.get('link', '#')})\n"
        md += f"- **Score:** {v.get('rate', 0)} ({v.get('label', '')})\n"
        md += f"- **Duration:** {v.get('duration', '')}\n"
        md += f"- **Sentiment:** {v.get('sentiment', '')}\n"
        md += f"- **Views:** {v.get('views', 0)}\n"
        md += f"- **Topics:** {v.get('topics', '')}\n\n"
        
        md += "**AI Summary:**\n"
        md += f"{v.get('summary', 'No summary')}\n\n"
        
        md += "**Notes & Strategy:**\n"
        md += f"{v.get('notes', 'No notes')}\n\n"
        
        if v.get('hook'): md += f"- **Hook:** {v.get('hook')}\n"
        if v.get('cta'): md += f"- **CTA:** {v.get('cta')}\n"
        if v.get('target_audience'): md += f"- **Target Audience:** {v.get('target_audience')}\n"
        if v.get('content_gap'): md += f"- **Content Gap:** {v.get('content_gap')}\n"
        
        md += "---\n\n"
        
    return md
