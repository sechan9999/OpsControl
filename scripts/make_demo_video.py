from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "opscontrol-demo"
OUT.mkdir(parents=True, exist_ok=True)
W, H = 1920, 1080
BG = "#081018"
PANEL = "#111c26"
PANEL_2 = "#152332"
TEXT = "#f8fafc"
MUTED = "#9fb2c8"
AMBER = "#f59e0b"
RED = "#ef4444"
GREEN = "#22c55e"
BLUE = "#38bdf8"

font = Path("C:/Windows/Fonts/segoeui.ttf")
bold = Path("C:/Windows/Fonts/segoeuib.ttf")
def f(size, is_bold=False):
    return ImageFont.truetype(str(bold if is_bold else font), size)

def text(draw, xy, value, size=28, color=TEXT, bold_text=False, anchor=None):
    draw.text(xy, value, font=f(size, bold_text), fill=color, anchor=anchor)

def rounded(draw, box, fill, radius=20, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def header(draw, section, title, subtitle):
    text(draw, (92, 76), "OPSCONTROL", 28, AMBER, True)
    text(draw, (92, 126), section.upper(), 20, MUTED, True)
    text(draw, (92, 176), title, 56, TEXT, True)
    text(draw, (92, 246), subtitle, 26, MUTED)
    draw.line((92, 300, 1828, 300), fill="#223344", width=2)

def metric(draw, x, y, label, value, color=TEXT):
    rounded(draw, (x, y, x+255, y+122), PANEL)
    text(draw, (x+22, y+25), label.upper(), 16, MUTED, True)
    text(draw, (x+22, y+62), value, 38, color, True)

def footer(draw, number):
    text(draw, (92, 1030), "OpsControl | Human-in-the-loop operations exception desk", 18, MUTED)
    text(draw, (1828, 1030), f"{number}/6", 18, MUTED, anchor="ra")

def slide_one():
    im = Image.new("RGB", (W,H), BG); d=ImageDraw.Draw(im)
    header(d, "The incident", "A disruption should create a queue, not chaos.", "Carrier updates, broker emails, and driver alerts arrive all at once.")
    for i,(label,value,color) in enumerate([("Incoming updates", "32", AMBER),("Duplicate deliveries", "3", RED),("High-risk shipment", "1", RED)]):
        metric(d, 140+i*355, 390, label, value, color)
    rounded(d, (120,590,1800,890), PANEL)
    text(d, (160,640), "Port of Savannah weather event", 34, TEXT, True)
    text(d, (160,705), "Held containers. Missed delivery windows. Customer updates waiting.", 28, MUTED)
    text(d, (160,790), "OpsControl organizes the first pass so operators can focus on the decisions that need judgment.", 26, BLUE)
    footer(d,1); return im

def slide_two():
    im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
    header(d,"Ingest", "32 messages enter one controlled workflow.", "Normalized-message idempotency removes repeat work before triage begins.")
    steps=[("Raw updates", "EDI, email, SMS"),("Normalize", "Whitespace and case"),("Deduplicate", "SHA-256 key"),("Triage", "Structured exception")]
    for i,(a,b) in enumerate(steps):
        x=120+i*430; rounded(d,(x,410,x+330,650),PANEL_2); text(d,(x+28,462),str(i+1),22,AMBER,True); text(d,(x+28,512),a,30,TEXT,True); text(d,(x+28,566),b,21,MUTED)
        if i<3: text(d,(x+365,535),">",42,AMBER,True)
    metric(d,270,760,"Unique records","29",GREEN); metric(d,620,760,"Duplicates dropped","3",AMBER); metric(d,970,760,"Silent failures","0",GREEN)
    footer(d,2); return im

def slide_three():
    im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
    header(d,"Prioritize", "The inbox surfaces the consequence, not just the message.", "The replay creates a stable risk-ranked queue for the operator.")
    for i,(lab,val,col) in enumerate([("Ingested","29",TEXT),("Ready for approval","12",GREEN),("Human review","2",AMBER),("Value at risk","$25,000",RED)]): metric(d,95+i*330,350,lab,val,col)
    rounded(d,(95,530,1825,925),PANEL)
    text(d,(135,575),"INBOX",20,MUTED,True)
    rows=[("RED","OPS-40045-A","REEFER_TEMP","Missed delivery window | $25,000 at risk",RED),("ORANGE","OPS-40021-A","PORT_DELAY","Savannah weather delay | customer update drafted",AMBER),("GREEN","OPS-40031-C","CUSTOMS_HOLD","Documentation review | monitor",GREEN)]
    for idx,(tier,ref,kind,impact,col) in enumerate(rows):
        y=635+idx*86; rounded(d,(130,y,1790,y+66),PANEL_2,12); text(d,(154,y+20),tier,16,col,True); text(d,(300,y+17),ref,22,TEXT,True); text(d,(555,y+19),kind,18,MUTED,True); text(d,(920,y+20),impact,18,MUTED)
    footer(d,3); return im

def slide_four():
    im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
    header(d,"Investigate", "The highest-risk shipment comes with evidence.", "Each investigation is bounded to five tool rounds and remains visible to the operator.")
    rounded(d,(100,355,1110,900),PANEL); rounded(d,(1140,355,1820,900),PANEL)
    text(d,(145,410),"OPS-40045-A | REEFER_TEMP",30,RED,True)
    text(d,(145,480),"Temperature-sensitive pharma",24,TEXT,True)
    text(d,(145,535),"Delivery window: Thursday 08:00-12:00",22,MUTED)
    text(d,(145,580),"Updated arrival: Thursday 15:40",22,MUTED)
    text(d,(145,655),"Window missed: yes",25,RED,True)
    text(d,(145,710),"Value at risk: $25,000",32,RED,True)
    text(d,(1185,410),"AGENT TRACE",20,MUTED,True)
    trace=["1  lookup shipment", "2  check port conditions", "3  calculate ETA impact", "4  confirm delivery window", "5  finalize assessment"]
    for i,item in enumerate(trace):
        y=485+i*67; rounded(d,(1180,y,1775,y+48),PANEL_2,10); text(d,(1205,y+13),item,19,TEXT if i<4 else GREEN, i==4)
    footer(d,4); return im

def slide_five():
    im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
    header(d,"Human control", "Automation prepares the work. People make the call.", "Low-confidence cases never become confident-looking customer messages.")
    rounded(d,(100,365,930,905),PANEL); rounded(d,(980,365,1820,905),PANEL)
    text(d,(145,420),"READY FOR APPROVAL",20,GREEN,True); text(d,(145,488),"Customer draft",31,TEXT,True)
    for i,line in enumerate(["Subject: Update on OPS-40045-A", "We are monitoring the Savannah delay...", "We will confirm the revised delivery plan... "]): text(d,(145,555+i*55),line,21,MUTED)
    rounded(d,(145,760,510,830),GREEN,14); text(d,(327,795),"APPROVE & SEND",20,BG,True,anchor="mm")
    text(d,(1025,420),"HUMAN REVIEW",20,AMBER,True); text(d,(1025,488),"No reference available",31,TEXT,True)
    text(d,(1025,555),"Customs hold message",21,MUTED); text(d,(1025,600),"Shipment identity cannot be confirmed.",21,MUTED)
    rounded(d,(1025,690,1755,785),PANEL_2,14); text(d,(1055,720),"Route: needs_human_review",22,AMBER,True)
    footer(d,5); return im

def slide_six():
    im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
    header(d,"Built for reliable operations", "OpsControl helps teams decide what matters now.", "A reproducible demo today. Real carrier channels next.")
    left=[("Codex", "Workflow, guardrails, replay harness, and regression tests"),("GPT-5.6", "Optional structured triage for live carrier text"),("Demo mode", "Deterministic, credential-free, and replayable")]
    for i,(a,b) in enumerate(left):
        y=390+i*135; rounded(d,(145,y,1775,y+100),PANEL); text(d,(180,y+25),a,27,AMBER,True); text(d,(440,y+31),b,23,TEXT)
    rounded(d,(340,835,1580,945),"#f59e0b",18); text(d,(960,890),"opscontrol.streamlit.app",37,BG,True,anchor="mm")
    footer(d,6); return im

for idx, fn in enumerate([slide_one,slide_two,slide_three,slide_four,slide_five,slide_six], start=1):
    fn().save(OUT / f"slide-{idx}.png")