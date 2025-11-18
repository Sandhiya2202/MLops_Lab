#!/usr/bin/env python
# coding: utf-8

# In[12]:


from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional
import requests

app = FastAPI()

MBTA_BASE_URL = "https://api-v3.mbta.com"
MBTA_API_KEY: Optional[str] = None  # Optional – leave None for low usage


class ChatRequest(BaseModel):
    message: str


def mbta_get(path: str, params=None):
    """Helper to call MBTA API."""
    headers = {}
    if MBTA_API_KEY:
        headers["x-api-key"] = MBTA_API_KEY

    resp = requests.get(
        f"{MBTA_BASE_URL}{path}",
        params=params or {},
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def format_time(iso_str: Optional[str]) -> str:
    """Convert ISO datetime string to '7:31 PM' style."""
    if not iso_str:
        return "Unknown time"
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%I:%M %p").lstrip("0")
    except Exception:
        return iso_str


def minutes_until(iso_str: Optional[str]) -> Optional[int]:
    """Return minutes from now until the given ISO time (rounded)."""
    if not iso_str:
        return None
    try:
        dt = datetime.fromisoformat(iso_str)  # includes timezone
        now = datetime.now(timezone.utc).astimezone(dt.tzinfo)
        diff = dt - now
        minutes = int(round(diff.total_seconds() / 60.0))
        return minutes
    except Exception:
        return None


def get_previous_stop_for_trip(trip_id: str) -> Optional[str]:
    """
    Try to infer the last known stop for a vehicle on a given trip.

    We:
    - Call /vehicles?filter[trip]=<trip_id>
    - Take the first vehicle
    - Read its stop relationship
    - Use /stops/{stop_id} to get the human-readable stop name

    This is a best-effort approximation; if anything fails, we return None.
    """
    try:
        data = mbta_get("/vehicles", params={"filter[trip]": trip_id, "page[limit]": 1})
        vehicles = data.get("data", [])
        if not vehicles:
            return None

        v = vehicles[0]
        stop_rel = v.get("relationships", {}).get("stop", {}).get("data")
        if not stop_rel:
            return None

        stop_id = stop_rel.get("id")
        if not stop_id:
            return None

        stop_info = mbta_get(f"/stops/{stop_id}")
        name = stop_info.get("data", {}).get("attributes", {}).get("name")
        return name
    except Exception:
        return None


def get_next_trains_northeastern() -> str:
    """Fetch live predictions for Northeastern University station (place-nuniv)."""
    stop_id = "place-nuniv"
    readable_name = "Northeastern University Station"

    data = mbta_get(
        "/predictions",
        params={
            "filter[stop]": stop_id,
            "sort": "departure_time",
            "page[limit]": 5,
            "include": "route",
        },
    )

    predictions = data.get("data", [])
    if not predictions:
        return f"I don’t see any upcoming Green Line trains at {readable_name} right now."

    # Build lookup for route names
    included = data.get("included", []) or []
    route_names = {}
    for item in included:
        if item.get("type") == "route":
            rid = item.get("id")
            attr = item.get("attributes", {})
            route_names[rid] = (
                attr.get("long_name")
                or attr.get("short_name")
                or rid
            )

    lines: list[str] = []
    for p in predictions[:3]:  # just first 3
        attr = p.get("attributes", {})
        dep = attr.get("departure_time") or attr.get("arrival_time")

        # ---- NEW LOGIC FOR STATUS ----
        raw_status = attr.get("status")
        if raw_status and raw_status != "No status":
            status_text = raw_status
        else:
            # try to say "Left <previous stop>"
            trip_id = (
                p.get("relationships", {})
                 .get("trip", {})
                 .get("data", {})
                 .get("id")
            )
            prev_stop = get_previous_stop_for_trip(trip_id) if trip_id else None
            if prev_stop:
                status_text = f"Left {prev_stop}"
            else:
                status_text = "No status"
        # -------------------------------

        # Route
        rel = p.get("relationships", {})
        route_id = None
        if "route" in rel and rel["route"].get("data"):
            route_id = rel["route"]["data"].get("id")
        route_name = route_names.get(route_id, route_id or "Unknown route")

        # Direction
        direction_id = attr.get("direction_id")
        if direction_id == 0:
            direction = "Outbound"
        elif direction_id == 1:
            direction = "Inbound"
        else:
            direction = "Unknown direction"

        t_str = format_time(dep)
        mins = minutes_until(dep)
        if mins is None:
            when = f"at {t_str}"
        elif mins <= 0:
            when = "arriving now"
        elif mins == 1:
            when = "in 1 minute"
        else:
            when = f"in {mins} minutes"

        lines.append(
            f"• {route_name} ({direction}) — {when} (scheduled at {t_str}, {status_text})"
        )

    header = f"You’re at {readable_name}.\nHere are the next trains:"
    return header + "\n" + "\n".join(lines)


def handle_chat_message(text: str) -> str:
    """Very simple chatbot logic."""
    t = text.lower()

    # If user mentions Northeastern / here / this station, assume place-nuniv
    is_northeastern = (
        "northeastern" in t
        or "neu" in t
        or "here" in t
        or "this station" in t
    )

    asks_train = any(
        word in t
        for word in ["train", "next", "when", "where", "coming", "arrive"]
    )

    if is_northeastern and asks_train:
        try:
            return get_next_trains_northeastern()
        except Exception as e:
            return (
                "I tried to look up the live trains for Northeastern, "
                f"but I hit an error: {e}"
            )

    # Small help response
    if "help" in t or "what can you do" in t:
        return (
            "You can ask things like:\n"
            "• Where is the train right now? I'm at Northeastern\n"
            "• When is the next train at Northeastern?\n\n"
            "Right now I’m focused on Northeastern University Station (Green Line E)."
        )

    # Default response
    return (
        "I’m a simple MBTA helper.\n\n"
        "Try asking:\n"
        "• Where is the train right now? I'm at Northeastern\n"
        "• When is the next train at Northeastern?\n"
        "I’ll use live MBTA data for Northeastern University Station."
    )


@app.get("/", response_class=HTMLResponse)
def index():
    """Serve a simple chat UI."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8" />
      <title>MBTA Northeastern Chatbot</title>
      <style>
        body {
          margin: 0;
          padding: 0;
          font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          background: #020617;
          color: #e5e7eb;
          display: flex;
          justify-content: center;
          align-items: center;
          min-height: 100vh;
        }
        .chat-wrapper {
          width: 420px;
          max-width: 100%;
          background: #0f172a;
          border-radius: 16px;
          box-shadow: 0 20px 40px rgba(15, 23, 42, 0.7);
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }
        .chat-header {
          padding: 14px 16px;
          border-bottom: 1px solid #1f2937;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .chat-title {
          font-size: 1rem;
          font-weight: 600;
        }
        .chat-subtitle {
          font-size: 0.8rem;
          color: #9ca3af;
        }
        .chat-body {
          padding: 12px 16px;
          height: 380px;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 8px;
          background: radial-gradient(circle at top left, #1d283a, #020617);
        }
        .msg {
          max-width: 85%;
          padding: 8px 10px;
          border-radius: 12px;
          font-size: 0.9rem;
          white-space: pre-line;
        }
        .msg-user {
          align-self: flex-end;
          background: #22c55e;
          color: #022c22;
          border-bottom-right-radius: 4px;
        }
        .msg-bot {
          align-self: flex-start;
          background: #111827;
          border-bottom-left-radius: 4px;
          border: 1px solid #1f2937;
        }
        .chat-footer {
          border-top: 1px solid #1f2937;
          padding: 10px;
          display: flex;
          gap: 8px;
          background: #020617;
        }
        .chat-input {
          flex: 1;
          border-radius: 999px;
          border: 1px solid #374151;
          padding: 8px 12px;
          font-size: 0.9rem;
          background: #020617;
          color: #e5e7eb;
          outline: none;
        }
        .chat-input::placeholder {
          color: #6b7280;
        }
        .chat-send {
          border-radius: 999px;
          border: none;
          padding: 8px 14px;
          font-size: 0.9rem;
          font-weight: 500;
          background: linear-gradient(135deg, #22c55e, #16a34a);
          color: white;
          cursor: pointer;
        }
        .chat-send:disabled {
          opacity: 0.6;
          cursor: default;
        }
      </style>
    </head>
    <body>
      <div class="chat-wrapper">
        <div class="chat-header">
          <div class="chat-title">MBTA Northeastern Chatbot</div>
          <div class="chat-subtitle">
            Ask: “Where is the train right now? I’m at Northeastern”
          </div>
        </div>
        <div id="chatBody" class="chat-body"></div>
        <div class="chat-footer">
          <input id="chatInput" class="chat-input" placeholder="Type a message..." />
          <button id="chatSend" class="chat-send">Send</button>
        </div>
      </div>

      <script>
        const chatBody = document.getElementById("chatBody");
        const chatInput = document.getElementById("chatInput");
        const chatSend = document.getElementById("chatSend");

        function addMessage(text, from) {
          const div = document.createElement("div");
          div.classList.add("msg");
          if (from === "user") {
            div.classList.add("msg-user");
          } else {
            div.classList.add("msg-bot");
          }
          div.textContent = text;
          chatBody.appendChild(div);
          chatBody.scrollTop = chatBody.scrollHeight;
        }

        async function sendMessage() {
          const text = chatInput.value.trim();
          if (!text) return;

          addMessage(text, "user");
          chatInput.value = "";
          chatInput.focus();
          chatSend.disabled = true;

          try {
            const res = await fetch("/chat", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ message: text })
            });
            if (!res.ok) {
              throw new Error("HTTP " + res.status);
            }
            const data = await res.json();
            addMessage(data.reply, "bot");
          } catch (err) {
            console.error(err);
            addMessage("Sorry, something went wrong while talking to the MBTA API.", "bot");
          } finally {
            chatSend.disabled = false;
          }
        }

        chatSend.addEventListener("click", sendMessage);
        chatInput.addEventListener("keydown", (e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            sendMessage();
          }
        });

        // Greeting
        addMessage(
          "Hi! I’m your MBTA helper for Northeastern University Station.\\n\\n" +
          "Try: “Where is the train right now? I’m at Northeastern” or\\n" +
          "“When is the next train at Northeastern?”",
          "bot"
        );
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/chat")
def chat(req: ChatRequest):
    """Chat endpoint: takes user text, returns bot reply."""
    reply = handle_chat_message(req.message)
    return JSONResponse({"reply": reply})


# In[ ]:





# In[ ]:




