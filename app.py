"""
H5 Customer Portal
Provides customer-facing H5 pages for order history, session management, and resource confirmation
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from functools import wraps

from flask import Flask, request, jsonify, render_template, redirect, url_for, session, g

from framework.schemas.events import mask_id_card, mask_phone, generate_token
from framework.connectors import (
    OrderRepository, ItineraryRepository, ResourceRepository,
    TokenManager, cache
)
from framework.security import desensitizer, SessionValidator


# Create Flask app
app = Flask(__name__,
            template_folder='templates',
            static_folder='front',
            static_url_path='/front')
app.secret_key = "h5-secret-key-change-in-production"
from flask_sock import Sock
sock = Sock(app)


# =============================================================================
# WebSocket Setup (For Real-time Monitoring)
# =============================================================================
@sock.route('/ws/monitor')
def ws_monitor(ws):
    """
    WebSocket endpoint for real-time frontend monitoring.
    It registers itself to the global ConnectionManager in wecom gateway.
    """
    try:
        from apps.wecom_gateway.bot_sdk_app import ws_manager
        
        # Flask-Sock is synchronous, we wrap it with a pseudo-async interface 
        # so it's compatible with our manager
        class PseudoWebSocket:
            def __init__(self, raw_ws):
                self.ws = raw_ws
            
            async def accept(self):
                pass
                
            async def send_text(self, data: str):
                self.ws.send(data)

        p_ws = PseudoWebSocket(ws)
        # Hack to add to active connections
        if p_ws not in ws_manager.active_connections:
            ws_manager.active_connections.append(p_ws)
            
        while True:
            data = ws.receive()
            if data is None:
                break
    except Exception as e:
        print(f"WebSocket Error: {e}")
    finally:
        try:
            from apps.wecom_gateway.bot_sdk_app import ws_manager
            if p_ws in ws_manager.active_connections:
                ws_manager.active_connections.remove(p_ws)
        except:
            pass


# =============================================================================
# Request Helpers
# =============================================================================

def get_session_data():
    """Get current session data from URL token or cookie"""
    # Check for token in query string
    token = request.args.get("token") or request.form.get("token")
    if token:
        token_data = TokenManager.get_token(token)
        if token_data:
            return token_data

    # Check for customer_session_id
    customer_session_id = request.args.get("session_id") or request.cookies.get("customer_session_id")
    if customer_session_id:
        return {"customer_session_id": customer_session_id, "type": "session"}

    return {}


def require_session(f):
    """Decorator to require valid session"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_data = get_session_data()

        if not session_data:
            return jsonify({"error": "无效的会话", "code": "INVALID_SESSION"}), 401

        g.session_data = session_data
        return f(*args, **kwargs)

    return decorated_function


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
@require_session
def h5_orders():
    """Customer order list"""
    session_data = g.session_data
    customer_session_id = session_data.get("customer_session_id")

    # Get orders
    orders = OrderRepository.get_by_customer_session(customer_session_id, limit=50)

    # Enrich order data
    for order in orders:
        itinerary = ItineraryRepository.get_by_id(order["itinerary_id"])
        order["itinerary_name"] = itinerary["name"] if itinerary else "未知线路"
        order["itinerary_days"] = itinerary["days"] if itinerary else 0

        # Check if has trip plan
        if order["order_status"] >= 3:  # 待执行
            order["has_trip_plan"] = True
        else:
            order["has_trip_plan"] = False

    return render_template("h5_orders.html",
                           orders=orders,
                           customer_session_id=customer_session_id)


@app.route("/h5/order/<int:order_id>")
def h5_order_detail(order_id):
    """Order detail page"""
    session_data = get_session_data()

    # Validate session access
    customer_session_id = session_data.get("customer_session_id")
    if customer_session_id:
        order = OrderRepository.get_by_id(order_id)
        if order and order.get("customer_session_id") != customer_session_id:
            return jsonify({"error": "无权访问"}), 403

    if not order:
        return jsonify({"error": "订单不存在"}), 404

    # Get itinerary
    itinerary = ItineraryRepository.get_by_id(order["itinerary_id"])

    # Get passengers (desensitized)
    passenger_list = json.loads(order["passenger_list"]) if order.get("passenger_list") else []
    desensitized_passengers = []
    for p in passenger_list:
        desensitized_passengers.append({
            "name": desensitizer.desensitize_name(p.get("name", "")),
            "id_card": desensitizer.desensitize_id_card(p.get("id_card", "")),
            "phone": desensitizer.desensitize_phone(p.get("phone", "")),
            "remark": p.get("remark", ""),
            "role": p.get("role", "tourist")
        })

    # Get resources info
    hotel_info = None
    vehicle_info = None
    guide_info = None

    if order.get("hotel_session_id"):
        hotel_info = {"session_id": order["hotel_session_id"], "confirmed": True}
    if order.get("vehicle_session_id"):
        vehicle_info = {"session_id": order["vehicle_session_id"], "confirmed": True}
    if order.get("guide_session_id"):
        guide_info = {"session_id": order["guide_session_id"], "confirmed": True}

    return render_template("h5_order_detail.html",
                           order=order,
                           itinerary=itinerary,
                           passengers=desensitized_passengers,
                           hotel_info=hotel_info,
                           vehicle_info=vehicle_info,
                           guide_info=guide_info)


@app.route("/h5/passengers/<int:order_id>")
def h5_passenger_form(order_id):
    """Passenger information form"""
    session_data = get_session_data()

    # Validate
    order = OrderRepository.get_by_id(order_id)
    if not order:
        return jsonify({"error": "订单不存在"}), 404

    # Check order status
    if order["order_status"] > 2:  # 已超过待资源确认
        return jsonify({"error": "当前状态不可修改旅客信息"}), 400

    return render_template("h5_passengers.html",
                           order_id=order_id,
                           order=order)


@app.route("/h5/passengers/<int:order_id>/submit", methods=["POST"])
def h5_passenger_submit(order_id):
    """Submit passenger information"""
    data = request.get_json()

    passengers = data.get("passengers", [])
    if not passengers:
        return jsonify({"success": False, "message": "旅客信息不能为空"})

    # Validate each passenger
    for p in passengers:
        if not p.get("name"):
            return jsonify({"success": False, "message": "旅客姓名不能为空"})
        if not p.get("id_card"):
            return jsonify({"success": False, "message": "旅客身份证不能为空"})

    # Update order
    # In production, use repository
    # OrderRepository.update_passengers(order_id, passengers)

    return jsonify({
        "success": True,
        "message": f"已提交{len(passengers)}位旅客信息"
    })


@app.route("/h5/confirm/hotel/<int:order_id>")
def h5_confirm_hotel(order_id):
    """Hotel confirmation page"""
    token = request.args.get("token")
    if not token:
        return jsonify({"error": "无效的确认链接"}), 400

    # Validate token
    token_data = TokenManager.get_token(token)
    if not token_data or token_data.get("type") != "hotel_confirm":
        return jsonify({"error": "确认链接已失效"}), 400

    if token_data.get("order_id") != order_id:
        return jsonify({"error": "订单不匹配"}), 400

    # Get hotel info
    resource_id = token_data.get("resource_id")
    hotel = ResourceRepository.get_by_id(resource_id)

    return render_template("h5_confirm_hotel.html",
                           order_id=order_id,
                           hotel=hotel,
                           token=token,
                           data=token_data.get("data", {}))


@app.route("/h5/confirm/hotel/<int:order_id>/submit", methods=["POST"])
def h5_confirm_hotel_submit(order_id):
    """Submit hotel confirmation"""
    data = request.get_json()
    token = data.get("token")
    confirmed = data.get("confirmed", False)

    # Validate token
    token_data = TokenManager.get_token(token)
    if not token_data:
        return jsonify({"success": False, "message": "确认已失效"})

    if not confirmed:
        # Record as no room
        resource_id = token_data.get("resource_id")
        confirm_data = token_data.get("data", {})

        from framework.connectors import HotelBlackoutRepository
        for date in confirm_data.get("dates", []):
            HotelBlackoutRepository.add_blocked(
                resource_id=resource_id,
                date=date,
                room_type=data.get("room_type"),
                reason="酒店确认无房"
            )

        return jsonify({
            "success": True,
            "message": "已记录无房，将为您联系下一家酒店",
            "action": "next_hotel"
        })

    # Confirm hotel
    details = {
        "session_id": f"hotel_{token_data.get('resource_id')}",
        "room_type": data.get("room_type"),
        "room_quantity": data.get("room_quantity", 1),
        "check_in_names": data.get("check_in_names", []),
        "payment_method": data.get("payment_method"),
        "driver_room": data.get("driver_room", 0),
        "driver_name": data.get("driver_name", ""),
        "driver_phone": data.get("driver_phone", ""),
    }

    # Update order
    OrderRepository.update_session_ids(order_id, {
        "hotel_session_id": details["session_id"]
    })

    # Delete token
    TokenManager.delete_token(token)

    return jsonify({
        "success": True,
        "message": "酒店确认成功",
        "action": "confirmed"
    })


@app.route("/h5/confirm/vehicle/<int:order_id>")
def h5_confirm_vehicle(order_id):
    """Vehicle confirmation page"""
    token = request.args.get("token")
    if not token:
        return jsonify({"error": "无效的确认链接"}), 400

    token_data = TokenManager.get_token(token)
    if not token_data or token_data.get("type") != "vehicle_confirm":
        return jsonify({"error": "确认链接已失效"}), 400

    resource_id = token_data.get("resource_id")
    vehicle = ResourceRepository.get_by_id(resource_id)

    return render_template("h5_confirm_vehicle.html",
                           order_id=order_id,
                           vehicle=vehicle,
                           token=token,
                           data=token_data.get("data", {}))


