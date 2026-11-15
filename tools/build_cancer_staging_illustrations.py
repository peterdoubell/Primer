"""Render original, labelled SVG reporting schematics from cancer-staging.json.

These are orientation diagrams, not patient images or an automatic stage engine.
Clinical definitions, versions, limits and sources live in the JSON catalogue.
"""
import html
import json
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/radiology/cancer-staging.json'
OUT = ROOT / 'web/reference-media/reporting-diagrams/cancer'

def text(x, y, value, size=18, width=34, color='#243741'):
    lines = textwrap.wrap(value, width=width, break_long_words=False)
    return ''.join(f'<text x="{x}" y="{y+i*(size+6)}" font-size="{size}" fill="{color}">{html.escape(line)}</text>' for i, line in enumerate(lines))

def anatomy(kind):
    # Coordinates are illustrative. Stage depends on the table, not drawing scale.
    if kind == 'adrenal':
        return ('<path d="M118 213C159 192 236 191 274 215L226 137Z" fill="#deedf1" stroke="#648896" stroke-width="5"/>'
                '<path d="M186 254C119 237 100 323 142 378C181 409 237 365 223 334C181 343 159 291 219 282Z" fill="#deedf1" stroke="#648896" stroke-width="4"/>'
                '<circle cx="220" cy="195" r="27" fill="#b73947"/><path d="M238 204L298 250" stroke="#b73947" stroke-width="13"/>'
                + text(76,115,'Adrenal gland / extra-adrenal extent',16,39)
                + text(81,425,'Kidney below • vessels and organs nearby',16,42))
    if kind == 'lung':
        return ('<path d="M210 142V215M210 190L163 229M210 190L260 229" stroke="#648896" stroke-width="12" fill="none"/>'
                '<path d="M175 164C105 177 79 308 113 386L178 365Z M246 164C321 185 344 309 310 386L242 365Z" fill="#deedf1" stroke="#648896" stroke-width="4"/>'
                '<circle cx="148" cy="292" r="23" fill="#b73947"/><circle cx="195" cy="223" r="9" fill="#c98126"/><circle cx="226" cy="260" r="9" fill="#c98126"/>'
                + text(80,420,'Primary + pleural / mediastinal interfaces',16,38))
    if kind == 'wall':
        return ('<circle cx="210" cy="275" r="114" fill="#e3e9db" stroke="#648896" stroke-width="4"/><circle cx="210" cy="275" r="91" fill="#a1bcc8"/>'
                '<circle cx="210" cy="275" r="64" fill="#f0d3a7"/><circle cx="210" cy="275" r="38" fill="#fff"/>'
                '<path d="M248 275H345" stroke="#b73947" stroke-width="19"/><path d="M258 305L336 347" stroke="#b73947" stroke-width="10"/>'
                + text(70,143,'Lumen → submucosa → muscle → outside',16,42)
                + text(70,423,'Map depth and the outer organ interface',16,42))
    if kind == 'renal':
        return ('<path d="M207 151C102 145 88 260 112 343C145 418 235 370 242 322C182 325 172 245 239 220C247 189 235 164 207 151Z" fill="#deedf1" stroke="#648896" stroke-width="5"/>'
                '<path d="M231 262H329V162M329 262V377" stroke="#648896" stroke-width="20" fill="none"/>'
                '<path d="M168 280L237 264H327V228" stroke="#b73947" stroke-width="16" fill="none"/><circle cx="161" cy="279" r="28" fill="#b73947"/>'
                + text(77,136,'Organ boundary',16,25)+text(250,408,'Vein / IVC level',16,24)
                + text(70,450,'Report invasion and thrombus separately',16,41))
    if kind == 'uterus':
        return ('<path d="M210 170C127 115 89 230 153 286L172 333V391H249V333L268 286C331 231 295 116 210 170Z" fill="#deedf1" stroke="#648896" stroke-width="4"/>'
                '<path d="M210 187V271L193 335H229L210 271" fill="none" stroke="#fff" stroke-width="20"/>'
                '<circle cx="210" cy="283" r="29" fill="#b73947"/><path d="M236 283L302 307" stroke="#b73947" stroke-width="13"/>'
                + text(82,127,'Endometrium / myometrium',16,35)+text(95,421,'Cervix • parametria • vaginal extent',16,36))
    if kind == 'prostate':
        return ('<path d="M139 193C151 151 198 181 177 218M262 193C250 151 208 181 229 218" fill="none" stroke="#648896" stroke-width="20"/>'
                '<ellipse cx="207" cy="281" rx="105" ry="79" fill="#deedf1" stroke="#648896" stroke-width="5"/><path d="M207 209V355" stroke="#fff" stroke-width="16"/>'
                '<circle cx="271" cy="272" r="24" fill="#b73947"/><path d="M285 272L330 282" stroke="#b73947" stroke-width="14"/>'
                + text(70,133,'Seminal vesicles',16,30)+text(72,411,'Capsule → EPE; seminal vesicles separately',16,42))
    if kind == 'breast':
        return ('<path d="M323 168V390" stroke="#648896" stroke-width="16"/><path d="M295 173V385" stroke="#a1bcc8" stroke-width="16"/>'
                '<path d="M278 168C149 155 74 261 102 302C115 325 169 376 277 388" fill="#deedf1" stroke="#648896" stroke-width="4"/>'
                '<circle cx="197" cy="276" r="28" fill="#b73947"/><circle cx="269" cy="191" r="10" fill="#c98126"/>'
                + text(70,141,'Largest invasive focus',16,27)+text(76,423,'Skin • pectoralis • chest wall • nodes',16,41))
    if kind == 'liver':
        return ('<path d="M86 205C177 132 286 155 342 215L309 334L95 353Z" fill="#deedf1" stroke="#648896" stroke-width="5"/>'
                '<path d="M153 176L146 341M211 169L205 344M270 177L260 341" stroke="#648896" stroke-width="3"/>'
                '<circle cx="120" cy="272" r="20" fill="#b73947"/><circle cx="180" cy="244" r="19" fill="#b73947"/>'
                + text(65,136,'Map sections / burden and vascular spread',16,42)+text(79,423,'Record named segments and free sections',16,41))
    if kind == 'nodes':
        return ('<path d="M209 178V387M123 252H294M139 387L111 426M270 387L297 426" stroke="#deedf1" stroke-width="48" fill="none" stroke-linecap="round"/>'
                '<circle cx="209" cy="139" r="33" fill="#deedf1"/><path d="M83 315H335" stroke="#648896" stroke-width="3" stroke-dasharray="8 5"/>'
                '<circle cx="184" cy="220" r="10" fill="#c98126"/><circle cx="234" cy="220" r="10" fill="#c98126"/><circle cx="210" cy="281" r="10" fill="#c98126"/><circle cx="187" cy="365" r="10" fill="#c98126"/>'
                + text(90,470,'Level / side / diaphragm relationship',16,40))
    if kind == 'brain':
        return ('<path d="M207 168C145 125 72 195 113 253C78 307 135 382 209 355C275 389 337 322 302 262C346 198 279 136 207 168Z" fill="#deedf1" stroke="#648896" stroke-width="5"/>'
                '<path d="M207 166V355" stroke="#648896" stroke-width="3"/><ellipse cx="153" cy="246" rx="34" ry="26" fill="#b73947"/><ellipse cx="153" cy="246" rx="53" ry="41" fill="none" stroke="#c98126" stroke-width="3" stroke-dasharray="5 4"/>'
                + text(70,420,'Enhancing + nonenhancing extent',16,37))
    if kind == 'bone':
        return ('<path d="M156 171L158 363M247 171L246 363" stroke="#648896" stroke-width="13"/><path d="M163 185V348H242V185Z" fill="#deedf1"/>'
                '<ellipse cx="224" cy="269" rx="59" ry="43" fill="#b73947"/><path d="M247 258L303 228" stroke="#b73947" stroke-width="18"/>'
                + text(80,140,'Cortex / compartment',16,27)+text(70,426,'Length • soft tissue • skip lesions',16,38))
    if kind == 'ovarian':
        return ('<path d="M159 240H261M210 240V353" stroke="#648896" stroke-width="13"/><ellipse cx="118" cy="239" rx="38" ry="30" fill="#b73947"/><ellipse cx="301" cy="239" rx="38" ry="30" fill="#deedf1" stroke="#648896" stroke-width="4"/>'
                '<circle cx="102" cy="325" r="9" fill="#b73947"/><circle cx="293" cy="339" r="9" fill="#b73947"/><circle cx="246" cy="174" r="9" fill="#b73947"/>'
                + text(80,135,'Adnexal and peritoneal distribution',16,36)+text(78,426,'Capsular deposits ≠ organ metastasis',16,39))
    if kind == 'size':
        return ('<circle cx="116" cy="256" r="22" fill="#b73947"/><circle cx="213" cy="256" r="36" fill="#b73947"/><circle cx="323" cy="256" r="48" fill="#b73947"/>'
                +text(70,335,'T1 ≤2 cm | T2 >2–5 cm | T3 >5 cm',17,40)+text(70,421,'Actual adjacent organ invasion → T4',17,36))
    if kind == 'response':
        return ('<path d="M95 373V179M95 373H335" stroke="#648896" stroke-width="3" fill="none"/><path d="M114 205L211 299L308 236" stroke="#b73947" stroke-width="6" fill="none"/>'
                + text(70,144,'Example target sums (mm)',17,32)+text(80,405,'100 → 70: −30% from baseline (PR)',16,40)+text(80,439,'70 → 90: +28.6%, +20 mm from nadir',16,40))
    return ('<path d="M165 169V370M251 169V370" stroke="#648896" stroke-width="18"/><ellipse cx="167" cy="270" rx="53" ry="45" fill="#b73947"/><path d="M196 237L228 258L196 301" fill="none" stroke="#b73947" stroke-width="14"/>'
            +text(65,137,'Tumour–vessel interface',16,33)+text(75,422,'Contact angle • narrowing • encasement',16,41))

