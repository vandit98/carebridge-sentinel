from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from carebridge_sentinel.mcp_instance import mcp


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield


app = FastAPI(
    title="CareBridge Sentinel MCP",
    description="FHIR-aware transition-of-care and medication safety MCP server for Prompt Opinion.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "carebridge-sentinel-mcp"}


@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def landing_page() -> str:
    return """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>CareBridge Sentinel MCP</title>
        <style>
          :root {
            color-scheme: light;
            --ink: #17211d;
            --muted: #5d6b65;
            --line: #d7e0dc;
            --surface: #ffffff;
            --bg: #f5f8f6;
            --green: #007f73;
            --blue: #2f67b2;
          }
          * { box-sizing: border-box; }
          body {
            margin: 0;
            min-height: 100vh;
            color: var(--ink);
            background: linear-gradient(180deg, #eef6f3, var(--bg));
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          }
          main {
            width: min(1040px, calc(100% - 32px));
            margin: 0 auto;
            padding: 56px 0;
          }
          .hero {
            display: grid;
            grid-template-columns: minmax(0, 1.05fr) minmax(280px, 0.95fr);
            gap: 22px;
            align-items: stretch;
          }
          .panel {
            border: 1px solid var(--line);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.9);
            box-shadow: 0 22px 60px rgba(29, 44, 37, 0.12);
          }
          .intro { padding: 28px; }
          .eyebrow {
            color: var(--green);
            font-size: 12px;
            font-weight: 800;
            text-transform: uppercase;
          }
          h1 {
            margin: 8px 0 12px;
            font-size: clamp(34px, 5vw, 58px);
            line-height: 1;
          }
          p {
            margin: 0;
            color: var(--muted);
            font-size: 16px;
            line-height: 1.55;
          }
          .actions {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 22px;
          }
          a {
            display: inline-flex;
            align-items: center;
            min-height: 42px;
            padding: 10px 13px;
            border: 1px solid var(--line);
            border-radius: 8px;
            color: var(--ink);
            background: #fff;
            font-weight: 700;
            text-decoration: none;
          }
          a.primary {
            border-color: var(--green);
            color: #fff;
            background: var(--green);
          }
          .card-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 12px;
            padding: 18px;
          }
          .card {
            min-height: 128px;
            padding: 16px;
            border: 1px solid var(--line);
            border-radius: 8px;
            background: #fbfdfb;
          }
          .card b {
            display: block;
            margin-bottom: 8px;
            font-size: 15px;
          }
          .card span {
            color: var(--muted);
            font-size: 13px;
            line-height: 1.4;
          }
          .tools {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
            margin-top: 18px;
          }
          .tool {
            padding: 14px;
            border: 1px solid var(--line);
            border-radius: 8px;
            background: #fff;
          }
          .tool b {
            display: block;
            font-size: 13px;
          }
          .tool span {
            display: block;
            margin-top: 5px;
            color: var(--muted);
            font-size: 12px;
            line-height: 1.35;
          }
          code {
            padding: 2px 6px;
            border-radius: 6px;
            background: #e9f1ee;
          }
          @media (max-width: 780px) {
            main { padding: 28px 0; }
            .hero, .tools, .card-grid { grid-template-columns: 1fr; }
          }
        </style>
      </head>
      <body>
        <main>
          <section class="hero">
            <div class="panel intro">
              <div class="eyebrow">Live MCP server</div>
              <h1>CareBridge Sentinel</h1>
              <p>
                A FHIR-aware transition-of-care and medication safety MCP server for care managers,
                Prompt Opinion agents, and clinician-reviewed post-discharge workflows.
              </p>
              <div class="actions">
                <a class="primary" href="/mcp">MCP endpoint</a>
                <a href="/healthz">Health check</a>
                <a href="https://github.com/vandit98/carebridge-sentinel">GitHub</a>
              </div>
            </div>
            <div class="panel card-grid">
              <div class="card">
                <b>Transitions of care</b>
                <span>Generates cited handoff briefs, follow-up risks, and 72-hour rescue plans.</span>
              </div>
              <div class="card">
                <b>Medication safety</b>
                <span>Flags allergy conflicts, renal concerns, potassium risks, and high-risk combinations.</span>
              </div>
              <div class="card">
                <b>FHIR context</b>
                <span>Advertises <code>ai.promptopinion/fhir-context</code> scopes for patient-centered use.</span>
              </div>
              <div class="card">
                <b>Synthetic demo mode</b>
                <span>Render demo uses synthetic FHIR fixtures and does not store PHI or access tokens.</span>
              </div>
            </div>
          </section>
          <section class="tools">
            <div class="tool"><b>GenerateTransitionOfCareBrief</b><span>Clinician-ready transition risk summary.</span></div>
            <div class="tool"><b>FindLongitudinalCareGaps</b><span>Diabetes, hypertension, CKD, and prevention gaps.</span></div>
            <div class="tool"><b>BuildMedicationSafetyBrief</b><span>Medication, allergy, renal, and lab safety review.</span></div>
            <div class="tool"><b>PrioritizeTransitionPanel</b><span>Ranks post-acute patients for care-manager triage.</span></div>
          </section>
        </main>
      </body>
    </html>
    """


app.mount("/", mcp.streamable_http_app())
