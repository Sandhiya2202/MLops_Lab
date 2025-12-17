# Lab 5 – MBTA Real-Time Station Chatbot

## Overview

This lab implements a real-time MBTA station chatbot using:

- FastAPI (Python backend)
- HTML + JavaScript (simple chat UI)
- MBTA Public Real-Time API (V3)

The chatbot can answer questions like:

- "Where is the train right now at Northeastern University?"
- "When is the next train at South Station?"
- "Next train at Ruggles?"

It detects the station name from the user message, calls the live MBTA API, and returns human-friendly responses.

---

## What is the MBTA API?

The MBTA provides a public real-time API at:

https://api-v3.mbta.com

Main endpoints used in this lab:

- `/stops` – list of all MBTA stops (stations)
- `/predictions` – real-time arrival/departure predictions

Example prediction request:

- `GET /predictions?filter[stop]=place-nuniv` → next trains at Northeastern University (`stop_id = place-nuniv`)

All data comes from MBTA’s live operational systems (GPS, schedules, control center), so this chatbot works with **real-time train data**.

---

## What I Did in This Lab

1. **Chatbot backend with FastAPI**
   - Endpoint: `POST /chat`
   - Accepts a JSON body with a user message: `{"message": "..."}`
   - Returns a reply string based on live MBTA data.

2. **Station name detection**
   - On startup, the app calls `/stops` and builds a mapping:
     - "northeastern university" → "place-nuniv"
     - "south station" → "place-sstat"
     - "ruggles" → its stop id
   - It matches station names from the user text (e.g., "South Station", "Ruggles", "Back Bay").

3. **Live prediction lookup**
   - For the detected station, it calls:
     - `/predictions?filter[stop]=STOP_ID&sort=departure_time`
   - It extracts:
     - Route name (e.g., Green Line E, Orange Line)
     - Direction (Inbound / Outbound)
     - Departure/arrival time
     - Status (On time / No status / etc.)
   - It converts the timestamp into:
     - "in X minutes" or "arriving now"

4. **Chat-style frontend UI**
   - A simple HTML + JS chat window is served from `GET /`.
   - The frontend sends messages to `/chat` and displays replies like a chat conversation.

---

## How the Chatbot Works (Flow)

1. User types a message, e.g.:
   - "Where is the train right now at Northeastern University?"

2. Frontend sends this text to:
   - `POST /chat`

3. Backend:
   - Detects the station name in the text.
   - Maps it to the MBTA `stop_id`.
   - Calls `/predictions` for that stop.

4. The app:
   - Reads the next few predictions.
   - Calculates "in X minutes" from the current time.
   - Builds a reply like:

     Here are the next trains at Northeastern University:
     • Green Line E (Inbound) — in 3 minutes (scheduled at 7:31 PM, On time)
     • Green Line E (Inbound) — in 10 minutes (scheduled at 7:38 PM, No status)

5. The reply is sent back to the frontend and shown in the chat UI.

---

## How to Run the Project

From this folder:

```bash
cd ~/MLOps_Lab/MLOps/Lab5_MBTA_Chatbot

# Install dependencies
pip install fastapi uvicorn requests

# Run the app
uvicorn mbta_chatbot:app --reload --port 9000

