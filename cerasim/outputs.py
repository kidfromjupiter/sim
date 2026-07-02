import os
from fpdf import FPDF
from cerasim.config import SCENARIOS

def generate_csv_report(df_comp):
    """Generate CSV bytes from the KPI DataFrame."""
    return df_comp.to_csv(index=False).encode('utf-8')

def generate_pdf_report(results_dict, df_comp, comp_path):
    """Generate a PDF report containing KPIs and charts."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Title Page
    pdf.add_page()
    pdf.set_font("helvetica", "B", 24)
    pdf.cell(0, 20, "SaniCer Supply Chain Simulator", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("helvetica", "I", 14)
    pdf.cell(0, 10, "Simulation Report", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(10)
    
    # KPIs Table
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Key Performance Indicators", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # Replace euro symbol for helvetica compatibility
    df_comp_pdf = df_comp.copy()
    for col in ["Revenue", "Net Profit"]:
        if col in df_comp_pdf.columns:
            df_comp_pdf[col] = df_comp_pdf[col].astype(str).str.replace("€", "EUR ")

    pdf.set_font("helvetica", "", 9)
    cols = df_comp_pdf.columns.tolist()
    col_widths = [25, 20, 20, 30, 20, 25, 25, 25] # Total 190
    
    for i, col in enumerate(cols):
        pdf.cell(col_widths[i], 10, str(col), border=1, align="C")
    pdf.ln()
    
    for index, row in df_comp_pdf.iterrows():
        for i, col in enumerate(cols):
            pdf.cell(col_widths[i], 10, str(row[col]), border=1, align="C")
        pdf.ln()
        
    # Scenario Comparison Chart
    if comp_path and os.path.exists(comp_path):
        pdf.add_page()
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "Scenario Comparison", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)
        pdf.image(comp_path, w=190)
        
    # Individual Dashboards
    for sid, (_, kpis, chart_path) in results_dict.items():
        if chart_path and os.path.exists(chart_path):
            pdf.add_page()
            pdf.set_font("helvetica", "B", 16)
            pdf.cell(0, 10, f"{SCENARIOS[sid]['label']} Dashboard", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", "I", 12)
            pdf.cell(0, 10, SCENARIOS[sid]['description'], new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            pdf.image(chart_path, w=190)
            
    return bytes(pdf.output())