@app.route("/h5/confirm/vehicle/<int:order_id>/submit", methods=["POST"])
def h5_confirm_vehicle_submit(order_id):
    """Submit vehicle confirmation"""
    data = request.get_json()
    token = data.get("token")
    confirmed = data.get("confirmed", False)

    if not confirmed:
        return jsonify({"success": True, "message": "已记录，将为您联系下一家车队"})

    details = {
        "session_id": f"vehicle_{data.get('resource_id')}",
        "driver_name": data.get("driver_name", ""),
        "driver_id_card": data.get("driver_id_card", ""),
        "driver_license": data.get("driver_license", ""),
        "vehicle_plate": data.get("vehicle_plate", ""),
        "driver_phone": data.get("driver_phone", ""),
    }

    OrderRepository.update_session_ids(order_id, {
        "vehicle_session_id": details["session_id"]
    })

    TokenManager.delete_token(token)

    return jsonify({
        "success": True,
        "message": "车辆确认成功",
        "action": "confirmed"
    })


@app.route("/h5/confirm/guide/<int:order_id>")
def h5_confirm_guide(order_id):
    """Guide confirmation page"""
    token = request.args.get("token")
    if not token:
        return jsonify({"error": "无效的确认链接"}), 400

    token_data = TokenManager.get_token(token)
    if not token_data or token_data.get("type") != "guide_confirm":
        return jsonify({"error": "确认链接已失效"}), 400

    resource_id = token_data.get("resource_id")
    guide = ResourceRepository.get_by_id(resource_id)

    return render_template("h5_confirm_guide.html",
                           order_id=order_id,
                           guide=guide,
                           token=token,
                           data=token_data.get("data", {}))


@app.route("/h5/confirm/guide/<int:order_id>/submit", methods=["POST"])
def h5_confirm_guide_submit(order_id):
    """Submit guide confirmation"""
    data = request.get_json()
    token = data.get("token")
    confirmed = data.get("confirmed", False)

    if not confirmed:
        return jsonify({"success": True, "message": "已记录，将为您联系下一位导游"})

    details = {
        "session_id": f"guide_{data.get('resource_id')}",
        "guide_name": data.get("guide_name", ""),
        "guide_id_card": data.get("guide_id_card", ""),
        "guide_license": data.get("guide_license", ""),
        "guide_phone": data.get("guide_phone", ""),
    }

    OrderRepository.update_session_ids(order_id, {
        "guide_session_id": details["session_id"]
    })

    TokenManager.delete_token(token)

    return jsonify({
        "success": True,
        "message": "导游确认成功",
        "action": "confirmed"
    })


@app.route("/h5/trip_plan/<int:order_id>")
def h5_trip_plan(order_id):
    """Trip plan download/preview"""
    session_data = get_session_data()
    customer_session_id = session_data.get("customer_session_id")

    order = OrderRepository.get_by_id(order_id)
    if not order:
        return jsonify({"error": "订单不存在"}), 404

    if customer_session_id and order.get("customer_session_id") != customer_session_id:
        return jsonify({"error": "无权访问"}), 403

    # Check if trip plan exists
    if order["order_status"] < 3:
        return jsonify({"error": "订单未完成资源确认"}), 400

    # Return trip plan data
    return render_template("h5_trip_plan.html", order=order)


# =============================================================================
# API Endpoints
# =============================================================================

@app.route("/api/h5/orders")
def api_h5_orders():
    """API: Get customer orders"""
    session_data = get_session_data()
    customer_session_id = session_data.get("customer_session_id")

    if not customer_session_id:
        return jsonify({"error": "无效会话"}), 401

    orders = OrderRepository.get_by_customer_session(customer_session_id)

    # Desensitize
    for order in orders:
        if order.get("owner_phone"):
            order["owner_phone"] = desensitizer.desensitize_phone(order["owner_phone"])
        if order.get("wholesaler_phone"):
            order["wholesaler_phone"] = desensitizer.desensitize_phone(order["wholesaler_phone"])

    return jsonify({
        "success": True,
        "orders": orders,
        "total": len(orders)
    })


@app.route("/api/h5/order/<int:order_id>")
def api_h5_order_detail(order_id):
    """API: Get order detail"""
    session_data = get_session_data()
    customer_session_id = session_data.get("customer_session_id")

    order = OrderRepository.get_by_id(order_id)
    if not order:
        return jsonify({"error": "订单不存在"}), 404

    if customer_session_id and order.get("customer_session_id") != customer_session_id:
        return jsonify({"error": "无权访问"}), 403

    # Desensitize
    if order.get("passenger_list"):
        passengers = json.loads(order["passenger_list"])
        order["passenger_list"] = [
            {
                "name": desensitizer.desensitize_name(p.get("name", "")),
                "id_card": desensitizer.desensitize_id_card(p.get("id_card", "")),
                "phone": desensitizer.desensitize_phone(p.get("phone", "")),
                "remark": p.get("remark", ""),
            }
            for p in passengers
        ]

    return jsonify({
        "success": True,
        "order": order
    })


# =============================================================================
# Static Files & Agent Flow
# =============================================================================

@app.route("/agent-flow")
def agent_flow():
    """AI Agent Flow Monitor Page"""
    return render_template("agent_flow.html")


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
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_h5_portal()