def main():
    data = json.loads(DATA.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    for key, system in data['systems'].items():
        title=html.escape(system['title'])
        body=text(28,40,system['title'],23,70)+text(28,75,system['version'],16,92)
        body+=anatomy(system['diagram_kind'])
        for i, step in enumerate(system['illustration_steps']):
            y=126+i*86
            body+=f'<rect x="446" y="{y}" width="464" height="65" rx="9" fill="#eef3f4" stroke="#648896"/>'
            body+=text(460,y+28,f'{i+1}. {step}',17,47)
            if i<3: body+=f'<path d="M675 {y+68}v15" stroke="#648896" stroke-width="3" marker-end="url(#arrow)"/>'
        body+=text(32,524,'Original orientation schematic • red = example tumour / extension; amber = nodes or additional extent',15,108)
        body+=text(32,552,'Use the category table and named system. Drawing scale, contact and appearance do not assign a stage.',15,110)
        raw=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 600" role="img" aria-label="{title}: reporting anatomy and staging pathway"><title>{title}</title><defs><marker id="arrow" markerWidth="5" markerHeight="5" refX="4" refY="2.5" orient="auto"><path d="M0 0L5 2.5L0 5" fill="#648896"/></marker></defs><rect width="960" height="600" fill="#fffaf3"/><g font-family="Arial,sans-serif">{body}</g></svg>'
        (OUT/(key+'.svg')).write_text(raw+'\n')
        system['illustration']={'title':system['title']+' — reporting anatomy and pathway','src':'/app/reference-media/reporting-diagrams/cancer/'+key+'.svg','alt':system['title']+'. '+'. '.join(system['illustration_steps']), 'caption':'Original simplified anatomical and reporting schematic. Read with the category table; this is not a clinical case image.'}
    DATA.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

if __name__ == '__main__':
    main()
