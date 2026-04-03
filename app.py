"""
H5 Customer Portal - Simplified Version
Provides customer-facing H5 pages for company intro, recruitment, and agent flow monitoring
"""

import json
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, g
from flask_sock import Sock


# Create Flask app
app = Flask(__name__,
            template_folder='templates',
            static_folder='front',
            static_url_path='/front')
app.secret_key = "h5-secret-key-change-in-production"
sock = Sock(app)


# =============================================================================
# WebSocket Setup (For Real-time Monitoring)
# =============================================================================
connected_clients = []

@sock.route('/ws/monitor')
def ws_monitor(ws):
    """WebSocket endpoint for real-time frontend monitoring."""
    connected_clients.append(ws)
    try:
        while True:
            data = ws.receive()
            if data is None:
                break
            # Broadcast to all clients
            for client in connected_clients:
                if client != ws:
                    try:
                        client.send(data)
                    except:
                        pass
    except Exception as e:
        print(f"WebSocket Error: {e}")
    finally:
        if ws in connected_clients:
            connected_clients.remove(ws)


# =============================================================================
# Routes
# =============================================================================

@app.route("/")
def index():
    """Root redirect to H5 portal"""
    return redirect("/h5/")


@app.route("/h5/")
def h5_index():
    """H5 portal index page - show company intro"""
    return render_template("company.html")


@app.route("/h5/company")
def h5_company():
    """Company intro page (explicit route)"""
    return render_template("company.html")


@app.route("/recruit")
def h5_recruit():
    """Recruitment page for international interns"""
    return render_template("recruit.html")


@app.route("/h5/orders")
def h5_orders():
    """Customer order list - demo page"""
    return render_template("h5_orders.html")


@app.route("/h5/entry")
def h5_entry():
    """H5 entry page"""
    return render_template("h5_entry.html")


# =============================================================================
# API Endpoints
# =============================================================================

@app.route("/api/h5/orders")
def api_h5_orders():
    """API: Get customer orders (demo data)"""
    return jsonify({
        "success": True,
        "orders": [],
        "total": 0
    })


@app.route("/api/agent-flow/status")
def api_agent_flow_status():
    """API: Get agent flow status"""
    return jsonify({
        "success": True,
        "agents": [],
        "total": 0
    })


# =============================================================================
# Static Files & Agent Flow
# =============================================================================

@app.route("/agent-flow")
def agent_flow():
    """AI Agent Flow Monitor Page"""
    return render_template("agent_flow.html")


# =============================================================================
# Health Check
# =============================================================================

@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "h5_portal"})


# =============================================================================
# Main Entry
# =============================================================================

def run_h5_portal(host: str = "0.0.0.0", port: int = 8080, debug: bool = True):
    """Run H5 portal server"""
    print(f"\n🚀 H5 Portal Starting...")
    print(f"   Company: http://{host}:{port}/h5/")
    print(f"   Recruit: http://{host}:{port}/recruit")
    print(f"   Agent Flow: http://{host}:{port}/agent-flow")
    print(f"   Health: http://{host}:{port}/health\n")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_h5_portal()