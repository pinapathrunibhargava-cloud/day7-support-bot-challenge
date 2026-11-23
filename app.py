"""Customer Support Bot (Day 7 Challenge: risk review).

A small Flask app. A customer sends a message, the LLM decides on a reply
and an action, and the app carries out the action.
"""
import json
import logging

from flask import Flask, jsonify, request

from llm import call_llm

app = Flask(__name__)

API_KEY = "sk-demo-4f9a2c71-FAKE-KEY-for-training-only"

logging.basicConfig(filename="logs/app.log", level=logging.INFO)

ORDERS = {
    "10231": {
        "status": "Shipped",
        "amount": 1299,
        "customer_email": "ravi.kumar@example.com"
    },
    "10232": {
        "status": "Delivered",
        "amount": 499,
        "customer_email": "priya.s@example.com"
    },
    "10233": {
        "status": "Processing",
        "amount": 2499,
        "customer_email": "priya.s@example.com"
    },
}
CUSTOMERS = {
    "ravi.kumar@example.com": {"name": "Ravi Kumar", "phone": "+91 98480 12345", "active": True},
    "priya.s@example.com": {"name": "Priya Sharma", "phone": "+91 99890 67890", "active": True},
}
# Demo authentication tokens (for challenge testing only)
DEMO_AUTH_TOKENS = {
    "demo-ravi-token": "ravi.kumar@example.com",
    "demo-priya-token": "priya.s@example.com",
}


def get_authenticated_customer():
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ", 1)[1]
    return DEMO_AUTH_TOKENS.get(token)
REFUNDS = []


# ---------- Tools the LLM can use ----------

def get_order_status(order_id):
    order = ORDERS.get(order_id)
    return order["status"] if order else "Order not found"


def issue_refund(order_id, amount):
    REFUNDS.append({"order_id": order_id, "amount": amount})
    return f"Refunded Rs {amount} for order {order_id}"


def delete_customer_account(customer_email):
    CUSTOMERS.pop(customer_email, None)
    return f"Deleted account {customer_email}"


TOOLS = {
    "get_order_status": get_order_status,
    "issue_refund": issue_refund,
    "delete_customer_account": delete_customer_account,
}


# ---------- Chat endpoint ----------


@app.post("/chat")
def chat():
    email = get_authenticated_customer()

    if not email:
        return jsonify({"error": "Unauthorized access"}), 401

    data = request.get_json(silent=True) or {}
    message = data.get("message", "")
    customer = CUSTOMERS.get(email, {})

    if not customer or not customer.get("active"):
        return jsonify({"error": "Customer account is inactive"}), 403

    prompt = (
        "You are a helpful support agent. Reply in JSON with reply, action and args.\n"
        f"Customer name: {customer.get('name')}\n"
        f"Customer email: {email}\n"
        f"Customer phone: {customer.get('phone')}\n"
        f"Customer message: {message}"
    )

    logging.info("AI request received")

    text, usage = call_llm(prompt, API_KEY)
    result = json.loads(text)

    action = result.get("action")
    action_result = None

    if action:
        args = result.get("args", {})

        if not isinstance(args, dict):
            return jsonify({"error": "Invalid action arguments"}), 400

        if action not in TOOLS:
            return jsonify({"error": "Invalid action"}), 400

        if action in ("get_order_status", "issue_refund"):
            order_id = str(args.get("order_id", ""))
            order = ORDERS.get(order_id)

            if not order or order["customer_email"] != email:
                return jsonify({"error": "Access denied for this order"}), 403

        if action == "issue_refund":
            amount = args.get("amount")
            order = ORDERS[order_id]

            if not isinstance(amount, int) or isinstance(amount, bool):
                return jsonify({"error": "Invalid refund amount"}), 400

            if amount <= 0 or amount > order["amount"]:
                return jsonify({"error": "Refund amount exceeds allowed limit"}), 400

        if action == "delete_customer_account":
            args = {"customer_email": email}

        action_result = TOOLS[action](**args)

    logging.info("AI response generated successfully")

    return jsonify({
        "reply": result.get("reply", ""),
        "action_result": action_result
    })



if __name__ == "__main__":
    app.run(debug=True)
